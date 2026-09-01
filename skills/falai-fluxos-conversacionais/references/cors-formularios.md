# CORS — Formulários HTML (Browser → API)

**Problema (21/08/2026):** formulários HTML hospedados em `static-server.aiexpert-condoconta.info` fazem `fetch()` cross-origin para `webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc`. Headers custom (`X-Service-Account-Token`, `auth`) disparam preflight OPTIONS. O ForwardAuth redireciona para login → navegador aborta com `ERR_FAILED`.

## Mecanismo de falha
1. `fetch()` com `Content-Type: application/json` + headers customizados
2. Navegador dispara **preflight OPTIONS**
3. ForwardAuth do proxy vê requisição sem sessão → **302 redirect para login**
4. `Redirect is not allowed for a preflight request` → **ERR_FAILED**

## Tentativas e resultados (testados empiricamente)

| Abordagem | Resultado |
|---|---|
| `application/x-www-form-urlencoded` sem auth headers | 401 Unauthorized |
| Auth no body como `URLSearchParams` + `form-urlencoded` | API rejeita: `Input should be a valid dictionary` |
| Auth no body + `application/json` (mesma origem?) | Browsers não veem mesma origem → preflight |
| `Content-Type: application/x-www-form-urlencoded` com auth headers | Headers custom → preflight → 302 |
| OPTIONS no webhook-proxy | HTTP 405, sem CORS headers |
| Destino direto (`condopower-api.aiexpert-condoconta.info`) | Timeout do container (inacessível) |

## ⚠️ Conclusão (21/08/2026)

**NENHUMA solução client-side funciona.** A API espera JSON, mas JSON + headers custom cross-origin = preflight = 302 = ERR_FAILED. `form-urlencoded` não dispara preflight mas a API rejeita.

## Soluções necessárias (server-side)

### 1. Proxy no mesmo domínio (recomendado)
Static-server roteia `/api/rpc` → `condopower-api` via Traefik interno.
Mesmo domínio = zero preflight. Navegador vê `fetch('/api/rpc')`.

### 2. CORS + pular auth em preflight
- Adicionar middleware CORS na `condopower-api`
- Traefik/ForwardAuth pular autenticação em OPTIONS

### Status
Nenhuma solução implementada. Formulários HTML (pulse, avaliação) NÃO funcionam no navegador.