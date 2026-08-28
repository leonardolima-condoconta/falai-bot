---
name: condopower-api-routing
description: Endpoints, proxy, diagnóstico e padrão /proxy/condopower-rpc (mesmo domínio, zero CORS, sem tokens no navegador).
version: 2.0.0
---

# condopower-api routing — endpoints, proxy e diagnóstico

## Arquitetura atual (Agosto/2026)

```
NAVEGADOR (colaborador)
  │
  ├─ POST /proxy/condopower-rpc  ──→ static-server ──→ condopower-api (interno)
  │   └─ headers: Content-Type: application/json  (zero tokens no navegador)
  │   └─ usado para: TODOS os form.* e access.verify nos formulários HTML

AGENTE FALAI (container)
  │
  └─ POST /webhooks/condopower-api  ──→ webhook-proxy ──→ condopower-api
      └─ headers: X-Service-Account-Token + auth  (obrigatórios)
      └─ usado para: access.verify, form.*.get, pulse.*, celebrations.*, roster.sync
```

| Contexto | Endpoint | Auth | Quem usa |
|---|---|---|---|
| Navegador | `https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc` | Proxy resolve server-side | Formulários HTML |
| Servidor | `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api` | `X-Service-Account-Token` + `auth` | Falai (Python), crons |

## Regras críticas

### 1. NUNCA inclua `/rpc` no path do webhook-proxy
O proxy monta `/rpc` automaticamente ao encaminhar. Usar `/webhooks/condopower-api/rpc` manualmente causa:
```
{"detail": "Webhook route 'condopower-api' does not accept a subpath."}
```
Correto: `/webhooks/condopower-api` (sem `/rpc`).

### 2. Formulários HTML NUNCA expõem tokens
O fetch no navegador usa apenas `Content-Type: application/json`. O static-server injeta os tokens server-side ao fazer o proxy reverso para a condopower-api. Padrão correto:
```javascript
fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc',{
  method:'POST',
  headers:{'Content-Type':'application/json'},  // só isso
  body:JSON.stringify({method:'form.autoavaliacao',params:{...}})
})
```

### 3. Container NÃO alcança a URL direta
`https://condopower-api.aiexpert-condoconta.info` → timeout (60s+). Use sempre o webhook-proxy para chamadas server-side. Credenciais em `/opt/data/.env`:
```bash
grep -E 'CONDOPOWER_SA_TOKEN|CONDOPOWER_AUTH' /opt/data/.env
```
Headers obrigatórios: `X-Service-Account-Token` + `auth`. Se a URL direta der timeout, **carregue esta skill imediatamente** — não insista com retries na URL direta.

### 4. access.verify nos formulários é client-side
Os geradores Python (`gerar_form_avaliacao.py`, `gerar_form_lider.py`) não chamam `access.verify` — embutem o email no HTML e o navegador resolve o UUID via `/proxy/condopower-rpc` no carregamento da página. Isso é necessário porque o container não alcança a condopower-api.

### 5. Cookies de submissão têm max-age=864000 (10 dias)
`autoavaliacao_respondida=1`, `pulses_respondido=1`, `avaliacao_lider_feitos=[...]` — todos com `max-age=864000`. O formulário do líder usa cookie JSON-encoded para rastrear múltiplos liderados avaliados.

### 6. Pulses para não-People — use `form.pulse.get` com e-mail People + área

Quando um líder (nível 2) pergunta quantas pessoas do time responderam à Pulses:
- `pulse.round_status` → **403 NOT_PEOPLE** (só nível 3+)
- `form.pulse.get` com o e-mail do líder → **lista vazia** (anonimato)
- ✅ Use `form.pulse.get` com `requester_email` de alguém do time People (ex: `rodrigo.catarcione@condoconta.com.br`) e o filtro `area` do departamento

Isso retorna as respostas anônimas da área sem quebrar o anonimato individual. NUNCA use o e-mail do líder — retorna lista vazia. Cuide com texto livre em times pequenos: o conteúdo pode identificar o autor indiretamente.

## Diagnóstico rápido

| Sintoma | Causa | Ação |
|---|---|---|
| 401 `Unauthorized` | Faltam headers de auth | Adicionar `X-Service-Account-Token` + `auth` |
| 404 "does not accept a subpath" | `/rpc` no path manual | Remover `/rpc` — usar só `/webhooks/condopower-api` |
| 404 HTML do nginx (COM auth) | Backend caído (uvicorn/gunicorn) | Reiniciar aplicação no servidor |
| Timeout 60s | Container tentou URL direta | Usar webhook-proxy |
| HTTP 000 no static-server | Rota `/proxy/condopower-rpc` não configurada | Configurar proxy reverso no static-server |
| 400 MISSING_PARAMS no form | `colaborador_id` vazio | access.verify não resolveu — aguardar load da página |

## Fallback durante outage

- Perguntas respondíveis com Confluence (cargos, trilhas) → prossiga, avisando da falha.
- Perguntas que exigem RBAC (formulários, avaliações) → pare e peça para tentar depois.

## Slack — links nunca em negrito

No Slack, asteriscos aplicam **negrito**. Links entre asteriscos quebram visualmente. Padrão correto:
```
📝 *Link do formulário:* https://static-server.aiexpert-condoconta.info/pesquisa-pulses
```
❌ Errado: `*Link: https://...*` (link dentro do par de asteriscos)

## Ver também

- `condopower-api` — catálogo de métodos e contratos (v2.1.0). ⚠️ Esta skill omite o webhook-proxy e os headers de auth; se a URL direta der timeout, carregue a skill `condopower-api-routing`.
- `references/container-routing-fallback.md` — caso real de timeout na URL direta e recuperação com o proxy (27/08/2026)
- `condopower-rbac` — regras de identificação e níveis de acesso (levels 1-5)
- `condopower-formularios` — CORS, proxy e padrão dos formulários HTML
- `references/pulse-for-non-people.md` — padrão de consulta Pulses para líderes via e-mail People + área (caso real 28/08/2026)