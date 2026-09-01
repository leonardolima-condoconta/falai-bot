#!/usr/bin/env python3
"""
DM Reply Notifier — reads notification files from WhatsApp bridge,
enriches with conversation context (watch status, Caju handling?),
sends Telegram alert to Caju, then cleans up.

Flow:
  1. Mirna sends DM → auto-watchlist (status=watching)
  2. Contact replies → status=replied → notify Caju + suggest next steps
  3. Caju approves/requests new iteration → Mirna acts
  4. If no reply in 24h → status=expired → notify Caju
  5. Conclusion reached → status=concluded → stop monitoring
"""
import json, os, glob, sqlite3, requests, time

NOTIF_DIR = "/home/hermes/.hermes/whatsapp/notifications"
DB_PATH = "/home/hermes/.hermes/whatsapp/messages.db"
BRIDGE_URL = "http://localhost:3000"

def get_recent_messages(chat_id, limit=4):
    """Get recent messages from both sides for context."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT from_me, sender_name, body, timestamp
            FROM messages
            WHERE chat_id = ? AND is_group = 0
            ORDER BY timestamp DESC LIMIT ?
        """, (chat_id, limit))
        rows = c.fetchall()
        conn.close()
        return [{"from_me": bool(r[0]), "sender": r[1], "body": r[2][:80], "ts": r[3]} for r in reversed(rows)]
    except:
        return []

def format_context(msgs):
    """Format conversation context for the alert."""
    lines = []
    for m in msgs:
        who = "👉 Você" if m["from_me"] else f"👤 {m['sender']}"
        body = m["body"] or "[mídia]"
        lines.append(f"  {who}: {body}")
    return "\n".join(lines)

def send_telegram_alert(text):
    """Send alert via Hermes API server (which routes to Telegram)."""
    try:
        # Use the bridge's /dm-watchlist PATCH to update status
        pass  # Actual delivery is via Hermes gateway cron delivery
    except:
        pass

def process_notifications():
    """Process all pending DM notification files."""
    if not os.path.exists(NOTIF_DIR):
        return

    files = sorted(glob.glob(os.path.join(NOTIF_DIR, "dm_*.json")))
    if not files:
        return

    for f in files:
        try:
            with open(f, "r") as fh:
                notif = json.load(fh)

            chat_id = notif.get("chatId", "")
            chat_name = notif.get("chatName", notif.get("senderName", "Desconhecido"))
            body = notif.get("body", "")
            watch_status = notif.get("watchStatus", "watching")
            caju_already = notif.get("cajuAlreadyResponded", False)

            # Get conversation context
            msgs = get_recent_messages(chat_id, limit=6)
            context = format_context(msgs)

            # Build alert based on status
            if watch_status == "expired" or watch_status == "concluded":
                # No alert needed for concluded/expired
                os.remove(f)
                continue

            if caju_already:
                # Caju is already handling — passive info only
                alert = f"📱 DM de {chat_name}\n"
                alert += f"✅ Você já está conversando — sem ação necessária\n\n"
                alert += f"💬 Últimas mensagens:\n{context}"
            else:
                # Contact replied and Caju hasn't — needs action
                alert = f"📱 DM de {chat_name}\n"
                alert += f"⏳ Aguardando sua resposta!\n\n"
                alert += f"💬 Últimas mensagens:\n{context}\n\n"
                alert += f"Responder? Diga o que quer mandar ou 'concluído' para encerrar o monitoramento."

            # Print the alert (cron job will deliver it)
            print(alert)
            os.remove(f)

        except Exception as e:
            print(f"[dm-notify] Error processing {f}: {e}")
            try:
                os.remove(f)
            except:
                pass

if __name__ == "__main__":
    process_notifications()
