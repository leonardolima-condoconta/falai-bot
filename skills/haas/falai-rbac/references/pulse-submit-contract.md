# pulse.submit — Contrato empírico (19/08/2026)

Testado com curl contra produção. O que a API REALMENTE exige:

## Requisição válida

```json
POST /rpc
{
  "method": "pulse.submit",
  "params": {
    "respondent_email": "amanda.almeida@condoconta.com.br",
    "sentimento_pessoal": "Bem",
    "relacao_lideranca": "Boa",
    "sentimento_time": "Muito Bom",
    "ia_ganho_tempo": "Ajudou muito",
    "ia_qualidade": "Melhorou moderadamente",
    "enps": 9,
    "motivo_nota": "Time engajado"
  }
}
```

## Campos obrigatórios

`respondent_email` é MANDATÓRIO. Sem ele:
```json
{"ok":false,"error":{"code":"MISSING_PARAMS","fields":[{"field":"respondent_email","reason":"Field required"}]}}
```

Os demais campos são opcionais (API não recusa se faltar `sentimento_pessoal`, etc.).

## O que NÃO funciona

- `application/x-www-form-urlencoded` → rejeitado: `Input should be a valid dictionary`
- JSON direto sem wrapper `{"method":"...","params":{...}}` → rejeitado: `Field required [method]`
- Sem `respondent_email` → `MISSING_PARAMS`

## Implicação para formulários HTML

O formulário no navegador precisa de:
1. Campo `respondent_email` (obrigatório)
2. Enviar como JSON com wrapper `method` + `params`
3. Headers `X-Service-Account-Token` e `auth`

⚠️ O envio cross-origin via `fetch()` com `Content-Type: application/json` + headers custom dispara preflight CORS. O proxy ForwardAuth redireciona OPTIONS para login → navegador aborta. Sem CORS na API ou proxy no mesmo domínio, o formulário não funciona no navegador.