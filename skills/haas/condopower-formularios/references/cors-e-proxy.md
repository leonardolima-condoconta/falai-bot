# CORS / preflight nos formulários — investigação completa e solução

## O problema

Formulários HTML publicados em `static-server.aiexpert-condoconta.info` precisavam gravar
na condopower-api. Todo `fetch` cross-origin com `Content-Type: application/json` dispara
um **preflight OPTIONS** que o browser manda ANTES do POST.

O gateway/Traefik (ForwardAuth) vê o OPTIONS sem sessão e redireciona pra login (302).
Redirect em preflight é fatal: o browser aborta com
`Redirect is not allowed for a preflight request → ERR_FAILED`.

## O que foi testado (na ordem) e por que falhou

| Tentativa | Resultado | Motivo |
|---|---|---|
| `fetch` → `webhook-proxy.../webhooks/condopower-api/rpc` com JSON + auth headers | ❌ preflight 302 | cross-origin + headers custom = preflight |
| `form-urlencoded` + auth no body | ❌ 400 | API espera JSON, não form-urlencoded |
| auth no body (sem headers custom) | ❌ 400 | mesmo problema — API não converte |
| `condopower-api:8000/rpc` (http/https) | ❌ timeout | container não alcança rede interna |
| `condopower-api.aiexpert-condoconta.info/rpc` direto | ❌ timeout do container | mesmo — só o navegador alcança |
| **proxy same-domain `/proxy/condopower-rpc`** | ✅ FUNCIONA | mesmo domínio = sem preflight |

## A solução

O static-server expõe `https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc`
que encaminha internamente para a condopower-api. Pro browser é o MESMO domínio do formulário,
então não há preflight nem CORS.

```javascript
fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc', {
  method:'POST',
  headers:{'Content-Type':'application/json'},   // sem tokens
  body:JSON.stringify({method:'form.pulse', params:data})
})
```

O proxy injeta `X-Service-Account-Token` e `auth` server-side — **os tokens nunca vão no JS**
(o usuário pediu explicitamente para remover de todos os headers).

## Nota sobre o container

O container Python (Falai) NÃO alcança `condopower-api.aiexpert-condoconta.info` (timeout)
nem o webhook-proxy para `/rpc` (404 do gateway). Por isso:
- O `access.verify` usado para descobrir `colaborador_id` é feito **client-side** no navegador.
- O Python só faz o que funciona do container: ler o `.env`, ler os JSONs locais, gerar o HTML
  e publicar via webhook do static-server (esse endpoint o container alcança).

## Sintoma clássico do erro 400

`form.autoavaliacao` retornando `400 MISSING_PARAMS` / "Parâmetros inválidos ou ausentes"
quase sempre é `colaborador_id` vazio no hidden input. Se o `access.verify` (server-side no
Python) falha, `cid` sai vazio e a API rejeita. A correção é mover a resolução pro navegador.
