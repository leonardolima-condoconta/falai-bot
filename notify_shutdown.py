#!/usr/bin/env python3
"""Notifica shutdown do Falai no Telegram."""
import os, requests

env_file = "/opt/data/.env"
env = {}
if os.path.exists(env_file):
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k] = v

bot_token = env.get("TELEGRAM_BOT_TOKEN", "")
home = env.get("TELEGRAM_HOME_CHANNEL", "")

if bot_token and home:
    try:
        requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json={"chat_id": home, "text": "⚠️ Falai Gateway desligando..."},
            timeout=5
        )
    except:
        pass
