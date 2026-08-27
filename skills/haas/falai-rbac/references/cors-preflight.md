# CORS / Preflight — Resultado empírico (23/08/2026)

## Problema

Formulários HTML em `static-server.aiexpert-condoconta.info` fazem `fetch()` para
`condopower-api.aiexpert-condoconta.info/rpc` com:
- `Content-Type: application/json`
- Headers custom: `X-Service-Account-Token`, `auth`

Navegador detecta cross-origin → manda **preflight OPTIONS** antes do POST.

## Resultados

### OPTIONS via webhook-proxy
```
HTTP/2 405 Method Not Allowed
Allow: PUT, GET, POST, PATCH
{"detail":"Method Not Allowed"}
```
- istio-envoy responde 405
- Zero headers CORS (sem `Access-Control-Allow-Origin`)
- Navegador aborta: `Redirect is not allowed for a preflight request → ERR_FAILED`

### POST via curl (funciona)
```
HTTP/2 200
x-gateway-forwarded-to: https://condopower-api.aiexpert-condoconta.info/rpc
```
- POST vai, mas resposta também **não traz headers CORS**
- Mesmo se o preflight passasse, o navegador descartaria a resposta

### URL direta (condopower-api.aiexpert-condoconta.info/rpc)
- Container da Falai **NÃO alcança** essa URL (timeout)
- Usar SEMPRE `webhook-proxy` para chamadas internas (curl/Python)
- A URL direta é usada apenas no `fetch()` do navegador (HTML estático)

## O que NÃO funciona

| Tentativa | Resultado |
|---|---|
| `form-urlencoded` + headers custom | Dispara preflight mesmo assim |
| Auth no body (`URLSearchParams`) | API rejeita: `Input should be a valid dictionary` |
| `Content-Type: application/json` sem headers | API rejeita por falta de auth |
| `application/x-www-form-urlencoded` + auth no body | API rejeita: `Input should be a valid dictionary` |

## Soluções possíveis (nenhuma implementada)

1. **Middleware CORS na `condopower-api`** — `Access-Control-Allow-Origin: *` — mais rápido
2. **Proxy no mesmo domínio** — static-server roteia `/api/rpc` → condopower-api (zero CORS)
3. **Submeter via `<form>` nativo** — sem fetch, sem preflight — mas API espera JSON

## Status

❌ NÃO RESOLVIDO. Nenhum formulário HTML funciona em navegador até que CORS seja resolvido.

Chamadas internas (curl/Python) funcionam via webhook-proxy. O problema é só no navegador.

## Dual URL strategy

| Contexto | URL |
|---|---|
| Python/curl (container) | `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc` |
| fetch() no HTML (navegador) | `https://condopower-api.aiexpert-condoconta.info/rpc` |