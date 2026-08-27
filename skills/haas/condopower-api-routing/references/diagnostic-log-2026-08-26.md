# Diagnóstico de outage — 26/08/2026

## Contexto

`access.verify` falhando para o Catar (Slack ID `U0AFGRGC80P`). Falai tentou 3x e as 3 falharam.

## Testes realizados e resultados

### Teste 1: webhook-proxy COM headers reais
```
URL: https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc
Método: POST
Headers: X-Service-Account-Token (SA token), auth (UUID)
Body: {"method":"access.verify","params":{"identifier":"U0APYGTD8K1"}}
```
**Resultado:** HTTP 404 — HTML do nginx
**Headers de resposta:**
```
x-gateway-forwarded-to: https://condopower-api.aiexpert-condoconta.info/rpc
x-envoy-upstream-service-time: 55
server: istio-envoy
```
**Interpretação:** Proxy encaminhou em 55ms, mas a aplicação Python atrás do nginx está fora do ar.

### Teste 2: URL direta
```
URL: https://condopower-api.aiexpert-condoconta.info/rpc
```
**Resultado:** Timeout (60s)
**Interpretação:** Container não alcança essa rede — já documentado.

### Teste 3: webhook-proxy SEM headers
```
URL: https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc
Headers: apenas Content-Type
```
**Resultado:** HTTP 401 — `{"detail":"Unauthorized."}`
**Interpretação:** Proxy está vivo e autenticando. Confirma que o problema é no backend, não no proxy.

### Teste 4: webhook-proxy SEM `/rpc`
```
URL: https://webhook-proxy.condoconta.com.br/webhooks/condopower-api
```
**Resultado:** HTTP 405 — `Method GET not allowed` (GET) / `405 Not Allowed` (POST com auth)
**x-gateway-forwarded-to:** `https://condopower-api.aiexpert-condoconta.info/` (sem `/rpc`)
**Interpretação:** Path `/rpc` é obrigatório.

### Teste 5: curl de saúde
```
curl https://webhook-proxy.condoconta.com.br/ → 404 (normal, root sem path)
curl https://condopower-api.aiexpert-condoconta.info/ → timeout (container não alcança)
```

## Conclusão

A aplicação Python (uvicorn/gunicorn/starlette) da `condopower-api` caiu no servidor onde roda. O nginx está de pé (responde em 55ms) mas retorna 404 porque não encontra o backend. É necessário restart da aplicação no servidor `condopower-api.aiexpert-condoconta.info`.

## Método de diagnóstico (genérico)

1. Testar webhook-proxy **sem** headers → 401 = proxy OK
2. Testar webhook-proxy **com** headers → ler `x-gateway-forwarded-to`
   - Se `x-envoy-upstream-service-time` está presente e baixo → proxy encaminhou, backend respondeu
   - Se resposta é HTML 404 do nginx → backend fora do ar
   - Se resposta é JSON com envelope `{"ok":...}` → API funcionando