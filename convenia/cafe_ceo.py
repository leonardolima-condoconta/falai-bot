#!/usr/bin/env python3
"""Envia Café com o CEO no Slack #people-hr. Toda quarta 08h45."""
import json, urllib.request, os

CHANNEL = "C0BJLA3H16F"

def get_token():
    return os.environ.get("SLACK_BOT_TOKEN", "")

def main():
    from datetime import date
    today = date.today()
    if today.weekday() != 2:
        print("Hoje não é quarta-feira, pulando.")
        return
    
    msg = (
        "☕ *Café com o CEO!*\n\n"
        "<!channel>, toda quarta-feira, às 08h45. Participação obrigatória para todos!\n\n"
        "_Juntos, alinhados e conectados, vamos mais longe!_ 🚀"
    )
    
    token = get_token()
    data = json.dumps({"channel": CHANNEL, "text": msg, "mrkdwn": True}).encode()
    req = urllib.request.Request("https://slack.com/api/chat.postMessage",
        data=data, headers={"Authorization": f"Bearer {token}", "Content-Type":"application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print("✅ Enviado" if result.get("ok") else f"❌ {result.get('error')}")

if __name__ == "__main__":
    main()