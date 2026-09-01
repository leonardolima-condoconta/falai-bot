/**
 * allowlist.js — WhatsApp Bridge user access control
 * 
 * parseAllowedUsers: parses WHATSAPP_ALLOWED_USERS env var (comma-separated JIDs)
 * matchesAllowedUser: checks if a sender is in the allowed list
 *   - Supports direct JID match (5521999999999@s.whatsapp.net)
 *   - Supports phone-only match against LID-mapped numbers
 *   - Reads lid-mapping-*_reverse.json from session dir for LID→phone resolution
 */

import { readFileSync, existsSync, readdirSync } from 'fs';
import path from 'path';

/**
 * Parse comma-separated allowed users string into array of JIDs.
 * Example: "55219xxxx@s.whatsapp.net,55219yyyy@s.whatsapp.net"
 */
export function parseAllowedUsers(envStr) {
  if (!envStr || envStr.trim() === '') return [];
  return envStr.split(',').map(s => s.trim()).filter(Boolean);
}

/**
 * Build LID → phone mapping from session directory.
 * Reads lid-mapping-*_reverse.json files: { "LID": "phone" }
 */
function buildLidPhoneMap(sessionDir) {
  const map = new Map();
  try {
    if (!sessionDir || !existsSync(sessionDir)) return map;
    const files = readdirSync(sessionDir).filter(f => f.startsWith('lid-mapping-') && f.endsWith('_reverse.json'));
    for (const file of files) {
      try {
        const data = JSON.parse(readFileSync(path.join(sessionDir, file), 'utf-8'));
        if (data && typeof data === 'object') {
          for (const [lid, phone] of Object.entries(data)) {
            map.set(lid, phone);
            map.set(lid + '@lid', phone);
          }
        }
      } catch (e) { /* skip corrupted files */ }
    }
  } catch (e) { /* ignore */ }
  return map;
}

/**
 * Check if a senderId is in the allowed users list.
 * 
 * @param {string} senderId - Raw sender ID (e.g., "55219xxx@s.whatsapp.net" or "123456@lid")
 * @param {string[]} allowedUsers - Array of allowed JIDs
 * @param {string} sessionDir - Path to WhatsApp session directory (for LID resolution)
 * @returns {boolean}
 */
export function matchesAllowedUser(senderId, allowedUsers, sessionDir) {
  if (!allowedUsers || allowedUsers.length === 0) return true; // No filter = allow all
  if (!senderId) return false;
  
  // Direct match
  if (allowedUsers.includes(senderId)) return true;
  
  // Try LID → phone resolution
  if (senderId.endsWith('@lid')) {
    const lidPhoneMap = buildLidPhoneMap(sessionDir);
    const phone = lidPhoneMap.get(senderId);
    if (phone) {
      const phoneJid = phone + '@s.whatsapp.net';
      if (allowedUsers.includes(phoneJid)) return true;
      // Also try without @s.whatsapp.net
      if (allowedUsers.includes(phone)) return true;
    }
  }
  
  // Try phone match (strip @s.whatsapp.net from senderId)
  if (senderId.endsWith('@s.whatsapp.net')) {
    const phone = senderId.replace('@s.whatsapp.net', '');
    if (allowedUsers.includes(phone)) return true;
  }
  
  return false;
}
