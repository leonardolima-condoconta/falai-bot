#!/usr/bin/env python3
"""
Agenda 1x1 mensais e avaliacoes semestrais SEM CONFLITOS.
Cada pessoa (lider ou liderado) so pode ter 1 reuniao por horario.
"""
import sqlite3, json, subprocess
from datetime import datetime, timedelta, date

DB = "/opt/data/convenia_data/convenia.db"
TOKEN_FILE = "/opt/data/google_token.json"

def get_token():
    with open(TOKEN_FILE) as f:
        return json.load(f)["access_token"]

def refresh_token():
    with open(TOKEN_FILE) as f:
        data = json.load(f)
    with open("/opt/data/google_client_secret.json") as f:
        cs = json.load(f)
    client_secret = cs["installed"]["client_secret"]
    r = subprocess.run([
        "curl", "-s", "-X", "POST", "https://oauth2.googleapis.com/token",
        "-d", f"client_id={data.get('client_id','764640240643-7c7t0pomj4jjmh441glh3d16eo0ih9h1.apps.googleusercontent.com')}",
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

def get_calendar_busy(token, day, tz_offset="-03:00"):
    """Get busy slots for a specific day."""
    time_min = f"{day.isoformat()}T09:00:00{tz_offset}"
    time_max = f"{day.isoformat()}T17:00:00{tz_offset}"
    r = subprocess.run([
        "curl", "-s", "-H", f"Authorization: Bearer {token}",
        "https://www.googleapis.com/calendar/v3/calendars/primary/freeBusy"
    ], capture_output=True, text=True, timeout=30,
       input=json.dumps({"timeMin": time_min, "timeMax": time_max, "items": [{"id": "primary"}]}))
    try:
        return json.loads(r.stdout).get("calendars", {}).get("primary", {}).get("busy", [])
    except:
        return []

def find_free_slot(token, person_slots, start_date, duration_min=30):
    """
    Find free slot avoiding:
    1. Calendar busy slots
    2. Already-scheduled slots for this person (in person_slots set)
    """
    day = start_date
    tz_offset = "-03:00"
    
    while True:
        if day.weekday() >= 5:
            day += timedelta(days=1)
            continue
        
        calendar_busy = get_calendar_busy(token, day)
        
        for h in range(9, 17):
            for m in [0, 30]:
                slot_start = datetime(day.year, day.month, day.day, h, m)
                slot_end = slot_start + timedelta(minutes=duration_min)
                s_iso = slot_start.isoformat() + tz_offset
                e_iso = slot_end.isoformat() + tz_offset
                
                # Check calendar conflicts
                conflict = False
                for b in calendar_busy:
                    if b.get("start","") < e_iso and b.get("end","") > s_iso:
                        conflict = True
                        break
                
                # Check already-scheduled conflicts for this person
                if not conflict:
                    for ps in person_slots:
                        if ps[0] < e_iso and ps[1] > s_iso:
                            conflict = True
                            break
                
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
        "conferenceData": {
            "createRequest": {
                "requestId": f"falai-{datetime.now().timestamp()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }
    }
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1&sendUpdates=all",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(event)
    ], capture_output=True, text=True, timeout=30)
    data = json.loads(r.stdout)
    return data.get("htmlLink") if "id" in data else None

def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    
    pairs = conn.execute("""
        SELECT 
            s.id as lider_id, s.name as lider_nome, s.email as lider_email,
            e.id as colab_id, e.name as colab_nome, e.email as colab_email,
            j.name as cargo
        FROM employees e
        JOIN employees s ON e.supervisor_id = s.id
        JOIN jobs j ON e.job_id = j.id
        WHERE e.is_active = 1
        ORDER BY s.name, e.name
    """).fetchall()
    conn.close()
    
    print(f"Pares: {len(pairs)}")
    
    token = get_token()
    now = date.today()
    
    # Dicionario: email -> set de slots (start, end)
    person_slots = {}
    
    count_1x1 = 0
    count_avaliacao = 0
    
    for pair in pairs:
        lider_email = pair["lider_email"]
        colab_email = pair["colab_email"]
        
        # Garantir que ambos tem slot tracker
        if lider_email not in person_slots:
            person_slots[lider_email] = set()
        if colab_email not in person_slots:
            person_slots[colab_email] = set()
        
        all_slots = person_slots[lider_email] | person_slots[colab_email]
        
        # 1x1
        start, end = find_free_slot(token, all_slots, now + timedelta(days=count_1x1 % 30), 30)
        
        desc_1x1 = f"""1x1: {pair['lider_nome']} & {pair['colab_nome']}

Pauta: {pair['colab_nome']} — {pair['cargo']}

Para registrar este 1x1, chame a Falai no Slack:
👉 https://app.slack.com/client/THLSB1VM4/U08MB56BPG8
Envie: "@Falai iniciar 1x1 com {pair['colab_nome']}"

by Falai — CondoConta People"""
        
        create_event(token,
            f"1x1: {pair['lider_nome']} ↔ {pair['colab_nome']}",
            desc_1x1, start, end,
            [lider_email, colab_email])
        
        # Registrar slot para AMBOS
        person_slots[lider_email].add((start, end))
        person_slots[colab_email].add((start, end))
        count_1x1 += 1
        
        # Avaliacao
        all_slots = person_slots[lider_email] | person_slots[colab_email]
        start_a, end_a = find_free_slot(token, all_slots, now + timedelta(days=count_avaliacao + 180), 45)
        
        desc_aval = f"""Avaliacao Semestral: {pair['colab_nome']}

Cargo: {pair['cargo']}
Lider: {pair['lider_nome']}

Para iniciar a avaliacao, chame a Falai no Slack:
👉 https://app.slack.com/client/THLSB1VM4/U08MB56BPG8
Envie: "@Falai iniciar avaliacao de {pair['colab_nome']}"

by Falai — CondoConta People"""
        
        create_event(token,
            f"Avaliacao: {pair['colab_nome']} ({pair['cargo']})",
            desc_aval, start_a, end_a,
            [lider_email, colab_email])
        
        person_slots[lider_email].add((start_a, end_a))
        person_slots[colab_email].add((start_a, end_a))
        count_avaliacao += 1
        
        if count_1x1 % 10 == 0:
            print(f"  {count_1x1}/{len(pairs)} 1x1, {count_avaliacao} aval...")
            token = refresh_token()
    
    print(f"✅ {count_1x1} 1x1, {count_avaliacao} avaliacoes — zero conflitos")

if __name__ == "__main__":
    main()