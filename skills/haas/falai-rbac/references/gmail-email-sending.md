# Envio de e-mail pelo Gmail (people@condoconta.com.br)

Conta OAuth autenticada e funcionando no container da Falai: **people@condoconta.com.br**.
Verificado em 27/08/2026 — `getProfile` retorna `people@condoconta.com.br`, caixa ativa.

## Fatos do ambiente (container Falai)

- **Token OAuth:** `/opt/data/google_token.json` — NÃO é `~/.hermes/google_token.json`
  (o `$HOME` real é `/opt/data/home`, mas o token fica em `/opt/data` direto).
- **Client secret:** `/opt/data/google_client_secret.json`
- **Python com as libs Google:** `/opt/data/.venv/bin/python`
  (o `python3` do sistema NÃO tem `googleapiclient` — `ModuleNotFoundError: No module named 'google'`).
- **`setup.py --check` está QUEBRADO** neste container: falha com
  `ModuleNotFoundError: No module named 'hermes_constants'`. NÃO confie nele para
  validar auth — valide direto via Gmail API (ver abaixo).

## Pitfall — `expiry` vem como int (expires_in, ex. 3599)

`Credentials.from_authorized_user_info` quebra com
`AttributeError: 'int' object has no attribute 'rstrip'` se o `expiry` for int.
Converter antes de construir as credenciais:

```python
import json, datetime
data = json.load(open('/opt/data/google_token.json'))
if isinstance(data.get('expiry'), int) and data['expiry'] < 100000:
    from datetime import timezone
    data['expiry'] = (datetime.datetime.now(timezone.utc)
                      + datetime.timedelta(seconds=data['expiry'])).isoformat()
```

## Verificar autenticação (sempre antes de operar)

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

data = json.load(open('/opt/data/google_token.json'))
# ... aplica o fix de expiry acima ...
creds = Credentials.from_authorized_user_info(data)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
gmail = build('gmail', 'v1', credentials=creds)
print(gmail.users().getProfile(userId='me').execute()['emailAddress'])
# -> people@condoconta.com.br
```

## Enviar e-mail

```python
import base64
from email.mime.text import MIMEText

def send(to, subject, body, html=False):
    msg = MIMEText(body, 'html' if html else 'plain', 'utf-8')
    msg['to'] = to
    msg['subject'] = subject
    msg['from'] = 'people@condoconta.com.br'
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

Para HTML, `MIMEText(body, 'html', 'utf-8')`. Para anexos, usar `MIMEMultipart`.

## Regras de uso

- **Confirmar com o usuário o conteúdo antes de enviar** (mostrar draft e aguardar aprovação).
- **RBAC:** Gmail é levels 3+ (team_people/admin/superadmin). Levels 1-2 (condopower/condo_leader) NÃO têm acesso.
- Remetente SEMPRE `people@condoconta.com.br`.
