import urllib.request
import urllib.parse
import json
import os
import sys

# Config
ENV_PATH = "/opt/data/.env"
WEBHOOK_URL = "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api"
REQUESTER_EMAIL = "luana.xavier@condoconta.com.br"
SLACK_CHANNEL = "U0AS4CSDUUU"

def get_env_var(key):
    if not os.path.exists(ENV_PATH):
        return None
    with open(ENV_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
    return None

def call_api(method, payload, sa_token, auth):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(WEBHOOK_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-Service-Account-Token', sa_token)
    req.add_header('auth', auth)
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def send_slack(token, channel, text):
    url = "https://slack.com/api/chat.postMessage"
    payload = {
        "channel": channel,
        "text": text,
        "mrkdwn": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {"error": str(e)}

def main():
    sa_token = get_env_var("CONDOPOWER_SA_TOKEN")
    auth = get_env_var("CONDOPOWER_AUTH")
    slack_token = get_env_var("SLACK_BOT_TOKEN")

    if not sa_token or not auth:
        print("CRITICAL: Missing CONDOPOWER credentials.")
        sys.exit(1)

    # 1. Get round status
    status_payload = {
        "method": "pulse.round_status",
        "params": {"requester_email": REQUESTER_EMAIL}
    }
    status_data = call_api("POST", status_payload, sa_token, auth)
    
    if "error" in status_data:
        if slack_token:
            send_slack(slack_token, SLACK_CHANNEL, "API indisponível no momento — nova tentativa amanhã.")
        print("API_UNAVAILABLE")
        sys.exit(0)

    # Check if round is closed
    res_status = status_data.get("result", {})
    is_open = res_status.get("aberta", True)
    
    # 2. Get answers
    answers_payload = {
        "method": "pulse.answers",
        "params": {"requester_email": REQUESTER_EMAIL}
    }
    answers_data = call_api("POST", answers_payload, sa_token, auth)
    
    if "error" in answers_data:
        if slack_token:
            send_slack(slack_token, SLACK_CHANNEL, "API indisponível no momento — nova tentativa amanhã.")
        print("API_UNAVAILABLE")
        sys.exit(0)

    res_answers = answers_data.get("result", {})
    
    periodo = res_status.get("periodo", "N/A")
    convidados = res_status.get("convidados", 0)
    respondidos = res_answers.get("respondidos", 0)
    faltantes = convidados - respondidos
    adesao = (respondidos / convidados * 100) if convidados > 0 else 0
    
    areas = res_answers.get("areas", [])
    area_list = ""
    for a in areas:
        area_list += f"• {a.get('area', 'Sem área')}: {a.get('count', 0)}\n"

    if not is_open:
        header = "🏁 *Pesquisa Pulse — Agosto/2026* — RESULTADO FINAL"
        footer = "Rodada encerrada. Este foi o último envio automático."
        msg = (
            f"{header}\n"
            f"🗓 Período: {periodo}\n"
            f"👥 Convidados: {convidados}\n"
            f"✅ Responderam: {respondidos}\n"
            f"⏳ Faltam: {faltantes}\n"
            f"📈 Adesão: {adesao:.1f}%\n\n"
            f"*Respostas por área:*\n{area_list}\n"
            f"{footer}\n\n"
            f"*by Falai — People*"
        )
        if slack_token:
            send_slack(slack_token, SLACK_CHANNEL, msg)
        print("JOB_REMOVAL_REQUIRED")
    else:
        msg = (
            f"📊 *Pesquisa Pulse — Agosto/2026* — Acompanhamento diário\n"
            f"🗓 Período: {periodo}\n"
            f"👥 Convidados: {convidados}\n"
            f"✅ Responderam: {respondidos}\n"
            f"⏳ Faltam: {faltantes}\n"
            f"📈 Adesão: {adesao:.1f}%\n\n"
            f"*Respostas por área:*\n{area_list}\n"
            f"*by Falai — People*"
        )
        if slack_token:
            send_slack(slack_token, SLACK_CHANNEL, msg)
        print("SUCCESS")

if __name__ == "__main__":
    main()
