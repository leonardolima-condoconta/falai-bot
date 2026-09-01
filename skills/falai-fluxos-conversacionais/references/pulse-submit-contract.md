# Pulse Submit — Contrato Empírico

Testado em 20/08/2026 contra `webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc`.

## Requisitos

| Campo | Obrigatório | Tipo |
|---|---|---|
| `method` | ✅ | `"pulse.submit"` |
| `params` | ✅ | objeto |
| `params.respondent_email` | ✅ | string |
| `params.area` | ❌ | string (dropdown: 15 opções) |
| `params.lideranca_direta` | ❌ | string (dropdown: 26 opções) |
| `params.sentimento_pessoal` | ❌ | string "1" a "5" |
| `params.relacao_lideranca` | ❌ | string "1" a "5" |
| `params.sentimento_time` | ❌ | string "1" a "5" |
| `params.ia_ganho_tempo` | ❌ | string "1" a "5" |
| `params.ia_qualidade` | ❌ | string "1" a "5" |
| `params.enps` | ❌ | string "0" a "10" |
| `params.motivo_nota` | ❌ | string |

## Comportamento

- `respondent_email` é usado para controle de participação (evitar duplicidade) e medir adesão
- A resposta em si NÃO carrega identidade (tabela separada)
- Sem `respondent_email` → `{"ok":false,"error":{"code":"MISSING_PARAMS","fields":[{"field":"respondent_email","reason":"Field required"}]}}`
- Sem rodada aberta → `409 NO_OPEN_ROUND`
- Segunda resposta mesma rodada → `409 ALREADY_ANSWERED`
- Sucesso → `{"ok":true,"result":{"pesquisa":"2026-MM","registrado":"..."}}`

## Áreas (dropdown)

Banking Operations, Collection ExtraJudicial, Collection CondoJud, Corporate, Credit & Risk, Suporte ao Cliente, Relacionamento com o cliente, Implantação, Engineering, Finance, IT Operations, Marketing, People, Product, Sales

## Lideranças (dropdown)

Bruno Veronese, Franco Brognoli, Gianluca Dal Zotto, Guilherme Giacometti, Humberto Basso, Joanna Rosa, Kauê B Tomazelli, Leonardo Perin, Luciano Bernardi, Marcelo Cruz, Mateus Medeiros, Juliano 'PanThrO' Santana, Paulo Pereira (Caju), Renata Paim, Rodrigo Borer, Rodrigo Catarcione, Rodrigo Della Rocca, Rodrigo Costa, Sabrina Vieira, Silvana Muller, Solange Pereira, Victor Oliveira Barros do Nascimento, Wilson Dalmolin, Renata Otacilio, Andrieli Elmatos

## Formulário HTML

Arquivo: `/opt/data/formularios/form-pulse.html`

Características:
- Dropdowns para área e liderança
- Botões com emoji + texto (`😥| Muito Mal`, etc.) na interface
- `data-value="1"` a `"5"` nos botões — no JSON envia número, não texto
- Submit via `fetch()` com `Content-Type: application/x-www-form-urlencoded` (CORS-safelisted)
- Auth no body: `URLSearchParams` com `method`, `X-Service-Account-Token`, `auth` + campos do form
- URL: `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc`
- Banner: coração + ECG como background do header (base64, 40KB)