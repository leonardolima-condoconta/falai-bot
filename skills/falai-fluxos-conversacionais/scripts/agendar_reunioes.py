#!/usr/bin/env python3
"""
Agenda 1x1 mensais e avaliacoes semestrais para todos os lideres e seus liderados.
Eventos incluem Google Meet, Falai como participante (people@condoconta.com.br)
e instrucoes com link do bot no Slack.

Uso: cd /opt/data/convenia && PYTHONPATH=/opt/data /opt/data/.venv/bin/python3 -u agendar_reunioes.py
"""
import sqlite3, json, subprocess, time
from datetime import datetime, timedelta, date

DB = "/opt/data/convenia_data/convenia.db"
TOKEN_FILE = "/opt/data/google_token.json"

def get_token():
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    return data["access_token"]

def refresh_token():
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    client_id = data.get("client_id", "764640240643-...")
    with open("/opt/data/google_client_secret.json") as f:
        cs = json.load(f)
    client_secret = cs["installed"]["client_secret"]
    r = subprocess.run([
        "curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
        "-d", f"client_id={client_id}",
        "-d", f"client_secret={client_secret}",
        "-d", f"refresh_token={data['refresh_token']}",
        "-d", "grant_type=refresh_token"
    ], capture_output=True, text=True, timeout=30)
    new_data = json.loads(r.stdout)
    if "access_token" in new_data:
        data["access_token"] = new_data["access_token"]
        with open(TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return data["access_token"]
    return None

def find_free_slot(token, start_date, duration_min=30):
    day = start_date
    while True:
        if day.weekday() >= 5:
            day += timedelta(days=1)
            continue
        tz_offset = "-03:00"
        time_min = f"{day.isoformat()}T09:00:00{tz_offset}"
        time_max = f"{day.isoformat()}T17:00:00{tz_offset}"
        r = subprocess.run([
            "curl", "-s",
            "-H", f"Authorization: Bearer {token}",
            "https://www.googleapis.com/calendar/v3/calendars/primary/freeBusy"
        ], capture_output=True, text=True, timeout=30,
           input=json.dumps({"timeMin": time_min, "timeMax": time_max, "items": [{"id": "primary"}]}))
        try:
            data = json.loads(r.stdout)
            busy = data.get("calendars", {}).get("primary", {}).get("busy", [])
        except:
            busy = []
        for h in range(9, 17):
            for m in [0, 30]:
                s_iso = f"{day.isoformat()}T{h:02d}:{m:02d}:00{tz_offset}"
                e_iso = f"{day.isoformat()}T{h:02d}:{m+duration_min:02d}:00{tz_offset}"
                conflict = any(b.get("start","") < e_iso and b.get("end","") > s_iso for b in busy)
                if not conflict:
                    return s_iso, e_iso
        day += timedelta(days=1)

def create_event(token, summary, description, start_time, end_time, attendees_emails):
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": end_time, "timeZone": "America/Sao_Paulo"},
        "attendees": [{"email": e} for e in attendees_emails] + [{"email": "people@condoconta.com.br"}],
        "conferenceData": {"createRequest": {"requestId": f"falai-{datetime.now().timestamp()}", "conferenceSolutionKey": {"type": "hangoutsMeet"}}},
        "sendUpdates": "all"
    }
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendUpdates=all",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(event)
    ], capture_output=True, text=True, timeout=30)
    data = json.loads(r.stdout)
    return data.get("htmlLink", f"ERRO: {data.get('error',{}).get('message','?')}")

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    pairs = conn.execute("""
        SELECT s.id as lider_id, s.name as lider_nome, s.email as lider_email,
               e.id as colab_id, e.name as colab_nome, e.email as colab_email,
               j.name as cargo
        FROM employees e JOIN employees s ON e.supervisor_id = s.id
        JOIN jobs j ON e.job_id = j.id WHERE e.is_active = 1 ORDER BY s.name, e.name
    """).fetchall()
    conn.close()
    
    token = get_token() or refresh_token()
    now = date.today()
    c1, ca = 0, 0
    
    for pair in pairs:
        s, e = find_free_slot(token, now + timedelta(days=c1 % 30), 30)
        desc_1x1 = f"""1x1: {pair['lider_nome']} & {pair['colab_nome']}
Pauta: {pair['colab_nome']} — {pair['cargo']}
Para registrar este 1x1: https://app.slack.com/client/THLSB1VM4/U08MB56BPG8
Envie: \"@Falai iniciar 1x1 com {pair['colab_nome']}\""""
        create_event(token, f"1x1: {pair['lider_nome']} ↔ {pair['colab_nome']}", desc_1x1, s, e, [pair['lider_email'], pair['colab_email']])
        c1 += 1
        
        sa, ea = find_free_slot(token, now + timedelta(days=ca + 180), 45)
        desc_aval = f"""Avaliacao Semestral: {pair['colab_nome']} ({pair['cargo']})
Lider: {pair['lider_nome']}
Para iniciar: https://app.slack.com/client/THLSB1VM4/U08MB56BPG8
Envie: \"@Falai iniciar avaliacao de {pair['colab_nome']}\""""
        create_event(token, f"Avaliacao: {pair['colab_nome']} ({pair['cargo']})", desc_aval, sa, ea, [pair['lider_email'], pair['colab_email']])
        ca += 1
        
        if c1 % 10 == 0:
            token = refresh_token()
    
    print(f"✅ {c1} 1x1, {ca} avaliacoes")

if __name__ == "__main__":
    main()