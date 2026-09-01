import json
import urllib.request

# Read bot token from temp file
with open('/tmp/.slack_bot_token', 'r') as f:
    bot_token = f.read().strip()

# Channel: #people-hr
channel = "C0BJLA3H16F"

# Message
text = "<!channel> 📊 *Pulse de Satisfação* — dia 20! Hora de abrir a pesquisa de clima do mês. Quem vai coordenar a rodada? Me chamem que eu ajudo a abrir e acompanhar a adesão!"

payload = json.dumps({
    "channel": channel,
    "text": text,
    "mrkdwn": True
}).encode("utf-8")

req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=payload,
    headers={
        "Authorization": "Bearer " + bot_token,
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    print("ok:", result.get("ok"))
    print("channel:", result.get("channel"))
    print("ts:", result.get("ts"))
    if not result.get("ok"):
        print("error:", result.get("error"))
except Exception as e:
    print("Exception:", e)