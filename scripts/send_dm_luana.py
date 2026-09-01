import urllib.request, json

# Read token from .env binary
with open("/opt/data/.env", "rb") as f:
    data = f.read()
idx = data.find(b"SLACK_BOT_TOKEN=")
start = idx + len(b"SLACK_BOT_TOKEN=")
end = data.find(b"\n", start)
token = data[start:end].decode("utf-8", errors="replace")

# Open DM with Luana Xavier
payload = json.dumps({"users": "U0AS4CSDUUU"}).encode()
req = urllib.request.Request(
    "https://slack.com/api/conversations.open",
    data=payload,
    headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
)
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())
print("conversations.open:", json.dumps(result, indent=2))

if result.get("ok"):
    channel_id = result["channel"]["id"]
    
    msg_text = "Ola, Luana! Tudo bem? :wave:\n\nO Rodrigo Catarcione pediu para eu te perguntar sobre o projeto de gestao dos condopowers (avaliacao, PDI, 1x1 e feedback):\n\n:point_right: *O feedback pode ser feito de qualquer um para qualquer um?*\n\nConsegue me ajudar com essa definicao?\n\n*by Falai — People*"

    msg_payload = json.dumps({
        "channel": channel_id,
        "text": msg_text,
        "mrkdwn": True
    }).encode()
    
    req2 = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=msg_payload,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
    )
    resp2 = urllib.request.urlopen(req2)
    result2 = json.loads(resp2.read())
    print("chat.postMessage:", json.dumps(result2, indent=2))