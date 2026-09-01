#!/usr/bin/env node
/**
 * Hermes Agent WhatsApp Bridge
 *
 * Standalone Node.js process that connects to WhatsApp via Baileys
 * and exposes HTTP endpoints for the Python gateway adapter.
 *
 * Endpoints (matches gateway/platforms/whatsapp.py expectations):
 *   GET  /messages       - Long-poll for new incoming messages
 *   POST /send           - Send a message { chatId, message, replyTo? }
 *   POST /edit           - Edit a sent message { chatId, messageId, message }
 *   POST /send-media     - Send media natively { chatId, filePath, mediaType?, caption?, fileName? }
 *   POST /typing         - Send typing indicator { chatId }
 *   GET  /chat/:id       - Get chat info
 *   GET  /health         - Health check
 *
 * Usage:
 *   node bridge.js --port 3000 --session ~/.hermes/whatsapp/session
 */

import { makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion, downloadMediaMessage } from '@whiskeysockets/baileys';
import express from 'express';
import { Boom } from '@hapi/boom';
import pino from 'pino';
import path from 'path';
import { mkdirSync, readFileSync, writeFileSync, existsSync, readdirSync, unlinkSync } from 'fs';
import { randomBytes, createHash } from 'crypto';
import { execSync } from 'child_process';
import { tmpdir } from 'os';
import qrcode from 'qrcode-terminal';
import Database from 'better-sqlite3';
import { matchesAllowedUser, parseAllowedUsers } from './allowlist.js';

// ─── Message Persistence (SQLite) ───────────────────────────────────────────
const MSG_DB_PATH = path.join(process.env.HOME || '~', '.hermes', 'whatsapp', 'messages.db');
let msgDb = null;
let stmtInsertMsg = null;
let stmtUpdateMsg = null;
let stmtUpsertGroup = null;

function initMessageDb() {
  try {
    mkdirSync(path.dirname(MSG_DB_PATH), { recursive: true });
    msgDb = new Database(MSG_DB_PATH);
    msgDb.pragma('journal_mode = WAL');
    msgDb.pragma('synchronous = NORMAL');

    msgDb.exec(`
      CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message_id TEXT UNIQUE,
        chat_id TEXT NOT NULL,
        chat_name TEXT,
        sender_id TEXT,
        sender_name TEXT,
        sender_phone TEXT,
        is_group INTEGER DEFAULT 0,
        from_me INTEGER DEFAULT 0,
        message_type TEXT DEFAULT 'text',
        body TEXT,
        media_type TEXT,
        media_path TEXT,
        mentioned_ids TEXT,
        quoted_message_id TEXT,
        timestamp INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
      CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
      CREATE INDEX IF NOT EXISTS idx_messages_chat_timestamp ON messages(chat_id, timestamp);
      CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
      CREATE INDEX IF NOT EXISTS idx_messages_sender_phone ON messages(sender_phone);
      CREATE TABLE IF NOT EXISTS group_metadata (
        chat_id TEXT PRIMARY KEY,
        chat_name TEXT,
        participant_count INTEGER,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
      );
    `);

    stmtInsertMsg = msgDb.prepare(`
      INSERT OR IGNORE INTO messages
        (message_id, chat_id, chat_name, sender_id, sender_name, sender_phone, is_group,
         from_me, message_type, body, media_type, media_path, mentioned_ids,
         quoted_message_id, timestamp)
      VALUES
        (@messageId, @chatId, @chatName, @senderId, @senderName, @senderPhone, @isGroup,
         @fromMe, @messageType, @body, @mediaType, @mediaPath, @mentionedIds,
         @quotedMessageId, @timestamp)
    `);

    // Update existing message (used by full-persist after media download / transcription)
    stmtUpdateMsg = msgDb.prepare(`
      UPDATE messages SET
        chat_name = @chatName,
        sender_name = @senderName,
        sender_phone = @senderPhone,
        body = @body,
        media_type = @mediaType,
        media_path = @mediaPath,
        mentioned_ids = @mentionedIds,
        quoted_message_id = @quotedMessageId
      WHERE message_id = @messageId
    `);

    stmtUpsertGroup = msgDb.prepare(`
      INSERT INTO group_metadata (chat_id, chat_name, participant_count, last_updated)
      VALUES (@chatId, @chatName, @participantCount, CURRENT_TIMESTAMP)
      ON CONFLICT(chat_id) DO UPDATE SET
        chat_name = @chatName,
        participant_count = @participantCount,
        last_updated = CURRENT_TIMESTAMP
    `);

    console.log(`[msg-db] Initialized: ${MSG_DB_PATH}`);
  } catch (err) {
    console.error(`[msg-db] Failed to init: ${err.message}`);
    msgDb = null;
  }
}

function persistMessage({ messageId, chatId, chatName, senderId, senderName, senderPhone, isGroup, fromMe, messageType, body, mediaType, mediaPath, mentionedIds, quotedMessageId, timestamp, update = false }) {
  if (!msgDb || !stmtInsertMsg) return;
  try {
    const params = {
      messageId: messageId || '',
      chatId: chatId || '',
      chatName: chatName || '',
      senderId: senderId || '',
      senderName: senderName || '',
      senderPhone: senderPhone || null,
      isGroup: isGroup ? 1 : 0,
      fromMe: fromMe ? 1 : 0,
      messageType: messageType || 'text',
      body: body || '',
      mediaType: mediaType || null,
      mediaPath: mediaPath || null,
      mentionedIds: mentionedIds || null,
      quotedMessageId: quotedMessageId || null,
      timestamp: timestamp || Math.floor(Date.now() / 1000),
    };
    if (update && stmtUpdateMsg) {
      // Full-persist: update existing row with media path, transcription, etc.
      stmtUpdateMsg.run(params);
    } else {
      // Early-persist: insert new row (INSERT OR IGNORE if already exists)
      stmtInsertMsg.run(params);
    }
    if (isGroup) console.log(`[msg-db] persisted group msg: ${chatId} | ${body?.substring(0, 50)}`);
    // Update contacts table
    upsertContact(senderId, senderName, senderPhone, isGroup, fromMe);
  } catch (err) {
    console.error('[msg-db] persistMessage error:', err.message);
  }
}

// Upsert contact from message sender info
function upsertContact(senderId, senderName, senderPhone, isGroup, fromMe) {
  if (!msgDb || fromMe) return;
  try {
    const lidPart = senderId?.replace(/@.*/, '') || '';
    const phonePart = senderPhone?.replace(/@.*/, '') || '';
    const displayName = senderName || phonePart || lidPart;
    
    // Use phone as primary key if available, otherwise LID
    const primaryKey = phonePart || lidPart;
    if (!primaryKey) return;
    
    msgDb.prepare(`
      INSERT INTO contacts (phone, name, lid, first_seen, last_seen, total_messages, groups_in)
      VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1, ?)
      ON CONFLICT(phone) DO UPDATE SET
        name = CASE WHEN excluded.name IS NOT NULL AND excluded.name != '' THEN excluded.name ELSE contacts.name END,
        lid = CASE WHEN excluded.lid IS NOT NULL AND excluded.lid != '' THEN excluded.lid ELSE contacts.lid END,
        last_seen = CURRENT_TIMESTAMP,
        total_messages = contacts.total_messages + 1,
        groups_in = CASE WHEN ? = 1 THEN contacts.groups_in + 1 ELSE contacts.groups_in END
    `).run(primaryKey, displayName, lidPart, isGroup ? 1 : 0, isGroup ? 1 : 0);
  } catch (err) {
    // silent - contact upsert is best-effort
  }
}

function persistGroupMetadata(chatId, chatName, participantCount) {
  if (!msgDb || !stmtUpsertGroup) return;
  try {
    stmtUpsertGroup.run({ chatId, chatName, participantCount });
    // Update the in-memory group name cache
    groupNameCache[chatId] = chatName;
  } catch (err) {
    // silent
  }
}

// In-memory group name cache: JID → human-readable name
const groupNameCache = {};
function loadGroupNameCache() {
  if (!msgDb) return;
  try {
    const rows = msgDb.prepare('SELECT chat_id, chat_name FROM group_metadata').all();
    for (const r of rows) {
      if (r.chat_name) groupNameCache[r.chat_id] = r.chat_name;
    }
    console.log(`[msg-db] Loaded ${Object.keys(groupNameCache).length} group names into cache`);
  } catch (err) {
    // silent
  }
}
function resolveGroupName(chatId) {
  return groupNameCache[chatId] || chatId.split('@')[0];
}

