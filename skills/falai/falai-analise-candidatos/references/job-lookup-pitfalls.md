# Pitfalls — Localizar vaga e contar candidatos

## Vagas com nomes similares

No InHire da CondoConta existem DUAS vagas de Business Partner com nomes parecidos:

| Vaga | ID curto | Status |
|---|---|---|
| HR Business Partner | `d337e1` | Aberta |
| Business Partner People | `76872f` | Congelada |

Se o usuário disser "vaga de Business Partner" sem especificar qual, SEMPRE confirme antes de reportar números. Pergunte qual ou mostre as duas opções.

"Business Partner People" = `76872fdd-dc42-4be1-b1c8-20bdb027f286` (71 talentos, 14/08/2026).
"HR Business Partner" = `d337e149-54e5-4a84-b378-b83dd849bbb3` (61 talentos, 14/08/2026).

## Sessão de browser expira entre navegações

Quando `document.body.innerText` retorna "Acesse sua conta", a sessão foi perdida.
Basta re-logar (etapa 2 do fluxo principal) e re-navegar para a URL desejada.
Não é erro — é comportamento normal da SPA do InHire.

## "Posições Abertas: 0" não significa vaga fechada

O campo "Posições Abertas" na listagem do dashboard pode ser 0 mesmo com a vaga `Aberta`.
Verifique SEMPRE o label de status (`Aberta` / `Congelada` / `Fechada` / `Cancelada`) separadamente.