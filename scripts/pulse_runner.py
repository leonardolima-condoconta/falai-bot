import urllib.request
import urllib.parse
import json
import os
import sys

def get_env():
    env_path = '/opt/data/.env'
    if not os.path.exists(env_path):
        print(f"Error: {env_path} not found")
        sys.exit(1)
    
    with open(env_path, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    
    env = {}
    for line in content.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def call_api(url, method, payload, sa_token, auth):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Service-Account-Token', sa_token)
    req.add_header('auth', auth)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def send_slack_dm(url, token, channel, text):
    payload = {
        "channel": channel,
        "text": text,
        "mrkdwn": True
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

def main():
    env = get_env()
    sa_token = env.get('CONDOPOWER_SA_TOKEN')
    auth = env.get('CONDOPOWER_AUTH')
    slack_token = env.get('SLACK_BOT_TOKEN')
    api_url = env.get('CONDOPOWER_API_URL')
    
    if not all([sa_token, auth, slack_token, api_url]):
        print("Error: Missing required environment variables.")
        sys.exit(1)

    email = "luana.xavier@condoconta.com.br"
    luana_id = "U0AS4CSDUUU"

    # 1. Get Round Status
    status_payload = {
        "method": "pulse.round_status",
        "params": {"requester_email": email}
    }
    status_resp = call_api(api_url, 'POST', status_payload, sa_token, auth)

    if "error" in status_resp:
        print(f"API_ERROR: {status_resp['error']}")
        send_slack_dm("https://slack.com/api/chat.postMessage", slack_token, luana_id, "API indisponível no momento — nova tentativa amanhã.")
        sys.exit(0)

    aberta = status_resp.get("aberta", False)
    periodo = status_resp.get("periodo", "Agosto/2026")
    convidados = status_resp.get("convidados", 0)
    respondidos = status_resp.get("respondidos", 0)
    faltantes = status_resp.get("faltantes", 0)
    
    adesao = 0
    if convidados > 0:
        adesao = round((respondidos / convidados) * 100, 1)

    # 2. Get Answers for area breakdown
    answers_payload = {
        "method": "pulse.answers",
        "params": {"requester_email": email}
    }
    answers_resp = call_api(api_url, 'POST', answers_payload, sa_token, auth)

    if "error" in answers_resp:
        print("API_ERROR_ANSWERS")
        send_slack_dm("https://slack.com/api/chat.postMessage", slack_token, luana_id, "API indisponível no momento — nova tentativa amanhã.")
        sys.exit(0)

    # Process areas
    area_counts = {}
    # The API might return data in different ways. We try to be robust.
    # Expecting: {"data": [{"area": "X", "count": Y}, ...]} or {"data": {"X": Y, ...}}
    data_field = answers_resp.get("data", [])
    
    if isinstance(data_field, dict):
        area_counts = data_field
    elif isinstance(data_field, list):
        for item in data_field:
            if isinstance(item, dict):
                a = item.get("area")
                c = item.get("count", 1)
                if a:
                    area_counts[a] = area_counts.get(a, 0) + c
            elif isinstance(item, str):
                area_counts[item] = area_counts.get(item, 0) + 1

    # 3. Build Message
    if not aberta:
        # FINAL REPORT
        msg = (
            f"🏁 *Pesquisa Pulse — Agosto/2026* — RESULTADO FINAL\n\n"
            f"🗓 Período: {periodo}\n"
            f"👥 Convidados: {convidados}\n"
            f"✅ Responderam: {respondidos}\n"
            f"⏳ Faltam: {faltantes}\n"
            f"📈 Adesão: {adesao}%\n\n"
            f"*Respostas por área:*\n"
        )
        # Sort areas by count descending
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        for area, count in sorted_areas:
            msg += f"• {area}: {count}\n"
        
        msg += "\nRodada encerrada. Este foi o último envio automático.\n\n*by Falai — People*"
        
        # Signal for cron removal
        print("JOB_CLOSED")
    else:
        # DAILY REPORT
        msg = (
            f"📊 *Pesquisa Pulse — Agosto/2026* — Acompanhamento diário\n\n"
            f"🗓 Período: {periodo}\n"
            f"👥 Convidados: {convidados}\n"
            f"✅ Responderam: {respondidos}\n"
            f"⏳ Faltam: {faltantes}\n"
            f"📈 Adesão: {adesao}%\n\n"
            f"*Respostas por área:*\n"
        )
        # Sort areas by count descending
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        for area, count in sorted_areas:
            msg += f"• {area}: {count}\n"
            
        msg += "\n*by Falai — People*"

    # 4. Send to Slack
    send_slack_dm("https://slack.com/api/chat.postMessage", slack_token, luana_id, msg)
    print("SUCCESS")

if __name__ == "__main__":
    main()
