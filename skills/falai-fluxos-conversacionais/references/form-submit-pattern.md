# Padrão de Submit dos Formulários Falai

## Estado atual (21–23/08/2026)

### URL de submit
`https://condopower-api.aiexpert-condoconta.info/rpc`

**Por que URL direta, não webhook-proxy:**
- O navegador do usuário precisa alcançar a API
- `webhook-proxy.condoconta.com.br` redireciona internamente (x-gateway-forwarded-to)
- Mas o container da Falai NÃO alcança a URL direta (timeout) — usa webhook-proxy internamente
- O navegador do usuário SIM alcança a URL direta
- Por isso: Python (server-side) = webhook-proxy; HTML (client-side fetch) = URL direta

### Headers de autenticação
```javascript
headers: {
  'Content-Type': 'application/json',
  'X-Service-Account-Token': '<CONDOPOWER_SA_TOKEN>',
  'auth': '<CONDOPOWER_AUTH>'
}
```

### Estrutura do body
```json
{
  "method": "form.<tipo>",
  "params": { ... }
}
```

## Métodos atuais (v2.0.0)
- `form.pulse` — resposta de clima
- `form.autoavaliacao` — autoavaliação
- `form.avaliacao_lider` — avaliação do líder sobre liderado
- `form.1x1` — registro de 1x1
- `form.pdi` — plano de desenvolvimento
- `form.9box` — nine box

## Análise CORS (21/08/2026)

### Problema original
fetch() cross-origin com `Content-Type: application/json` + headers custom → preflight OPTIONS → ForwardAuth redireciona → `ERR_FAILED`

### Abordagens testadas
| Abordagem | Resultado |
|---|---|
| `form-urlencoded` + auth no body | API rejeita: `Input should be a valid dictionary` |
| JSON + headers custom | Preflight → 302 → abort |
| OPTIONS no webhook-proxy | HTTP/2 405 Method Not Allowed |
| POST no webhook-proxy | HTTP/2 200 (funciona) mas sem CORS headers |

### Solução pendente
Nenhuma das abordagens de contorno resolveu no lado do cliente. A solução correta é middleware CORS na `condopower-api`:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, X-Service-Account-Token, auth`

Enquanto isso, o formulário pode funcionar se o usuário estiver na mesma rede/VPN que a API.