#!/usr/bin/env python3
import json, urllib.request, urllib.parse

# Token (clean) from binary .env
with open('/opt/data/.env', 'rb') as f:
    data = f.read()
idx = data.find(b'SLACK_BOT_TOKEN=')
start = idx + len(b'SLACK_BOT_TOKEN=')
end = data.find(b'\n', start)
TOKEN = data[start:end].decode('utf-8', errors='replace').strip()

BASE = "https://slack.com/api"

def api_get(method, params):
    url = f"{BASE}/{method}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOKEN})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

def api_post(method, form):
    url = f"{BASE}/{method}"
    body = urllib.parse.urlencode(form).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/x-www-form-urlencoded",
    }, method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())

targets = [
    ("Amanda Elena de Almeida", "amanda.almeida@condoconta.com.br"),
    ("Ana Paula de Britto Sosa", "ana.britto@condoconta.com.br"),
]

MESSAGE = ("Oi! 😊 Passando pra avisar: o Rodrigo marcou uma conversa com vocês "
           "às 17h de hoje sobre a festa de fim de ano, na sala 1. "
           "Conto com vocês lá! 🎉")

# First, build name->uid map via users.list (in case lookupByEmail lacks scope)
print("=== Resolvendo UIDs ===")
for name, email in targets:
    uid = None
    # Try lookupByEmail first
    try:
        r = api_get("users.lookupByEmail", {"email": email})
        if r.get("ok") and r.get("user", {}).get("id"):
            uid = r["user"]["id"]
            print(f"{name}: lookupByEmail -> {uid}")
        else:
            print(f"{name}: lookupByEmail fail: {r.get('error')}")
    except Exception as e:
        print(f"{name}: lookupByEmail exception: {e}")

    if not uid:
        # fallback to users.list filter by real_name
        try:
            r = api_get("users.list", {"limit": 1000})
            for u in r.get("members", []):
                rn = (u.get("real_name") or "").lower()
                dn = (u.get("profile", {}).get("display_name") or "").lower()
                prof = (u.get("profile", {}) or {})
                em = (prof.get("email") or "").lower()
                if email.lower() == em or name.lower() in rn or name.lower() in dn:
                    uid = u["id"]
                    print(f"{name}: users.list -> {uid} (real_name={u.get('real_name')})")
                    break
        except Exception as e:
            print(f"{name}: users.list exception: {e}")

    if uid:
        # Open DM
        try:
            dm = api_post("conversations.open", {"users": uid})
            ch = dm.get("channel", {}).get("id")
            print(f"{name}: DM channel -> {ch} ok={dm.get('ok')}")
            if ch:
                sent = api_post("chat.postMessage", {"channel": ch, "text": MESSAGE, "mrkdwn": True})
                print(f"{name}: postMessage ok={sent.get('ok')} ts={sent.get('ts')} err={sent.get('error')}")
        except Exception as e:
            print(f"{name}: DM/post exception: {e}")
    else:
        print(f"{name}: UID NAO RESOLVIDO")

print("=== FIM ===")
