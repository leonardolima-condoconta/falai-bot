# Arquitetura de proxy e CORS

## Problema original
Fetch cross-origin com `Content-Type: application/json` + headers custom (`X-Service-Account-Token`, `auth`) → navegador envia preflight OPTIONS → proxy/Traefik ForwardAuth redireciona para login (302) → navegador aborta: `Redirect is not allowed for a preflight request → ERR_FAILED`.

## Solução definitiva
Proxy mesmo-domínio no static-server:
```
/proxy/condopower-rpc → proxy_pass → condopower-api (interno)
```

Navegador faz fetch para `https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc` → mesmo domínio do formulário → zero CORS → zero preflight.

## Iterações testadas (histórico)

1. `form-urlencoded` + auth no body → API rejeita (espera JSON)
2. `condopower-api.aiexpert-condoconta.info/rpc` direto → timeout do container (sem conectividade)
3. `condopower-api:8000/rpc` → inacessível do navegador
4. `webhook-proxy` → CORS preflight bloqueado
5. Proxy mesmo-domínio → ✅ funciona, tokens obrigatórios