---
name: condopower-api-routing
description: Endpoints e diagnóstico de falhas da condopower-api.
version: 1.1.0
---

# condopower-api routing — endpoints e diagnóstico de falhas

## Dois endpoints, propósitos diferentes

A condopower-api tem duas portas de entrada. A escolha NÃO é intercambiável:

| Uso | Endpoint | Path |
|---|---|---|
| **Chamadas do agente (servidor)** — `access.verify`, `form.*.get`, `pulse.*`, `celebrations.*`, `roster.sync` | `https://webhook-proxy.condoconta.com.br` | `/webhooks/condopower-api` |
| **Submissão de formulários (navegador)** — `form.pulse`, `form.autoavaliacao`, `form.avaliacao_lider` | `https://condopower-api.aiexpert-condoconta.info` | `/rpc` |

### 🔑 Autenticação (Obrigatória)
Para chamadas via Proxy ou API, use estes headers exatos. **Não use `Authorization: Bearer` para a API Condopower (causa 401)**:

| Header | Origem no `.env` |
|---|---|
| `X-Service-Account-Token` | `CONDOPOWER_SA_TOKEN` |
| `auth` | `CONDOPOWER_AUTH` |

⚠️ **O container da Falai NÃO alcança a URL direta** — timeout de 60s. Para chamadas de dentro do agente, use SEMPRE o webhook-proxy. O endpoint direto é para os `fetch()` nos formulários HTML que rodam no navegador do colaborador.

⚠️ **O proxy monta o path final.** O webhook-proxy em `/webhooks/condopower-api` acrescenta `/rpc` ao encaminhar para o backend (confirmado 26/08/2026: `x-gateway-forwarded-to: https://condopower-api.aiexpert-condoconta.info/rpc`). **NUNCA inclua `/rpc` no path do proxy** — montar `/webhooks/condopower-api/rpc` causa `404` ("does not accept a subpath"). O `/rpc` é responsabilidade do proxy, não sua.

## Diagnóstico rápido de falha

Quando uma chamada ao webhook-proxy falhar, **olhe os headers de resposta** antes de concluir.

### 401 Unauthorized (sem headers de auth)
```json
{"detail": "Unauthorized."}
```
→ Proxy funcionando, faltam headers de auth. Não é outage.

### 404 Not Found — JSON (proxy, path com `/rpc`)
```json
{"detail": "Webhook route 'condopower-api' does not accept a subpath."}
```
→ Você montou `/webhooks/condopower-api/rpc` na mão. O proxy trata `/rpc` como subpath da rota `condopower-api`, que não aceita subpaths. **Solução:** remova o `/rpc` do path — use só `/webhooks/condopower-api`.

### 404 Not Found — HTML (COM headers de auth)
Resposta é HTML do nginx. Olhe os headers:
```
x-gateway-forwarded-to: https://condopower-api.aiexpert-condoconta.info/rpc
x-envoy-upstream-service-time: 55
```
→ Proxy encaminhou corretamente (55ms round-trip), mas **backend está fora do ar** — a aplicação Python (uvicorn/gunicorn) caiu e o nginx na frente responde 404. **Não é problema no proxy — a API precisa ser reiniciada.**

### Timeout (60s)
→ Container não alcança a rede da API. Não tente a URL direta de dentro do agente.

### 405 Not Allowed
→ Backend recebeu requisição sem `/rpc` (ex.: o proxy encaminhou para a raiz `/` em vez de `/rpc`). Confirme no header `x-gateway-forwarded-to`.

## Fallback durante outage

- Perguntas respondíveis com Confluence (cargos, trilhas) → prossiga, avisando da falha.
- Perguntas que exigem RBAC (formulários, avaliações) → pare e peça para tentar depois.
- Fluxo completo em `falai-rbac` → `references/condopower-api-outage-fallback.md`.

## Ver também

- `condopower-api` — catálogo de métodos e contratos
- `falai-rbac` — regras de identificação e níveis de acesso