// Resolve sender LID to phone number using session mapping
function resolveSenderPhone(senderId) {
  if (!senderId) return null;
  // Already a phone number format
  if (senderId.includes('@s.whatsapp.net')) return senderId;
  // Try LID → phone map
  const lidPart = senderId.replace(/@.*/, '');
  const phone = lidToPhone[lidPart];
  if (phone) return `${phone}@s.whatsapp.net`;
  return null;
}
// ─── End Message Persistence ────────────────────────────────────────────────

// Parse CLI args
const args = process.argv.slice(2);
function getArg(name, defaultVal) {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : defaultVal;
}

const WHATSAPP_DEBUG =
  typeof process !== 'undefined' &&
  process.env &&
  typeof process.env.WHATSAPP_DEBUG === 'string' &&
  ['1', 'true', 'yes', 'on'].includes(process.env.WHATSAPP_DEBUG.toLowerCase());

const PORT = parseInt(getArg('port', '3000'), 10);
const SESSION_DIR = getArg('session', path.join(process.env.HOME || '~', '.hermes', 'whatsapp', 'session'));
const IMAGE_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'image_cache');
const DOCUMENT_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'document_cache');
const AUDIO_CACHE_DIR = path.join(process.env.HOME || '~', '.hermes', 'audio_cache');

/**
 * Transcribe audio file using faster-whisper (local, no API cost).
 * Returns the transcription text or null on failure.
 * Uses 'base' model for good Portuguese accuracy at reasonable speed.
 */
async function transcribeAudio(filePath) {
  const { execFile } = await import('child_process');
  const { promisify } = await import('util');
  const execFileAsync = promisify(execFile);
  try {
    // Run Python transcription script inline — avoids native module loading issues in Node
    const script = `
import sys, json
from faster_whisper import WhisperModel
model = WhisperModel('base', device='cpu', compute_type='int8')
segments, info = model.transcribe(sys.argv[1], language='pt')
text = ' '.join(s.text.strip() for s in segments)
print(json.dumps({"text": text, "language": info.language}, ensure_ascii=False))
`;
    const { stdout } = await execFileAsync('python3', ['-c', script, filePath], { timeout: 30000 });
    const result = JSON.parse(stdout.trim());
    return result.text || null;
  } catch (e) {
    console.error(`[whisper] Error: ${e.message}`);
    return null;
  }
}
const PAIR_ONLY = args.includes('--pair-only');
const WHATSAPP_MODE = getArg('mode', process.env.WHATSAPP_MODE || 'self-chat'); // "bot" or "self-chat"
const DM_MODE = getArg('dm-mode', process.env.WHATSAPP_DM_MODE || 'watchlist');
// DM_MODE: 'watchlist' (only persisted/watchlist DMs) | 'all' (log every DM) | 'contacts' (only saved contacts)
const ALLOWED_USERS = parseAllowedUsers(process.env.WHATSAPP_ALLOWED_USERS || '');
const DEFAULT_REPLY_PREFIX = '✨ *Mirna* — AI Agent\n────────────\n';
const REPLY_PREFIX = process.env.WHATSAPP_REPLY_PREFIX === undefined
  ? DEFAULT_REPLY_PREFIX
  : process.env.WHATSAPP_REPLY_PREFIX.replace(/\\n/g, '\n');
const MAX_MESSAGE_LENGTH = parseInt(process.env.WHATSAPP_MAX_MESSAGE_LENGTH || '4096', 10);
const CHUNK_DELAY_MS = parseInt(process.env.WHATSAPP_CHUNK_DELAY_MS || '300', 10);
// Per-call timeout for sock.sendMessage(). Baileys occasionally hangs forever
// when uploading media to WhatsApp servers (and, less often, on text sends),
// which pins the bridge's HTTP handler until the upstream aiohttp timeout
// fires. Fail fast instead so the gateway can surface a real error and retry.
const SEND_TIMEOUT_MS = parseInt(process.env.WHATSAPP_SEND_TIMEOUT_MS || '60000', 10);

// Initialize message persistence DB at startup
initMessageDb();
loadGroupNameCache();

// Compute script hash at startup for gateway verification
const SCRIPT_HASH = process.env.BRIDGE_SCRIPT_HASH || (() => {
  try {
    const content = readFileSync('/opt/data/scripts/whatsapp-bridge/bridge.js', 'utf-8');
    return createHash('sha256').update(content).digest('hex').slice(0, 16);
  } catch (e) {
    console.error('[scriptHash] Failed:', e.message);
    return 'unknown';
  }
})();

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function sendWithTimeout(chatId, payload, timeoutMs = SEND_TIMEOUT_MS) {
  let timer;
  const timeoutPromise = new Promise((_, reject) => {
    timer = setTimeout(
      () => reject(new Error(`sendMessage timed out after ${timeoutMs / 1000}s`)),
      timeoutMs,
    );
  });
  return Promise.race([sock.sendMessage(chatId, payload), timeoutPromise])
    .finally(() => clearTimeout(timer));
}

function formatOutgoingMessage(message) {
  // In bot mode, messages come from a different number so the prefix is
  // redundant — the sender identity is already clear.  Only prepend in
  // self-chat and normal modes where bot and user share the same number.
  if (WHATSAPP_MODE === 'bot') return message;
  return REPLY_PREFIX ? `${REPLY_PREFIX}${message}` : message;
}

function splitLongMessage(message, maxLength = MAX_MESSAGE_LENGTH) {
  const text = String(message || '');
  if (!text) return [];
  if (!Number.isFinite(maxLength) || maxLength < 1 || text.length <= maxLength) {
    return [text];
  }

  const chunks = [];
  let remaining = text;
  while (remaining.length > maxLength) {
    let splitAt = remaining.lastIndexOf('\n', maxLength);
    if (splitAt < Math.floor(maxLength / 2)) {
      splitAt = remaining.lastIndexOf(' ', maxLength);
    }
    if (splitAt < 1) splitAt = maxLength;

    chunks.push(remaining.slice(0, splitAt).trimEnd());
    remaining = remaining.slice(splitAt).trimStart();
  }
  if (remaining) chunks.push(remaining);
  return chunks;
}

function trackSentMessageId(sent) {
  if (sent?.key?.id) {
    recentlySentIds.add(sent.key.id);
    if (recentlySentIds.size > MAX_RECENT_IDS) {
      recentlySentIds.delete(recentlySentIds.values().next().value);
    }
  }
}

function normalizeWhatsAppId(value) {
  if (!value) return '';
  return String(value).replace(':', '@');
}

function getMessageContent(msg) {
  const content = msg?.message || {};
  if (content.ephemeralMessage?.message) return content.ephemeralMessage.message;
  if (content.viewOnceMessage?.message) return content.viewOnceMessage.message;
  if (content.viewOnceMessageV2?.message) return content.viewOnceMessageV2.message;
  if (content.documentWithCaptionMessage?.message) return content.documentWithCaptionMessage.message;
  if (content.templateMessage?.hydratedTemplate) return content.templateMessage.hydratedTemplate;
  if (content.buttonsMessage) return content.buttonsMessage;
  if (content.listMessage) return content.listMessage;
  return content;
}

function getContextInfo(messageContent) {
  if (!messageContent || typeof messageContent !== 'object') return {};
  for (const value of Object.values(messageContent)) {
    if (value && typeof value === 'object' && value.contextInfo) {
      return value.contextInfo;
    }
  }
  return {};
}

mkdirSync(SESSION_DIR, { recursive: true });

// Build LID → phone reverse map from session files (lid-mapping-{phone}.json)
function buildLidMap() {
  const map = {};
  try {
    const files = readdirSync(SESSION_DIR);
    for (const f of files) {
      const m = f.match(/^lid-mapping-(\d+)\.json$/);
      if (!m) continue;
      const phone = m[1];
      const lid = String(JSON.parse(readFileSync(path.join(SESSION_DIR, f), 'utf8'))).trim();
      if (lid) {
        map[lid + '@lid'] = phone;  // with @lid suffix (matches group participant IDs)
        map[lid] = phone;            // without @lid (fallback)
      }
    }
    console.log(`LID map built: ${Object.keys(map).length} entries from ${files.length} session files`);
  } catch(e) {
    console.warn(`LID map build error: ${e.message}`);
  }
  return map;
}
let lidToPhone = buildLidMap();

