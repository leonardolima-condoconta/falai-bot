#!/usr/bin/env python3
"""
Scripts de People via condopower-api.
Substitui sync_employees.py, aniversarios.py e tempo_casa.py.
"""
import subprocess, json, sys, os

BASE = os.environ.get("CONDOPOWER_API_URL", "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api")
SA_TOKEN = os.environ.get("CONDOPOWER_SA_TOKEN", "")
AUTH = os.environ.get("CONDOPOWER_AUTH", "")

def call(method, params=None):
    """Chama a API condopower."""
    if params is None:
        params = {}
    r = subprocess.run([
        "curl", "-s", "-X", "POST", f"{BASE}",
        "-H", "Content-Type: application/json",
        "-H", f"X-Service-Account-Token: {SA_TOKEN}",
        "-H", f"auth: {AUTH}",
        "-d", json.dumps({"method":method,"params":params})
    ], capture_output=True, text=True, timeout=600)
    return json.loads(r.stdout)

def sync_roster():
    """Sincroniza cadastro via API."""
    print("🔄 Sincronizando cadastro...")
    r = call("roster.sync")
    if r.get("ok"):
        res = r["result"]
        print(f"✅ Sync: {res.get('employees')} emp, {res.get('departments')} depts, "
              f"{res.get('jobs')} jobs, {res.get('slack_ids_matched')} Slack IDs, "
              f"{res.get('deactivated')} desligados")
    else:
        print(f"❌ Erro: {r.get('error',{}).get('message','?')}")

def send_birthdays():
    """Envia aniversariantes no Slack via API."""
    from datetime import date
    today = date.today()
    if today.weekday() >= 5:
        print(f"Fim de semana ({today}), pulando.")
        return
    
    r = call("celebrations.birthdays", {"reference_date": today.isoformat()})
    if not r.get("ok"):
        print(f"❌ Erro: {r.get('error',{}).get('message','?')}")
        return
    
    res = r["result"]
    celebrants = res.get("celebrants", [])
    if not celebrants:
        print(f"Nenhum aniversariante em {res.get('covered_dates',[])}")
        return
    
    # Resolver @mentions via Slack
    mentions = []
    lista = []
    for c in celebrants:
        sid = c.get("slack_user_id")
        mention = f"<@{sid}>" if sid else c["full_name"]
        mentions.append(mention)
        date_tag = f"(sábado)" if "Sat" in str(c.get('celebrated_on','')) else ""
        date_tag = f"(domingo)" if "Sun" in str(c.get('celebrated_on','')) else date_tag
        lista.append(f"🎂 {mention} — {c['job']} ({c['department']}) {date_tag}")
    
    plural = "s" if len(celebrants) > 1 else ""
    msg = (
        f"🎉 *Comemoração — Aniversário{plural}* 🎉\n\n"
        f"<!channel>, hoje tem{'os' if len(celebrants) > 1 else ''} festa no condomínio! "
        f"Parabéns {', '.join(mentions)}!\n\n"
        f"Que coisa boa podermos fazer parte desse momento, "
        f"desejamos a você{plural} um novo ciclo cheio de alegrias! ✨\n\n"
        f"*Aniversariante{plural} do dia:*\n" + "\n".join(lista) + "\n\n"
        f"Vamos deixar o dia ainda mais especial?\n"
        f"Deixem seus votos aqui na thread! 🥳"
    )
    
    send_slack(msg)
    print(f"✅ {len(celebrants)} aniversariantes enviados")

def send_work_anniversaries():
    """Envia tempo de casa no Slack via API."""
    from datetime import date
    today = date.today()
    if today.weekday() >= 5:
        print(f"Fim de semana ({today}), pulando.")
        return
    
    r = call("celebrations.work_anniversaries", {"reference_date": today.isoformat()})
    if not r.get("ok"):
        print(f"❌ Erro: {r.get('error',{}).get('message','?')}")
        return
    
    res = r["result"]
    celebrants = res.get("celebrants", [])
    if not celebrants:
        print(f"Nenhum tempo de casa em {res.get('covered_dates',[])}")
        return
    
    mentions = []
    for c in celebrants:
        sid = c.get("slack_user_id")
        mention = f"<@{sid}>" if sid else c["full_name"]
        anos = c.get("years", 1)
        mentions.append(f"{mention} ({anos} ano{'s' if anos>1 else ''}) — {c['job']} ({c['department']})")
    
    total = len(celebrants)
    plural = "s" if total > 1 else ""
    tem_plural = "os" if total > 1 else ""
    
    msg = (
        f"🎉 *Comemoração — Tempo de Casa* 🎊\n\n"
        f"Hoje tem{tem_plural} {total} CondoPower{plural} completando mais um ano ao nosso lado:\n"
        + "\n".join(mentions) +
        f"\n\nParabéns! Obrigado por seguirem nessa jornada com a gente. "
        f"O trabalho de vocês e dedicação são muito importantes para nós!\n"
        f"Ficamos muito felizes em ver que todos estão ajudando na missão "
        f"de transformar a vida de quem vive condomínios 🚀\n\n"
        f"<!channel>, vamos deixar o dia ainda mais especial? "
        f"Deixem suas felicitações aqui na thread 💙"
    )
    
    send_slack(msg)
    print(f"✅ {len(celebrants)} tempos de casa enviados")

def send_slack(msg):
    """Envia mensagem no Slack #people-hr."""
    import urllib.request
    token = ""
    with open("/opt/data/.env") as f:
        for line in f:
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.strip().split("=",1)[1].strip('"').strip("'")
    data = json.dumps({"channel":"C0BJLA3H16F","text":msg,"mrkdwn":True}).encode()
    req = urllib.request.Request("https://slack.com/api/chat.postMessage",
        data=data, headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read())
    if not result.get("ok"):
        print(f"⚠️ Slack: {result.get('error')}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: condopower_scripts.py [sync|birthdays|work_anniversaries]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "sync":
        sync_roster()
    elif cmd == "birthdays":
        send_birthdays()
    elif cmd == "work_anniversaries":
        send_work_anniversaries()
    else:
        print(f"Comando desconhecido: {cmd}")