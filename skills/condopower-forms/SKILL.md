---
name: condopower-forms
description: "Padrão de forms People: proxy CORS, cookies, submit."
version: 1.0.0
---

# CondoPower Forms — Padrão Unificado

## Endpoint de submit

Todos os formulários fazem submit via proxy no mesmo domínio para evitar CORS/preflight:

```
https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc
```

Headers: `Content-Type: application/json` + `X-Service-Account-Token` + `auth`.
Os tokens VÃO no navegador (validado empiricamente: o formulário Pulse que funciona envia os dois
tokens no header; removê-los da autoavaliação causou 400). Não confiar em "proxy injeta internamente".

## Padrão de cookie

| Formulário | Cookie | max-age | Comportamento |
|---|---|---|---|
| Pulse | `pulses_respondido=1` | 864000 (10d) | Tela de agradecimento |
| Autoavaliação | `autoavaliacao_respondida=1` | 864000 (10d) | Tela de agradecimento |
| Líder | `avaliacao_lider_feitos=["uuid"]` | 864000 (10d) | Remove do dropdown; agradecimento só ao zerar |

## Arquivos geradores

| Formulário | Script | Status |
|---|---|---|
| Pulse | `form-pulse.html` (estático) | ✅ |
| Autoavaliação | `gerar_form_avaliacao.py` | ✅ |
| Líder | `gerar_form_lider.py` | ✅ |
| 1x1 consolidado | `gerar_form_1x1.py` | ✅ |
| PDI | — | ❌ |
| 9box | — | ❌ |

## Comunicação Slack

- Links NUNCA dentro de asteriscos (`*`) — quebra formatação
- Template Pulse: mês/ano dinâmico, VPN warning, período calculado
- Assinar: `*by Falai — People*`

## colaborador_id vem de access.verify

Autoavaliação, líder, 1x1, PDI e 9box EXIGEM `colaborador_id` (UUID do Convenia). Esse id vem de
`access.verify` no gerador Python — se a API estiver fora do ar no container, o campo sai `value=""`
e a API devolve `400 MISSING_PARAMS` ("Parâmetros inválidos ou ausentes"). **`form.pulse` é a exceção**
(anônimo, não exige id) — por isso Pulses funciona mesmo quando a identidade está fora do ar.

## Ciclo de vida

Cookie expira em 10 dias. Líder armazena array JSON de UUIDs.