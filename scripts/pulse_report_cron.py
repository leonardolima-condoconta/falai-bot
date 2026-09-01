import urllib.request
import json
import sys
from datetime import datetime

def run():
    ENV_PATH = "/opt/data/.env"
    PROXY_URL = "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api"
    SLACK_CHANNEL = "U0AS4CSDUUU"
    REQUESTER_EMAIL = "luana.xavier@condoconta.com.br"

    env = {}
    try:
        with open(ENV_PATH, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip().strip('"').strip("'")
    except Exception as e:
        print(f"Error loading .env: {e}")
        sys.exit(1)

    sa_token = env.get("CONDOPOWER_SA_TOKEN")
    auth_token = env.get("CONDOPOWER_AUTH")
    slack_token = env.get("SLACK_BOT_TOKEN")

    if not sa_token or not auth_token or not slack_token:
        print("Missing required credentials in .env")
        sys.exit(1)

    def call_rpc(method, params):
        payload = json.dumps({"method": method, "params": params}).encode("utf-8")
        req = urllib.request.Request(
            PROXY_URL,
            data=payload,
            headers={
                "X-Service-Account-Token": sa_token,
                "auth": auth_token,
                "Content-Type": "application/json"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            raise Exception(f"RPC {method} failed: {e}")

    try:
        status_res = call_rpc("pulse.round_status", {"requester_email": REQUESTER_EMAIL})
        answers_res = call_rpc("pulse.answers", {"requester_email": REQUESTER_EMAIL})

        if not status_res.get("ok") or not status_res.get("result"):
            raise Exception(f"Status API error: {status_res}")
        if not answers_res.get("ok") or not answers_res.get("result"):
            raise Exception(f"Answers API error: {answers_res}")

        result_status = status_res["result"]["rodadas"][0]
        result_answers = answers_res["result"]["rodadas"][0]["respostas"]
        
        # Formatting Dates
        d1 = datetime.strptime(result_status['inicio'][:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        d2 = datetime.strptime(result_status['fim'][:10], "%Y-%m-%d").strftime("%d/%m/%Y")
        periodo = f"{d1} a {d2}"

        convidados = result_status["convidados"]
        respondidos = result_status["responderam"]
        faltantes = result_status["faltam"]
        adesao = result_status["adesao_pct"]

        area_counts = {}
        for resp in result_answers:
            area = resp["raw"]["area"]
            area_counts[area] = area_counts.get(area, 0) + 1

        is_final = not result_status.get("aberta", True)
        
        if is_final:
            header = "🏁 *Pesquisa Pulse — Agosto/2026* — RESULTADO FINAL\n"
            footer = "\nRodada encerrada. Este foi o último envio automático."
        else:
            header = "📊 *Pesquisa Pulse — Agosto/2026* — Acompanhamento diário\n"
            footer = ""

        msg_body = (
            f"{header}"
            f"🗓 Período: {periodo}\n"
            f"👥 Convidados: {convidados}\n"
            f"✅ Responderam: {respondidos}\n"
            f"⏳ Faltam: {faltantes}\n"
            f"📈 Adesão: {adesao}%\n\n"
            "*Respostas por área:*\n"
        )
        
        for area, count in sorted(area_counts.items()):
            msg_body += f"• {area}: {count}\n"
            
        msg_body += f"\n{footer}\n"
        msg_body += "*by Falai — People*"

        # Send Slack
        slack_payload = json.dumps({
            "channel": SLACK_CHANNEL,
            "text": msg_body,
            "mrkdwn": True
        }).encode("utf-8")
        
        slack_req = urllib.request.Request(
            "https://slack.com/api/chat.postMessage",
            data=slack_payload,
            headers={
                "Authorization": f"Bearer {slack_token}",
                "Content-Type": "application/json"
            }
        )
        
        with urllib.request.urlopen(slack_req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if not res.get("ok"):
                print(f"Slack Error: {res}")
                sys.exit(1)
            else:
                print("Report sent successfully.")

        if is_final:
            # We'll try to use the command in terminal for removal
            print("REMOVING_JOB:413bb7dd1438")

    except Exception as e:
        print(f"API Error: {e}")
        # In case of API error, attempt to send error message to Slack
        try:
            err_msg = "API indisponível no momento — nova tentativa amanhã."
            err_payload = json.dumps({
                "channel": SLACK_CHANNEL,
                "text": f"⚠️ *Aviso Pulse*\n{err_msg}",
                "mrkdwn": True
            }).encode("utf-8")
            err_req = urllib.request.Request(
                "https://slack.com/api/chat.postMessage",
                data=err_payload,
                headers={
                    "Authorization": f"Bearer {slack_token}",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(err_req) as resp:
                pass
        except:
            pass
        print(err_msg)
        sys.exit(0)

if __name__ == "__main__":
    run()
