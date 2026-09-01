# Google Calendar — Setup e Acesso para Falai

## Pré-requisitos

- `/opt/data/google_token.json` — token OAuth (formato: access_token, refresh_token, scope, token_type, expires_in)
- `/opt/data/google_client_secret.json` — credenciais OAuth (contém client_id, client_secret)
- Pacotes Google instalados em virtualenv: `/opt/data/.venv/`

## Instalação (se pacotes ausentes)

```bash
python3 -m venv /opt/data/.venv
/opt/data/.venv/bin/pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pytz
```

Usar SEMPRE `/opt/data/.venv/bin/python3` — o python3 do sistema é externally-managed (PEP 668).

## Autenticação

O `google_token.json` atual já contém `client_id` e `client_secret` — NÃO é mais necessário fazer merge com `google_client_secret.json`.

**Padrão direto (funciona hoje):**

```python
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

with open('/opt/data/google_token.json') as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['access_token'],
    refresh_token=token_data['refresh_token'],
    token_uri='https://oauth2.googleapis.com/token',
    client_id=token_data['client_id'],
    client_secret=token_data['client_secret']
)

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open('/opt/data/google_token.json', 'w') as f:
        json.dump(json.loads(creds.to_json()), f)
```

> **PITFALL histórico (resolvido):** Anteriormente o token NÃO continha `client_id`/`client_secret` e exigia merge manual com `google_client_secret.json`. Se um dia o token voltar ao formato simplificado, verificar as chaves disponíveis com `print(token_data.keys())` e fazer o merge se necessário.

## Listar eventos do Calendar

```python
from googleapiclient.discovery import build
from datetime import datetime, timezone, timedelta
import pytz

service = build('calendar', 'v3', credentials=creds)
sao_paulo = pytz.timezone('America/Sao_Paulo')

now = datetime.now(timezone.utc)
end = now + timedelta(days=14)

events = service.events().list(
    calendarId='primary',
    timeMin=now.isoformat(),
    timeMax=end.isoformat(),
    singleEvents=True,
    maxResults=50,
    orderBy='startTime'
).execute()
```

## Verificar disponibilidade (Free/Busy)

Para achar horários livres entre duas ou mais pessoas sem precisar listar eventos completos:

```python
service = build('calendar', 'v3', credentials=creds)

fb_request = {
    "timeMin": '2026-08-14T08:00:00-03:00',
    "timeMax": '2026-08-14T19:00:00-03:00',
    "items": [
        {"id": "rodrigo.catarcione@condoconta.com.br"},
        {"id": "leonardo.lima@condoconta.com.br"},
    ]
}

result = service.freebusy().query(body=fb_request).execute()

for email, cal in result['calendars'].items():
    print(f"\n{email}:")
    for slot in cal.get('busy', []):
        print(f"  {slot['start']} → {slot['end']}")
```

Retorna apenas os blocos ocupados — todo o resto é livre. Ideal para cruzar agendas de múltiplas pessoas.

## Criar evento com convidados

```python
event = {
    'summary': 'Título da reunião',
    'description': 'Pauta...',
    'start': {
        'dateTime': '2026-08-14T14:00:00-03:00',
        'timeZone': 'America/Sao_Paulo',
    },
    'end': {
        'dateTime': '2026-08-14T15:00:00-03:00',
        'timeZone': 'America/Sao_Paulo',
    },
    'attendees': [
        {'email': 'rodrigo.catarcione@condoconta.com.br'},
        {'email': 'leonardo.lima@condoconta.com.br'},
    ],
    'conferenceData': {
        'createRequest': {
            'requestId': 'some-unique-id',
            'conferenceSolutionKey': {'type': 'hangoutsMeet'},
        }
    },
}

event = service.events().insert(
    calendarId='primary',
    body=event,
    conferenceDataVersion=1,
    sendUpdates='all'
).execute()
```

## Fuso horário

Sempre usar `America/Sao_Paulo` (GMT-3). Eventos precisam de `dateTime` com offset explícito (`-03:00`) e `timeZone` setado.

## Calendário usado

O token atual acessa o calendário `primary` da conta autenticada. 
Verificar qual conta está ativa: `service.calendarList().get(calendarId='primary').execute()['summary']`.