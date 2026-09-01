# CORS Proxy — Solução definitiva

## Problema original

Formulários em `static-server.aiexpert-condoconta.info` faziam `fetch()` cross-origin para `condopower-api.aiexpert-condoconta.info/rpc`. Com `Content-Type: application/json` + headers custom, o navegador disparava preflight OPTIONS. O Traefik ForwardAuth via requisição sem sessão e redirecionava para login (302). Resultado: `ERR_FAILED`.

## Tentativas frustradas

| Tentativa | Por que falhou |
|---|---|
| `application/x-www-form-urlencoded` sem headers | API rejeita (`Input should be a valid dictionary`) |
| Auth no body como URLSearchParams | API espera JSON, não form-urlencoded |
| `http://condopower-api:8000/rpc` | Container não alcança (timeout) |
| `https://condopower-api.aiexpert-condoconta.info/rpc` direto | Preflight → 302 → abort |
| CORS middleware na API | Não implementado no momento |

## Solução

Proxy no mesmo domínio. Static-server roteia `/proxy/condopower-rpc` → `condopower-api` internamente via rede Docker/Traefik. Zero preflight, zero CORS.

```javascript
fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ method: 'form.pulse', params: { ... } })
})
```

## Regras

- Mesmo domínio = sem preflight
- Zero tokens no navegador
- Proxy injeta `X-Service-Account-Token` e `auth` internamente