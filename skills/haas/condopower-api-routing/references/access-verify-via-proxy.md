# access.verify via webhook-proxy — padrão funcional

> Comprovado em 31/08/2026, corrigido em 01/09/2026.
> Resposta em 0.2s vs timeout 60s na URL direta.
> ⚠️ **NUNCA incluir sa_token/auth no corpo do JSON — causa 401.** Apenas headers.

## Código Python funcional (execute_code / scripts)

```python
import json, urllib.request

SA_TOKEN = "sa_d49f..."
AUTH = "7aa7e5b1..."
URL = "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api"

def call_rpc(method, params):
    """Headers-only: X-Service-Account-Token + auth. NUNCA payload enrichment."""
    payload = json.dumps({"method": method, "params": params}).encode("utf-8")
    req = urllib.request.Request(
        URL, data=payload,
        headers={
            "X-Service-Account-Token": SA_TOKEN,
            "auth": AUTH,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

result = call_rpc("access.verify", {"identifier": "U0AFGRGC80P"})
print(f"ok: {result['ok']}, nome: {result['result']['employee']['full_name']}, level: {result['result']['level']}")
```

## Curl funcional (terminal)

```bash
TOKEN="sa_d49fca02-..."
AUTH="7aa7e5b1-..."

curl -s -X POST \
  "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api" \
  -H "Content-Type: application/json" \
  -H "X-Service-Account-Token: $TOKEN" \
  -H "auth: $AUTH" \
  -d '{"method":"access.verify","params":{"identifier":"U0AFGRGC80P"}}'
```

## Scripts de referência (padrão real em produção)

`/opt/data/scripts/pulse_report_cron.py` — usa headers-only, sem payload enrichment.
Este é o padrão canônico: `payload = json.dumps({"method": method, "params": params})` — apenas.

## Checklist de chamada

- [ ] URL: `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api` (sem `/rpc`)
- [ ] Headers: `X-Service-Account-Token` + `auth`
- [ ] Body: APENAS `{"method": "...", "params": {...}}` — NUNCA incluir `sa_token` ou `auth` no corpo
- [ ] Timeout: 15s é suficiente (resposta típica < 1s)
- [ ] Credenciais: ler de `/opt/data/.env` via `grep -E 'CONDOPOWER_SA_TOKEN|CONDOPOWER_AUTH'`

## O que NUNCA fazer

```python
# ❌ URL DIRETA — sempre timeout 60s
url = "https://condopower-api.aiexpert-condoconta.info/rpc"

# ❌ Payload enrichment — CAUSA 401
payload = {"method": "access.verify", "params": {...}, "sa_token": "...", "auth": "..."}
# ⚠️ sa_token/auth NO CORPO causam "invalid service token"

# ❌ Sem headers de auth
headers = {"Content-Type": "application/json"}
# Faltam: X-Service-Account-Token e auth

# ❌ /rpc no path do webhook-proxy
url = "https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc"
# Responde: "does not accept a subpath"
```