const logger = pino({ level: 'warn' });

// Message queue for polling
const messageQueue = [];
const MAX_QUEUE_SIZE = 100;

// Track recently sent message IDs to prevent echo-back loops with media
const recentlySentIds = new Set();
const MAX_RECENT_IDS = 50;

let sock = null;
let connectionState = 'disconnected';
let currentQR = null; // latest QR string for /qr-image endpoint
// In-memory contact map — populated by contacts.upsert and contacts.update events
const contactMap = new Map();

async function startSocket() {
  const { state, saveCreds } = await useMultiFileAuthState(SESSION_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false,
    browser: ['Mirna', 'Chrome', '120.0'],
    syncFullHistory: false,
    markOnlineOnConnect: false,
    // Required for Baileys 7.x: without this, incoming messages that need
    // E2EE session re-establishment are silently dropped (msg.message === null)
    getMessage: async (key) => {
      // We don't maintain a message store, so return a placeholder.
      // This is enough for Baileys to complete the retry handshake.
      return { conversation: '' };
    },
  });

  // No store in Baileys 7 — track contacts manually from events

  sock.ev.on('creds.update', () => { saveCreds(); lidToPhone = buildLidMap(); });

  // ─── Sync WhatsApp contacts with DB ─────────────────────────────
  sock.ev.on('contacts.upsert', (contacts) => {
    if (!msgDb) return;
    logger.info(`contacts.upsert: received ${contacts.length} contacts`);
    const named = contacts.filter(c => c.name && c.name !== '.').length;
    logger.info(`contacts.upsert: ${named} with names`);
    for (const c of contacts) {
      const id = c.id || '';
      const name = c.name || '';
      const lid = c.lid || '';
      const phone = id.replace(/@.*/, '');
      if (!phone || phone.length < 8) continue;
      // Populate in-memory contact map
      contactMap.set(id, { id, name, lid, phone });
      try {
        msgDb.prepare(`
          INSERT INTO contacts (phone, name, lid, last_seen)
          VALUES (?, ?, ?, CURRENT_TIMESTAMP)
          ON CONFLICT(phone) DO UPDATE SET
            name = CASE WHEN ? != '' THEN ? ELSE contacts.name END,
            lid = CASE WHEN ? != '' THEN ? ELSE contacts.lid END,
            last_seen = CURRENT_TIMESTAMP
        `).run(phone, name, lid, name, name, lid, lid);
        // Also update group_members if we have phone
        if (lid) {
          msgDb.prepare(`
            UPDATE group_members SET member_phone = ? WHERE member_lid = ? AND (member_phone = '' OR member_phone IS NULL)
          `).run(phone, lid);
        }
      } catch(e) {}
    }
  });

  // Track contacts.update for name changes — persist pushName (notify) to DB
  sock.ev.on('contacts.update', (updates) => {
    if (!msgDb) return;
    for (const u of updates) {
      const existing = contactMap.get(u.id) || {};
      contactMap.set(u.id, { ...existing, ...u });
      // Persist pushName from 'notify' field
      const notify = u.notify || '';
      const verifiedName = u.verifiedName || '';
      const name = verifiedName || notify;
      if (!name || name === '.') continue;
      const phone = (u.id || '').replace(/@.*/, '');
      if (phone.length < 8) continue;
      try {
        msgDb.prepare(`
          INSERT INTO contacts (phone, name, lid, last_seen)
          VALUES (?, ?, ?, CURRENT_TIMESTAMP)
          ON CONFLICT(phone) DO UPDATE SET
            name = CASE WHEN ? != '' AND (contacts.name = '' OR contacts.name IS NULL OR contacts.name = '.') THEN ? ELSE contacts.name END,
            lid = CASE WHEN ? != '' THEN ? ELSE contacts.lid END,
            last_seen = CURRENT_TIMESTAMP
        `).run(phone, name, '', name, name, '', '');
        // Also update group_members by phone
        msgDb.prepare(`
          UPDATE group_members SET member_phone = ? WHERE member_phone = ? AND member_lid = ''
        `).run(phone, '');
        if (u.id && u.id.includes('@lid')) {
          msgDb.prepare(`UPDATE group_members SET member_phone = ? WHERE member_lid = ? AND (member_phone = '' OR member_phone IS NULL)`).run(phone, u.id);
        }
      } catch(e) { logger.error({ err: e }, 'contacts.update DB error'); }
    }
  });

  // chats.upsert fires with all chats (DMs + groups) including names from the phone's address book
  sock.ev.on('chats.upsert', (chats) => {
    for (const chat of chats) {
      const id = chat.id || '';
      if (id.includes('@g.us')) continue; // skip groups
      const phone = id.replace(/@.*/, '');
      const name = chat.name || '';
      if (phone.length >= 8 && name && name !== '.') {
        contactMap.set(id, { id, name, phone });
        // Also persist to DB
        try {
          msgDb.prepare(`
            INSERT INTO contacts (phone, name, last_seen)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(phone) DO UPDATE SET
              name = CASE WHEN ? != '' THEN ? ELSE contacts.name END,
              last_seen = CURRENT_TIMESTAMP
          `).run(phone, name, name, name);
        } catch(e) {}
      }
    }
  });

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr; // store for /qr-image endpoint
      console.log('\n📱 Scan this QR code with WhatsApp on your phone:\n');
      qrcode.generate(qr, { small: true });
      console.log('\nWaiting for scan...\n');
    }

    if (connection === 'close') {
      const reason = new Boom(lastDisconnect?.error)?.output?.statusCode;
      connectionState = 'disconnected';

      if (reason === DisconnectReason.loggedOut) {
        console.log('❌ Logged out. Delete session and restart to re-authenticate.');
        process.exit(1);
      } else {
        // 515 = restart requested (common after pairing). Always reconnect.
        if (reason === 515) {
          console.log('↻ WhatsApp requested restart (code 515). Reconnecting...');
        } else {
          console.log(`⚠️  Connection closed (reason: ${reason}). Reconnecting in 3s...`);
        }
        setTimeout(startSocket, reason === 515 ? 1000 : 3000);
      }
    } else if (connection === 'open') {
      connectionState = 'connected';
      console.log('✅ WhatsApp connected!');
      loadLidMappings();
      loadWatchlist(); // Restore DM watchlist from disk (must be AFTER loadLidMappings for LID resolution)
      if (PAIR_ONLY) {
        console.log('✅ Pairing complete. Credentials saved.');
        // Give Baileys a moment to flush creds, then exit cleanly
        setTimeout(() => process.exit(0), 2000);
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    // In self-chat mode, your own messages commonly arrive as 'append' rather
    // than 'notify'. Accept both and filter agent echo-backs below.
    if (type !== 'notify' && type !== 'append') return;

    const botIds = Array.from(new Set([
      normalizeWhatsAppId(sock.user?.id),
      normalizeWhatsAppId(sock.user?.lid),
    ].filter(Boolean)));

    for (const msg of messages) {
      if (!msg.message) continue;

      const chatId = msg.key.remoteJid;
      if (WHATSAPP_DEBUG) {
        try {
          console.log(JSON.stringify({
            event: 'upsert', type,
            fromMe: !!msg.key.fromMe, chatId,
            senderId: msg.key.participant || chatId,
            messageKeys: Object.keys(msg.message || {}),
          }));
        } catch {}
      }
      const senderId = msg.key.participant || chatId;
      const isGroup = chatId.endsWith('@g.us');
      const senderNumber = senderId.replace(/@.*/, '');
      // ─── Early persist: capture ALL group messages + watched DMs ────
      // This ensures we log messages even from groups not in the allowlist,
      // and DM conversations Mirna initiated (auto-watchlist).
      const watchedDM = checkWatchedDM(chatId, isGroup);
      const persistForAllDM = DM_MODE === 'all' && !isGroup;
      const persistForContactDM = DM_MODE === 'contacts' && !isGroup && checkContactDM(senderNumber);
      const shouldPersist = isGroup || watchedDM || persistForAllDM || persistForContactDM;
      if (shouldPersist) {
        const mc = getMessageContent(msg);
        let earlyBody = mc?.conversation || mc?.extendedTextMessage?.text ||
                         mc?.imageMessage?.caption || mc?.videoMessage?.caption ||
                         mc?.documentMessage?.caption || mc?.pttMessage?.caption || '';
        const earlyMediaType = mc?.imageMessage ? 'image' : mc?.videoMessage ? 'video' :
                               mc?.audioMessage || mc?.pttMessage ? 'ptt' :
                               mc?.documentMessage ? 'document' : '';
        if (!earlyBody && earlyMediaType) earlyBody = `[${earlyMediaType} received]`;
        // Only persist if we have something meaningful (skip reactions, presence, etc.)
        if (earlyBody || earlyMediaType) {
          persistMessage({
            messageId: msg.key.id,
            chatId: isGroup ? chatId : resolveDmChatId(chatId),
            chatName: isGroup ? resolveGroupName(chatId) : (msg.pushName || senderNumber),
            senderId,
            senderName: msg.pushName || senderNumber,
            senderPhone: resolveSenderPhone(senderId),
            isGroup,
            fromMe: !!msg.key.fromMe,
            messageType: earlyMediaType || 'text',
            body: earlyBody,
            mediaType: earlyMediaType || null,
            mediaPath: null,
            mentionedIds: null,
            quotedMessageId: null,
            timestamp: msg.messageTimestamp,
          });
          if (watchedDM) {
            console.log(`[dm-watch] Persisted DM reply: ${chatId} (resolved: ${resolveDmChatId(chatId)}) | ${earlyBody?.substring(0, 50)}`);
            // Update watchlist status: contact replied
            if (!msg.key.fromMe) {
              updateWatchEntry(chatId, { status: 'replied', lastReplyAt: msg.messageTimestamp });
            } else {
              // Caju replied — track it
              updateWatchEntry(chatId, { lastMeAt: msg.messageTimestamp });
            }
            // Write notification file for Hermes to pick up
            const resolvedChatId = resolveDmChatId(chatId);
            const watchEntry = getWatchEntry(chatId);
            const notif = {
              type: 'dm_reply',
              chatId: resolvedChatId,
              chatName: msg.pushName || senderNumber,
              senderName: msg.pushName || senderNumber,
              body: earlyBody?.substring(0, 200),
              timestamp: msg.messageTimestamp,
              notifiedAt: Date.now(),
              watchStatus: watchEntry?.status || 'watching',
              cajuAlreadyResponded: watchEntry ? (watchEntry.lastMeAt || 0) > (watchEntry.lastReplyAt || 0) : false,
            };
            try {
              const notifDir = '/home/hermes/.hermes/whatsapp/notifications';
              if (!existsSync(notifDir)) mkdirSync(notifDir, { recursive: true });
              writeFileSync(path.join(notifDir, `dm_${Date.now()}.json`), JSON.stringify(notif));
            } catch (e) { /* non-critical */ }
          }
        }
      }
      // ─── End early persist ────────────────────────────────────────────────

      // Handle fromMe messages based on mode
      if (msg.key.fromMe) {
        if (chatId.includes('status')) continue;

        // Normal mode (personal number + groups): allow fromMe in groups so the
        // user's own messages can trigger the agent.  The echo-back guard below
        // (REPLY_PREFIX / recentlySentIds) prevents infinite loops.
        if (WHATSAPP_MODE !== 'normal' && isGroup) continue;

        if (WHATSAPP_MODE === 'bot') {
          // Bot mode: separate number. ALL fromMe are echo-backs of our own replies — skip.
          continue;
        }

        // Normal mode + fromMe + group: pass through to the agent.
        if (WHATSAPP_MODE === 'normal' && isGroup) {
          // fall through to message processing
        } else {
          // Self-chat mode: only allow messages in the user's own self-chat
          // WhatsApp now uses LID (Linked Identity Device) format: 67427329167522@lid
          // AND classic format: 34652029134@s.whatsapp.net
          // sock.user has both: { id: "number:10@s.whatsapp.net", lid: "lid_number:10@lid" }
          const myNumber = (sock.user?.id || '').replace(/:.*@/, '@').replace(/@.*/, '');
          const myLid = (sock.user?.lid || '').replace(/:.*@/, '@').replace(/@.*/, '');
          const chatNumber = chatId.replace(/@.*/, '');
          const isSelfChat = (myNumber && chatNumber === myNumber) || (myLid && chatNumber === myLid);
          if (!isSelfChat) continue;
        }
      }

      // Handle !fromMe messages (from other people) based on mode.
      // Self-chat mode only responds to the user's own messages to
      // themselves — stranger DMs / group pings must never reach the
      // Python gateway, otherwise a pairing-code reply fires in response
      // to arbitrary incoming messages (#8389).
      if (!msg.key.fromMe) {
        if (WHATSAPP_MODE === 'self-chat') {
          try {
            console.log(JSON.stringify({
              event: 'ignored',
              reason: 'self_chat_mode_rejects_non_self',
              chatId,
              senderId,
            }));
          } catch {}
          continue;
        }
        if (!matchesAllowedUser(senderId, ALLOWED_USERS, SESSION_DIR)) {
          // In normal mode, allow group messages from anyone — the Python
          // gateway's group_policy/group_allow_from handles access control.
          if (WHATSAPP_MODE === 'normal' && isGroup) {
            // pass through
          } else if (WHATSAPP_MODE === 'normal' && !isGroup && checkWatchedDM(chatId, isGroup)) {
            // Escape hatch: DM replies from watched conversations pass through
            // even if not in ALLOWED_USERS — Mirna initiated the conversation,
            // so the reply must reach the gateway for analysis and suggestion.
            console.log(`[dm-watch] Allowlist bypass for watched DM: ${chatId}`);
          } else {
            try {
              console.log(JSON.stringify({
                event: 'ignored',
                reason: 'allowlist_mismatch',
                chatId,
                senderId,
              }));
            } catch {}
            continue;
          }
        }
      }

      const messageContent = getMessageContent(msg);
      const contextInfo = getContextInfo(messageContent);
      const mentionedIds = Array.from(new Set((contextInfo?.mentionedJid || []).map(normalizeWhatsAppId).filter(Boolean)));
      const quotedMessageId = contextInfo?.stanzaId || null;
      const quotedParticipant = normalizeWhatsAppId(contextInfo?.participant || '') || null;
      const quotedRemoteJid = normalizeWhatsAppId(contextInfo?.remoteJid || '') || null;
      const hasQuotedMessage = !!contextInfo?.quotedMessage;

      // Extract message body
      let body = '';
      let hasMedia = false;
      let mediaType = '';
      const mediaUrls = [];

      if (messageContent.conversation) {
        body = messageContent.conversation;
      } else if (messageContent.extendedTextMessage?.text) {
        body = messageContent.extendedTextMessage.text;
      } else if (messageContent.imageMessage) {
        body = messageContent.imageMessage.caption || '';
        hasMedia = true;
        mediaType = 'image';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.imageMessage.mimetype || 'image/jpeg';
          const extMap = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp', 'image/gif': '.gif' };
          const ext = extMap[mime] || '.jpg';
          mkdirSync(IMAGE_CACHE_DIR, { recursive: true });
          const filePath = path.join(IMAGE_CACHE_DIR, `img_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download image:', err.message);
        }
      } else if (messageContent.videoMessage) {
        body = messageContent.videoMessage.caption || '';
        hasMedia = true;
        mediaType = 'video';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = messageContent.videoMessage.mimetype || 'video/mp4';
          const ext = mime.includes('mp4') ? '.mp4' : '.mkv';
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const filePath = path.join(DOCUMENT_CACHE_DIR, `vid_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download video:', err.message);
        }
      } else if (messageContent.audioMessage || messageContent.pttMessage) {
        hasMedia = true;
        mediaType = messageContent.pttMessage ? 'ptt' : 'audio';
        try {
          const audioMsg = messageContent.pttMessage || messageContent.audioMessage;
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          const mime = audioMsg.mimetype || 'audio/ogg';
          const ext = mime.includes('ogg') ? '.ogg' : mime.includes('mp4') ? '.m4a' : '.ogg';
          mkdirSync(AUDIO_CACHE_DIR, { recursive: true });
          const filePath = path.join(AUDIO_CACHE_DIR, `aud_${randomBytes(6).toString('hex')}${ext}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
          // Transcribe PTT/audio messages via faster-whisper (local, no API cost)
          try {
            const transcript = await transcribeAudio(filePath);
            if (transcript) {
              body = `🎤 ${transcript}`;
              console.log(`[whisper] Transcribed ${mediaType}: ${transcript.substring(0, 80)}`);
            }
          } catch (whisperErr) {
            console.error(`[whisper] Transcription failed: ${whisperErr.message}`);
          }
        } catch (err) {
          console.error('[bridge] Failed to download audio:', err.message);
        }
      } else if (messageContent.documentMessage) {
        body = messageContent.documentMessage.caption || '';
        hasMedia = true;
        mediaType = 'document';
        const fileName = messageContent.documentMessage.fileName || 'document';
        try {
          const buf = await downloadMediaMessage(msg, 'buffer', {}, { logger, reuploadRequest: sock.updateMediaMessage });
          mkdirSync(DOCUMENT_CACHE_DIR, { recursive: true });
          const safeFileName = path.basename(fileName).replace(/[^a-zA-Z0-9._-]/g, '_');
          const filePath = path.join(DOCUMENT_CACHE_DIR, `doc_${randomBytes(6).toString('hex')}_${safeFileName}`);
          writeFileSync(filePath, buf);
          mediaUrls.push(filePath);
        } catch (err) {
          console.error('[bridge] Failed to download document:', err.message);
        }
      }

      // For media without caption, use a placeholder so the API message is never empty
      if (hasMedia && !body) {
        body = `[${mediaType} received]`;
      }

      // ─── Persist ALL messages to SQLite (before any filtering) ──────────
      // Skip empty messages (reactions, presence, etc.) — no useful content
      // This is the FULL persist — runs after media download and audio transcription.
      // Uses update=true to overwrite the early-persist row with complete data.
      if (body || hasMedia) {
        persistMessage({
          messageId: msg.key.id,
          chatId,
          chatName: isGroup ? resolveGroupName(chatId) : (msg.pushName || senderNumber),
          senderId,
          senderName: msg.pushName || senderNumber,
          senderPhone: resolveSenderPhone(senderId),
          isGroup,
          fromMe: !!msg.key.fromMe,
          messageType: hasMedia ? mediaType : 'text',
          body: body || '',
          mediaType: hasMedia ? mediaType : null,
          mediaPath: mediaUrls.length > 0 ? mediaUrls.join(',') : null,
          mentionedIds: mentionedIds.join(',') || null,
          quotedMessageId,
          timestamp: msg.messageTimestamp,
          update: true,
        });
      }
      // ─── End persist ────────────────────────────────────────────────────

      // Ignore Hermes' own reply messages in self-chat mode to avoid loops.
      if (msg.key.fromMe && ((REPLY_PREFIX && body.startsWith(REPLY_PREFIX)) || recentlySentIds.has(msg.key.id))) {
        if (WHATSAPP_DEBUG) {
          try { console.log(JSON.stringify({ event: 'ignored', reason: 'agent_echo', chatId, messageId: msg.key.id })); } catch {}
        }
        continue;
      }

      // Skip empty messages
      if (!body && !hasMedia) {
        if (WHATSAPP_DEBUG) {
          try { 
            console.log(JSON.stringify({ event: 'ignored', reason: 'empty', chatId, messageKeys: Object.keys(msg.message || {}) })); 
          } catch (err) {
            console.error('Failed to log empty message event:', err);
          }
        }
        continue;
      }

      const event = {
        messageId: msg.key.id,
        chatId,
        senderId,
        senderName: msg.pushName || senderNumber,
        chatName: isGroup ? resolveGroupName(chatId) : (msg.pushName || senderNumber),
        isGroup,
        body,
        hasMedia,
        mediaType,
        mediaUrls,
        mentionedIds,
        quotedMessageId,
        quotedParticipant,
        quotedRemoteJid,
        hasQuotedMessage,
        botIds,
        timestamp: msg.messageTimestamp,
      };

      messageQueue.push(event);
      if (messageQueue.length > MAX_QUEUE_SIZE) {
        messageQueue.shift();
      }
    }
  });
}

// HTTP server
const app = express();
app.use(express.json());

// Host-header validation — defends against DNS rebinding.
// The bridge binds loopback-only (127.0.0.1) but a victim browser on
// the same machine could be tricked into fetching from an attacker
// hostname that TTL-flips to 127.0.0.1. Reject any request whose Host
// header doesn't resolve to a loopback alias.
// See GHSA-ppp5-vxwm-4cf7.
const _ACCEPTED_HOST_VALUES = new Set([
  'localhost',
  '127.0.0.1',
  '[::1]',
  '::1',
]);

app.use((req, res, next) => {
  const raw = (req.headers.host || '').trim();
  if (!raw) {
    return res.status(400).json({ error: 'Missing Host header' });
  }
  // Strip port suffix: "localhost:3000" → "localhost"
  const hostOnly = (raw.includes(':')
    ? raw.substring(0, raw.lastIndexOf(':'))
    : raw
  ).replace(/^\[|\]$/g, '').toLowerCase();
  if (!_ACCEPTED_HOST_VALUES.has(hostOnly)) {
    return res.status(400).json({
      error: 'Invalid Host header. Bridge accepts loopback hosts only.',
    });
  }
  next();
});

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// DM Watchlist — track conversations Mirna initiated
// When Mirna sends a DM, the chat is auto-watched.
// Replies from watched chats are persisted to DB and queued.
// Mirna NEVER auto-replies — Caju decides follow-up.
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// dmWatchlist is now a Map<chatId, WatchEntry> with metadata:
//   { chatId, addedAt, status, lastReplyAt, lastMeAt }
// status: "watching" | "replied" | "concluded" | "expired"
const dmWatchlist = new Map();
// LID↔JID bidirectional map — Baileys 7 uses LIDs for DM chatIds,
// but we store phone-based JIDs in the watchlist (e.g. 554899499666@s.whatsapp.net).
// This map lets us match LID-based chatIds against the phone-based watchlist.
const lidToJid = new Map(); // e.g. "181750181404871@lid" → "554899499666@s.whatsapp.net"
const jidToLid = new Map(); // e.g. "554899499666@s.whatsapp.net" → "181750181404871@lid"

// ─── DM Watchlist persistence ─────────────────────────────────────
const DM_WATCHLIST_PATH = path.join(path.dirname(SESSION_DIR), 'dm_watchlist.json');

/** Persist current watchlist to disk (called on every add/remove/update) */
function saveWatchlist() {
  try {
    const entries = [];
    for (const [chatId, entry] of dmWatchlist) {
      entries.push({ chatId, ...entry });
    }
    writeFileSync(DM_WATCHLIST_PATH, JSON.stringify(entries, null, 2));
  } catch (e) {
    console.error(`[dm-watch] Failed to save watchlist: ${e.message}`);
  }
}

/** Load watchlist from disk (called on startup, AFTER loadLidMappings) */
function loadWatchlist() {
  try {
    if (!existsSync(DM_WATCHLIST_PATH)) return;
    const raw = readFileSync(DM_WATCHLIST_PATH, 'utf-8');
    const data = JSON.parse(raw);
    if (Array.isArray(data)) {
      let loaded = 0;
      for (const entry of data) {
        // Legacy format: plain string — convert to object with metadata
        if (typeof entry === 'string') {
          const now = Math.floor(Date.now() / 1000);
          dmWatchlist.set(entry, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
          loaded++;
        } else if (entry && entry.chatId) {
          // New format: object with metadata
          dmWatchlist.set(entry.chatId, {
            addedAt: entry.addedAt || Math.floor(Date.now() / 1000),
            status: entry.status || 'watching',
            lastReplyAt: entry.lastReplyAt || null,
            lastMeAt: entry.lastMeAt || null,
          });
          loaded++;
        }
      }
      // Purge entries older than 24h or with status concluded/expired
      purgeExpiredWatchlist();
      console.log(`[dm-watch] Loaded ${loaded} entries from ${DM_WATCHLIST_PATH} (active: ${dmWatchlist.size})`);
    }
  } catch (e) {
    console.error(`[dm-watch] Failed to load watchlist: ${e.message}`);
  }
}

/** Remove entries that are expired (>24h) or concluded */
function purgeExpiredWatchlist() {
  const now = Math.floor(Date.now() / 1000);
  const MAX_AGE = 24 * 60 * 60; // 24 hours
  let purged = 0;
  for (const [chatId, entry] of dmWatchlist) {
    const age = now - entry.addedAt;
    if (entry.status === 'concluded' || entry.status === 'expired' || age > MAX_AGE) {
      dmWatchlist.delete(chatId);
      purged++;
    }
  }
  if (purged > 0) {
    saveWatchlist();
    console.log(`[dm-watch] Purged ${purged} expired/concluded entries`);
  }
}

/**
 * Load LID↔phone mappings from session files.
 * Forward format: lid-mapping-{PHONE}.json contains a string (the LID number)
 * Reverse format: lid-mapping-{LID}_reverse.json contains a string (the phone number)
 */
function loadLidMappings() {
  const sessionDir = SESSION_DIR;
  if (!existsSync(sessionDir)) return;
  const files = readdirSync(sessionDir).filter(f => f.startsWith('lid-mapping-') && !f.includes('_reverse'));
  let count = 0;
  for (const file of files) {
    try {
      const raw = readFileSync(path.join(sessionDir, file), 'utf-8');
      const data = JSON.parse(raw);
      // Extract phone from filename: lid-mapping-{PHONE}.json
      const phoneFromName = file.replace('lid-mapping-', '').replace('.json', '');
      if (typeof data === 'string') {
        // Forward format: file contains LID string, phone is in filename
        const lidFull = data.includes('@') ? data : `${data}@lid`;
        const jidFull = phoneFromName.includes('@') ? phoneFromName : `${phoneFromName}@s.whatsapp.net`;
        lidToJid.set(lidFull, jidFull);
        jidToLid.set(jidFull, lidFull);
        count++;
      } else if (typeof data === 'object' && data !== null) {
        // Dict format (legacy): { "LID_NUMBER": "PHONE_NUMBER", ... }
        for (const [lid, phone] of Object.entries(data)) {
          const lidFull = lid.includes('@') ? lid : `${lid}@lid`;
          const jidFull = phone.includes('@') ? phone : `${phone}@s.whatsapp.net`;
          lidToJid.set(lidFull, jidFull);
          jidToLid.set(jidFull, lidFull);
          count++;
        }
      }
    } catch {}
  }
  console.log(`[lid-map] Loaded ${count} LID↔JID mappings from ${files.length} files`);
}

/** Check if a chatId matches the DM watchlist (handles both JID and LID formats) */
function checkWatchedDM(chatId, isGroup) {
  if (isGroup) return false;
  if (dmWatchlist.has(chatId)) return true;
  // Try resolving LID→JID
  const resolvedJid = lidToJid.get(chatId);
  if (resolvedJid && dmWatchlist.has(resolvedJid)) return true;
  // Try resolving JID→LID (less common but just in case)
  const resolvedLid = jidToLid.get(chatId);
  if (resolvedLid && dmWatchlist.has(resolvedLid)) return true;
  return false;
}

/** Check if a sender's phone number is in our contacts DB (for DM_MODE='contacts') */
function checkContactDM(senderNumber) {
  if (!senderNumber) return false;
  try {
    const cleanPhone = senderNumber.replace(/[^0-9]/g, '');
    // Match on last 8 digits of phone (handles country code variations)
    const row = msgDb.prepare(
      'SELECT 1 FROM contacts WHERE phone LIKE ? LIMIT 1'
    ).get(`%${cleanPhone.slice(-8)}%`);
    return !!row;
  } catch (e) {
    return false;
  }
}

/** Get the watchlist entry for a chatId (resolving LID→JID) */
function getWatchEntry(chatId) {
  if (dmWatchlist.has(chatId)) return dmWatchlist.get(chatId);
  const resolvedJid = lidToJid.get(chatId);
  if (resolvedJid && dmWatchlist.has(resolvedJid)) return dmWatchlist.get(resolvedJid);
  const resolvedLid = jidToLid.get(chatId);
  if (resolvedLid && dmWatchlist.has(resolvedLid)) return dmWatchlist.get(resolvedLid);
  return null;
}

/** Update a watchlist entry's status/timestamps (resolving LID→JID) */
function updateWatchEntry(chatId, updates) {
  // Find the canonical key in the Map
  let key = chatId;
  if (!dmWatchlist.has(key)) {
    const resolvedJid = lidToJid.get(key);
    if (resolvedJid && dmWatchlist.has(resolvedJid)) key = resolvedJid;
    else {
      const resolvedLid = jidToLid.get(key);
      if (resolvedLid && dmWatchlist.has(resolvedLid)) key = resolvedLid;
      else return; // not in watchlist
    }
  }
  const entry = dmWatchlist.get(key);
  Object.assign(entry, updates);
  dmWatchlist.set(key, entry);
  saveWatchlist();
}

/** Resolve a chatId to its phone-based JID (for consistent DB storage) */
function resolveDmChatId(chatId) {
  if (chatId.includes('@s.whatsapp.net')) return chatId;
  const resolved = lidToJid.get(chatId);
  return resolved || chatId;
}

// ─── Poll for new messages (long-poll style) ─────────────────────────
app.get('/messages', (req, res) => {
  const msgs = messageQueue.splice(0, messageQueue.length);
  res.json(msgs);
});

// Send a message
app.post('/send', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, message, replyTo } = req.body;
  if (!chatId || !message) {
    return res.status(400).json({ error: 'chatId and message are required' });
  }

  try {
    const chunks = splitLongMessage(formatOutgoingMessage(message));
    const messageIds = [];
    for (let i = 0; i < chunks.length; i += 1) {
      const sent = await sendWithTimeout(chatId, { text: chunks[i] });
      trackSentMessageId(sent);
      if (sent?.key?.id) messageIds.push(sent.key.id);
      if (chunks.length > 1 && i < chunks.length - 1) {
        await sleep(CHUNK_DELAY_MS);
      }
    }

    res.json({
      success: true,
      messageId: messageIds[messageIds.length - 1],
      messageIds,
    });
    // Auto-watch DM conversations initiated by Mirna
    if (!chatId.endsWith('@g.us')) {
      const now = Math.floor(Date.now() / 1000);
      dmWatchlist.set(chatId, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
      const lid = jidToLid.get(chatId);
      if (lid) dmWatchlist.set(lid, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
      saveWatchlist();
      console.log(`[dm-watch] Now watching: ${chatId}${lid ? ` (+LID: ${lid})` : ''} (total: ${dmWatchlist.size})`);
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Edit a previously sent message
app.post('/edit', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, messageId, message } = req.body;
  if (!chatId || !messageId || !message) {
    return res.status(400).json({ error: 'chatId, messageId, and message are required' });
  }

  try {
    const key = { id: messageId, fromMe: true, remoteJid: chatId };
    const chunks = splitLongMessage(formatOutgoingMessage(message));
    const messageIds = [];

    await sendWithTimeout(chatId, { text: chunks[0], edit: key });
    if (chunks.length > 1) {
      for (let i = 1; i < chunks.length; i += 1) {
        const sent = await sendWithTimeout(chatId, { text: chunks[i] });
        trackSentMessageId(sent);
        if (sent?.key?.id) messageIds.push(sent.key.id);
        if (i < chunks.length - 1) {
          await sleep(CHUNK_DELAY_MS);
        }
      }
    }

    res.json({ success: true, messageIds });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// MIME type map and media type inference for /send-media
const MIME_MAP = {
  jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
  webp: 'image/webp', gif: 'image/gif',
  mp4: 'video/mp4', mov: 'video/quicktime', avi: 'video/x-msvideo',
  mkv: 'video/x-matroska', '3gp': 'video/3gpp',
  pdf: 'application/pdf',
  doc: 'application/msword',
  docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
};

function inferMediaType(ext) {
  if (['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext)) return 'image';
  if (['mp4', 'mov', 'avi', 'mkv', '3gp'].includes(ext)) return 'video';
  if (['ogg', 'opus', 'mp3', 'wav', 'm4a'].includes(ext)) return 'audio';
  return 'document';
}

// Send media (image, video, document) natively
app.post('/send-media', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }

  const { chatId, filePath, mediaType, caption, fileName } = req.body;
  if (!chatId || !filePath) {
    return res.status(400).json({ error: 'chatId and filePath are required' });
  }

  try {
    if (!existsSync(filePath)) {
      return res.status(404).json({ error: `File not found: ${filePath}` });
    }

    const buffer = readFileSync(filePath);
    const ext = filePath.toLowerCase().split('.').pop();
    const type = mediaType || inferMediaType(ext);
    let msgPayload;

    switch (type) {
      case 'image':
        msgPayload = { image: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'image/jpeg' };
        break;
      case 'video':
        msgPayload = { video: buffer, caption: caption || undefined, mimetype: MIME_MAP[ext] || 'video/mp4' };
        break;
      case 'audio': {
        // WhatsApp only renders a native voice bubble (ptt) when the file is ogg/opus.
        // If the caller passes mp3, wav, m4a etc. (e.g. from Edge TTS / NeuTTS),
        // silently convert to ogg/opus via ffmpeg so ptt is always honoured.
        let audioBuffer = buffer;
        let audioExt = ext;
        const needsConversion = !['ogg', 'opus'].includes(ext);
        let tmpPath = null;
        if (needsConversion) {
          tmpPath = path.join(tmpdir(), `hermes_voice_${randomBytes(6).toString('hex')}.ogg`);
          try {
            execSync(
              `ffmpeg -y -i ${JSON.stringify(filePath)} -ar 48000 -ac 1 -c:a libopus ${JSON.stringify(tmpPath)}`,
              { timeout: 30000, stdio: 'pipe' }
            );
            audioBuffer = readFileSync(tmpPath);
            audioExt = 'ogg';
          } catch (convErr) {
            // ffmpeg not available or conversion failed — fall back to original format
            console.warn('[bridge] ffmpeg conversion failed, sending as file attachment:', convErr.message);
          } finally {
            try { if (tmpPath && existsSync(tmpPath)) unlinkSync(tmpPath); } catch (_) {}
          }
        }
        const audioMime = (audioExt === 'ogg' || audioExt === 'opus') ? 'audio/ogg; codecs=opus' : 'audio/mpeg';
        msgPayload = { audio: audioBuffer, mimetype: audioMime, ptt: audioExt === 'ogg' || audioExt === 'opus' };
        break;
      }
      case 'document':
      default:
        msgPayload = {
          document: buffer,
          fileName: fileName || path.basename(filePath),
          caption: caption || undefined,
          mimetype: MIME_MAP[ext] || 'application/octet-stream',
        };
        break;
    }

    const sent = await sendWithTimeout(chatId, msgPayload);

    trackSentMessageId(sent);

    res.json({ success: true, messageId: sent?.key?.id });
    // Auto-watch DM conversations initiated by Mirna
    if (!chatId.endsWith('@g.us')) {
      const now = Math.floor(Date.now() / 1000);
      dmWatchlist.set(chatId, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
      const lid = jidToLid.get(chatId);
      if (lid) dmWatchlist.set(lid, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
      saveWatchlist();
      console.log(`[dm-watch] Now watching: ${chatId}${lid ? ` (+LID: ${lid})` : ''} (total: ${dmWatchlist.size})`);
    }
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Typing indicator
app.post('/typing', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected' });
  }

  const { chatId } = req.body;
  if (!chatId) return res.status(400).json({ error: 'chatId required' });

  try {
    await sock.sendPresenceUpdate('composing', chatId);
    res.json({ success: true });
  } catch (err) {
    res.json({ success: false });
  }
});

// Chat info
app.get('/chat/:id', async (req, res) => {
  const chatId = req.params.id;
  const isGroup = chatId.endsWith('@g.us');

  if (isGroup && sock) {
    try {
      const metadata = await sock.groupMetadata(chatId);
      // Persist group metadata for analysis
      persistGroupMetadata(chatId, metadata.subject, metadata.participants.length);
      // Also persist description in group_metadata
      try {
        if (metadata.desc) {
          msgDb.prepare(`UPDATE group_metadata SET description = ? WHERE chat_id = ?`).run(metadata.desc, chatId);
        }
      } catch(e) {}
      // Return participants with resolved names and phones
      const participants = metadata.participants.map(p => {
        const lid = p.id || '';
        const phone = lidToPhone[lid] || '';
        const isAdmin = !!(p.admin === 'admin' || p.admin === 'superadmin');
        // Try resolving name from contactMap too
        const cInfo = contactMap.get(lid) || contactMap.get(lid.replace('@lid','') + '@s.whatsapp.net') || {};
        const name = cInfo.name || '';
        return { id: lid, phone, admin: isAdmin, name };
      });
      return res.json({
        name: metadata.subject,
        desc: metadata.desc || '',
        descOwner: metadata.descOwner || '',
        creator: metadata.owner || '',
        createdAt: metadata.creation || 0,
        isGroup: true,
        participants,
        participantCount: metadata.participants.length,
      });
    } catch {
      // Fall through to default
    }
  }

  res.json({
    name: chatId.replace(/@.*/, ''),
    isGroup,
    participants: [],
  });
});

// Health check
// QR code data — for generating image externally
app.get('/qr-image', (req, res) => {
  if (!currentQR) return res.status(404).json({ error: 'No QR code available' });
  res.json({ qr: currentQR });
});

app.get('/health', (req, res) => {
  // Include contacts count from in-memory contact map
  const namedCount = [...contactMap.values()].filter(c => c.name).length;
  res.json({
    status: connectionState,
    queueLength: messageQueue.length,
    uptime: process.uptime(),
    scriptHash: SCRIPT_HASH,
    baileysContacts: contactMap.size,
    namedContacts: namedCount
  });
});

// Get all contacts from Baileys store (includes names from phone's address book)
app.get('/contacts', (req, res) => {
  if (!sock) {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const baileysContacts = contactMap;
    const contacts = [];
    for (const [id, info] of contactMap.entries()) {
      const name = info.name || info.notify || '';
      if (!name && !id.includes('@g.us')) continue; // skip unnamed individuals
      if (id.includes('@g.us')) continue; // skip groups
      const phone = id.replace(/@.*/, '');
      contacts.push({ id, phone, name });
    }
    // Sort: named first
    contacts.sort((a, b) => {
      if (a.name && !b.name) return -1;
      if (!a.name && b.name) return 1;
      return a.name.localeCompare(b.name);
    });
    res.json({ total: contacts.length, named: contacts.filter(c => c.name).length, contacts });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Check if a phone number is on WhatsApp
app.get('/on-whatsapp/:jid', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const jid = req.params.jid;
    const result = await sock.onWhatsApp(jid);
    res.json({ success: true, result });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Force resync of app state (contacts, etc.) — triggers contacts.upsert events
app.post('/force-sync', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const collections = req.body?.collections || ['regular'];
    logger.info(`Force resync of: ${collections.join(', ')}`);
    await sock.resyncAppState(collections, false);
    res.json({ success: true, message: `Resync triggered for: ${collections.join(', ')}` });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Batch resolve names for phone numbers using onWhatsApp + profile queries
app.post('/resolve-names', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  if (!msgDb) {
    return res.status(500).json({ error: 'DB not initialized' });
  }
  try {
    const phones = req.body?.phones || [];
    const batchSize = req.body?.batchSize || 50;
    const results = { resolved: 0, failed: 0, names: {} };

    // Process in batches to avoid rate limiting
    for (let i = 0; i < phones.length; i += batchSize) {
      const batch = phones.slice(i, i + batchSize);
      try {
        // onWhatsApp returns JIDs and existence info
        const waResults = await sock.onWhatsApp(...batch);
        for (const r of waResults) {
          if (r.exists && r.jid) {
            const phone = r.jid.replace(/@.*/, '');
            // Check if we already have a name for this contact
            const existing = contactMap.get(r.jid);
            if (existing?.name && existing.name !== '.') {
              results.names[phone] = existing.name;
              results.resolved++;
            } else if (existing?.notify && existing.notify !== '.') {
              results.names[phone] = existing.notify;
              results.resolved++;
            }
            // Persist JID mapping to contacts DB
            try {
              msgDb.prepare(`
                INSERT INTO contacts (phone, jid, last_seen)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(phone) DO UPDATE SET
                  jid = CASE WHEN ? != '' THEN ? ELSE contacts.jid END,
                  last_seen = CURRENT_TIMESTAMP
              `).run(phone, r.jid, r.jid, r.jid);
            } catch(e) {}
          }
        }
      } catch(e) {
        logger.warn({ err: e }, `onWhatsApp batch failed at ${i}`);
        results.failed += batch.length;
      }
      // Small delay between batches
      if (i + batchSize < phones.length) {
        await new Promise(r => setTimeout(r, 500));
      }
    }
    res.json(results);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Update WhatsApp profile display name
app.post('/update-profile-name', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const name = req.body?.name;
    if (!name) {
      return res.status(400).json({ error: 'Missing "name" in body' });
    }
    await sock.updateProfileName(name);
    res.json({ success: true, name });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ─── Pairing Code (phone number link) ────────────────────────────
app.post('/pair-code', async (req, res) => {
  if (!sock) return res.status(503).json({ error: 'Socket not initialized' });
  const { phone } = req.body;
  if (!phone) return res.status(400).json({ error: 'Missing "phone" in body (e.g. 5548991772279)' });
  try {
    const code = await sock.requestPairingCode(phone);
    console.log(`📱 Pairing code for ${phone}: ${code}`);
    res.json({ success: true, code, phone });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// ─── DM Watchlist endpoints ────────────────────────────────────────
// List watched DMs with metadata
app.get('/dm-watchlist', (req, res) => {
  const entries = [];
  for (const [chatId, entry] of dmWatchlist) {
    entries.push({ chatId, ...entry });
  }
  res.json({ watching: entries });
});

// Manually add a DM to watchlist
app.post('/dm-watchlist', (req, res) => {
  const { chatId } = req.body;
  if (!chatId) return res.status(400).json({ error: 'Missing chatId' });
  const now = Math.floor(Date.now() / 1000);
  dmWatchlist.set(chatId, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
  // Also add the LID counterpart if we have it
  const lid = jidToLid.get(chatId);
  if (lid) dmWatchlist.set(lid, { addedAt: now, status: 'watching', lastReplyAt: null, lastMeAt: null });
  saveWatchlist();
  console.log(`[dm-watch] Manually added: ${chatId}${lid ? ` (+LID: ${lid})` : ''} (total: ${dmWatchlist.size})`);
  const entries = [];
  for (const [cid, entry] of dmWatchlist) entries.push({ chatId: cid, ...entry });
  res.json({ success: true, watching: entries });
});

// Remove a DM from watchlist (or update status)
app.delete('/dm-watchlist', (req, res) => {
  const { chatId } = req.body;
  if (!chatId) return res.status(400).json({ error: 'Missing chatId' });
  dmWatchlist.delete(chatId);
  // Also remove the LID counterpart if we have it
  const lid = jidToLid.get(chatId);
  if (lid) dmWatchlist.delete(lid);
  saveWatchlist();
  console.log(`[dm-watch] Removed: ${chatId}${lid ? ` (+LID: ${lid})` : ''} (total: ${dmWatchlist.size})`);
  const entries = [];
  for (const [cid, entry] of dmWatchlist) entries.push({ chatId: cid, ...entry });
  res.json({ success: true, watching: entries });
});

// Update watchlist entry status (e.g. mark as concluded)
app.patch('/dm-watchlist', (req, res) => {
  const { chatId, status } = req.body;
  if (!chatId || !status) return res.status(400).json({ error: 'Missing chatId or status' });
  const validStatuses = ['watching', 'replied', 'concluded', 'expired'];
  if (!validStatuses.includes(status)) return res.status(400).json({ error: `Invalid status. Must be one of: ${validStatuses.join(', ')}` });
  updateWatchEntry(chatId, { status });
  console.log(`[dm-watch] Status updated: ${chatId} → ${status}`);
  const entries = [];
  for (const [cid, entry] of dmWatchlist) entries.push({ chatId: cid, ...entry });
  res.json({ success: true, watching: entries });
});

// Get recent DM replies from watched conversations
// Includes from_me messages so the agent can determine if Caju is already
// handling the conversation (no follow-up suggestion needed).
app.get('/dm-replies', (req, res) => {
  if (!msgDb) return res.status(500).json({ error: 'DB not initialized' });
  const limit = parseInt(req.query?.limit) || 20;
  const includeAll = req.query?.include_all === 'true'; // include from_me messages
  const watched = Array.from(dmWatchlist.keys());
  if (watched.length === 0) return res.json({ replies: [], conversations: [] });
  const placeholders = watched.map(() => '?').join(',');
  try {
    // Legacy endpoint: only non-from-me (backward compat)
    const rows = msgDb.prepare(`
      SELECT message_id, chat_id, chat_name, sender_name, sender_phone, from_me, body, timestamp
      FROM messages
      WHERE chat_id IN (${placeholders})
        AND is_group = 0 ${includeAll ? '' : 'AND from_me = 0'}
      ORDER BY timestamp DESC LIMIT ?
    `).all(...watched, limit);

    // New: per-conversation summary with "caju_already_responded" flag
    // For each watched contact, check if the last from_me message is AFTER
    // the last non-from_me message — if so, Caju is handling it.
    const conversations = [];
    const uniqueChats = [...new Set(rows.map(r => r.chat_id))];
    for (const chatId of uniqueChats) {
      const lastMe = msgDb.prepare(`
        SELECT MAX(timestamp) as ts FROM messages
        WHERE chat_id = ? AND is_group = 0 AND from_me = 1
      `).get(chatId);
      const lastThem = msgDb.prepare(`
        SELECT MAX(timestamp) as ts FROM messages
        WHERE chat_id = ? AND is_group = 0 AND from_me = 0
      `).get(chatId);
      const lastThemMsg = msgDb.prepare(`
        SELECT body, sender_name, timestamp FROM messages
        WHERE chat_id = ? AND is_group = 0 AND from_me = 0
        ORDER BY timestamp DESC LIMIT 1
      `).get(chatId);
      conversations.push({
        chat_id: chatId,
        chat_name: lastThemMsg?.sender_name || chatId,
        last_reply: lastThemMsg?.body || null,
        last_reply_ts: lastThem?.ts || null,
        last_me_ts: lastMe?.ts || null,
        caju_already_responded: (lastMe?.ts || 0) > (lastThem?.ts || 0),
      });
    }

    res.json({ replies: rows, conversations });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Fetch business profile for a JID — returns name for business accounts
app.get('/business-profile/:jid', async (req, res) => {
  if (!sock || connectionState !== 'connected') {
    return res.status(503).json({ error: 'Not connected to WhatsApp' });
  }
  try {
    const jid = req.params.jid;
    const profile = await sock.getBusinessProfile(jid);
    res.json({ success: true, profile });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Start
if (PAIR_ONLY) {
  // Pair-only mode: just connect, show QR, save creds, exit. No HTTP server.
  console.log('📱 WhatsApp pairing mode');
  console.log(`📁 Session: ${SESSION_DIR}`);
  console.log();
  startSocket();
} else {
  app.listen(PORT, '127.0.0.1', () => {
    console.log(`🌉 WhatsApp bridge listening on port ${PORT} (mode: ${WHATSAPP_MODE})`);
    console.log(`📁 Session stored in: ${SESSION_DIR}`);
    if (ALLOWED_USERS.size > 0) {
      console.log(`🔒 Allowed users: ${Array.from(ALLOWED_USERS).join(', ')}`);
    } else if (WHATSAPP_MODE === 'self-chat') {
      console.log(`🔒 Self-chat mode — only your own messages to yourself are processed.`);
    } else {
      console.log(`🔒 No WHATSAPP_ALLOWED_USERS set — incoming messages are rejected.`);
      console.log(`   Set WHATSAPP_ALLOWED_USERS=<phone> to authorize specific users,`);
      console.log(`   or WHATSAPP_ALLOWED_USERS=* for an explicit open bot.`);
    }
    console.log();
    startSocket();
  });
}
