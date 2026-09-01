# Ordem Unificada de Perguntas — Autoavaliação & Liderança

> **Por que:** ter a mesma ordem em ambos os formulários permite um comparativo
> mais assertivo no dash de 1:1. A Luana pediu isso explicitamente (31/08/2026).

## Ordem canônica (1 a 8)

| # | Dimensão | Autoavaliação | Liderança | Tipo |
|---|----------|---------------|-----------|------|
| 1 | Resultados | Como avalia seus Resultados? | Como avalia os Resultados de [nome]? | Escala 1-5 |
| 2 | Métrica da área | Pergunta específica da área | Pergunta específica da área | Texto aberto |
| 3 | Competências | Como avalia suas Competências? | Como avalia as Competências de [nome]? | Escala 1-5 |
| 4 | Autonomia / Prontidão | Situação de autonomia extra | Pronto para +responsabilidade? | Texto aberto |
| 5 | Potencial | Seu potencial 12-18 meses | Potencial de [nome] 12-18 meses | Escala 1-5 |
| 6 | Valor bem vivido | SCI de valor CondoConta | SCI de valor CondoConta | Texto aberto |
| 7 | Valor a evoluir | Onde precisa evoluir | Onde precisa evoluir | Texto aberto |
| 8 | PDI / Recomendação | Plano de carreira 6 meses | Recomendação (Promoção/Mérito/etc.) | Texto / Lista |

## Aplicando em formulários gerados pelo JSON

O JSON original (`autoavaliacao_perguntas.json`) tem ordem diferente:
`1-R, 2-Área, 3-Autonomia, 4-C, 5-V+, 6-V-, 7-PDI, 8-Motivação`

Reordenar com `new_order = [0, 1, 3, 2, None, 4, 5, 6]` onde:
- Índice = posição no array original
- `None` = pergunta nova (Potencial, escala 1-5)
- Drop Q8 original (Motivação) — não entra na nova ordem

```python
new_order = [0, 1, 3, 2, None, 4, 5, 6]
for new_n, old_idx in enumerate(new_order):
    display_n = new_n + 1
    if old_idx is None:
        # Nova pergunta: Potencial
        ...
    else:
        q = qs[old_idx]  # Reordenada
        ...
```

## Para formulários executivos (planilhas individuais)

Cada planilha tem as perguntas na ordem original do Excel. Aplicar a mesma reordenação
antes de gerar o HTML.

## Pergunta de Potencial (nova — adicionada em 31/08/2026)

```
"Como voce avalia seu Potencial para assumir mais responsabilidade nos proximos 12-18 meses?"
```
Escala 1-5. Não existia no JSON original. É adicionada como Q5 em todos os formulários
de autoavaliação.