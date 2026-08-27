---
name: google-oauth-onboarding
description: Onboarding Google Workspace para agentes HaaS. Credenciais JÁ estão no .env. O agente só gera o link OAuth e pede autorização.
version: 2.0.0
trusted: true
---

# Google OAuth Onboarding — HaaS CondoConta

Conecta Gmail, Calendar e Drive via OAuth. `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` JÁ estão no `/opt/data/.env` — você NUNCA pede credenciais ao admin.

## 🚨 REGRA #0 (ABSOLUTA)

**NUNCA peça ao admin:**
- ❌ "qual o client_id?"
- ❌ "qual o client_secret?"
- ❌ "crie um projeto no GCP"
- ❌ "preciso acessar o Infisical"

**Você já tem tudo no `/opt/data/.env`:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (padrão: `http://localhost:8080/`)

Sua ÚNICA função é gerar a URL OAuth e entregar pro admin clicar.

## Quando usar

- Admin diz: "conecta google", "oauth", "acessar email", "configurar calendar"
- Agente detecta que `auth.json` não existe

## Fluxo (3 passos)

### 1. Carregar credenciais (SILENCIOSO — não informe o admin)

```bash
source /opt/data/.env 2>/dev/null || export $(grep -v '^#' /opt/data/.env | xargs)
```

### 2. Gerar URL OAuth

```python
import os, secrets, urllib.parse, webbrowser

# Credenciais JÁ estão no .env — não pedir!
client_id = os.environ['GOOGLE_CLIENT_ID']
redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/')

state = secrets.token_urlsafe(32)
params = {
    'client_id': client_id,
    'redirect_uri': redirect_uri,
    'response_type': 'code',
    'scope': 'https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/drive.file https://www.googleapis.com/auth/spreadsheets',
    'access_type': 'offline',
    'prompt': 'consent',
    'state': state
}
auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
print(auth_url)
```

### 3. Entregar o link

> "🔗 Abra este link e autorize com sua conta CondoConta:
> {auth_url}
> 
> Depois me avise que eu finalizo."

**Só isso.** Nada de explicar o que é OAuth, nada de mencionar client_secret.

## Finalizar (após admin autorizar)

O callback vem na porta 8080. Trocar o código por tokens:

```python
import requests

token_resp = requests.post('https://oauth2.googleapis.com/token', data={
    'code': code_from_callback,
    'client_id': os.environ['GOOGLE_CLIENT_ID'],
    'client_secret': os.environ['GOOGLE_CLIENT_SECRET'],
    'redirect_uri': os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8080/'),
    'grant_type': 'authorization_code'
})
tokens = token_resp.json()
# Salvar tokens em auth.json
```

Confirmar: `"✅ Google conectado! Gmail, Calendar e Drive prontos."`

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Porta 8080 ocupada | `fuser -k 8080/tcp` |
| Token expirado | Re-executar onboarding |
| redirect_uri_mismatch | URI padrão: `http://localhost:8080/` |

## O que NUNCA fazer

- ❌ Pedir client_id ou client_secret — você JÁ TEM
- ❌ Mencionar Infisical — está descontinuado
- ❌ Dizer "não tenho credenciais" — leia /opt/data/.env
- ❌ Explicar OAuth — só passe o link
