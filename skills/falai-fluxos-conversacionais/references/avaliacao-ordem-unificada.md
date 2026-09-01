# Ordem Unificada de Perguntas — Autoavaliação e Liderança

Para permitir comparabilidade direta entre autoavaliação e avaliação do líder,
todos os formulários do ciclo 2026.2 seguem a mesma ordem de dimensões.

## Ordem canônica (1-8)

| # | Dimensão | Autoavaliação | Liderança |
|---|---|---|---|
| 1 | Resultados | ⭐ Como avalia seus Resultados? | ⭐ Como avalia os Resultados de [nome]? |
| 2 | Área (métrica) | ✍️ Pergunta específica da área | ✍️ Pergunta específica da área |
| 3 | Competências | ⭐ Como avalia suas Competências? | ⭐ Como avalia as Competências de [nome]? |
| 4 | Autonomia / Prontidão | ✍️ Situação de autonomia | ✍️ Pronto para +responsabilidade? |
| 5 | Potencial | ⭐ Seu potencial 12-18 meses | ⭐ Potencial de [nome] 12-18 meses |
| 6 | Valor bem vivido | ✍️ SCI de valor vivido | ✍️ SCI de valor vivido |
| 7 | Valor a evoluir | ✍️ Onde precisa evoluir | ✍️ Onde precisa evoluir |
| 8 | PDI / Recomendação | ✍️ Plano de carreira 6 meses | 📋 Recomendação (Promoção/Mérito/etc.) |

## Diferença na Q8

- **Autoavaliação:** "O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira?" (PDI)
- **Liderança:** "Recomendação para este colaborador neste ciclo" (Lista suspensa: Promoção / Mérito / Bônus / Manter / PDI intensivo / PIP / Desligamento)

## Por que esta ordem?

1. **Resultados primeiro** — métrica objetiva, ancora a conversa
2. **Área** — contextualiza a entrega no domínio específico
3. **Competências** — avaliação de habilidades (CHA)
4. **Autonomia** — prontidão para assumir mais
5. **Potencial** — projeção de crescimento
6. **Valores (V+)** — o que está funcionando
7. **Valores (V-)** — onde melhorar
8. **Futuro** — PDI (auto) ou Recomendação (líder)

## Como aplicar nos geradores

### Autoavaliação executiva (`gerar_exec_forms.py`)
Aplicar reordenação `[0, 1, 3, 2, None, 4, 5, 6]` sobre o array original:
- Q1→Q1 (Resultados), Q2→Q2 (Área), Q4→Q3 (Competências), Q3→Q4 (Autonomia)
- Q5 é NOVA (Potencial, não existia no original)
- Q5→Q6 (V+), Q6→Q7 (V-), Q7→Q8 (PDI)
- Q8 original (Motivação) é **descartada**

### Liderança executiva (`gerar_lider_dellarocca.py`)
Basta trocar Q3↔Q4 (Prontidão e Competências), o resto já está na ordem correta.

## Pitfall: esquecer de reordenar

Se os geradores forem executados sem esta reordenação, autoavaliação e liderança
ficarão com ordens diferentes — impossibilitando o comparativo lado a lado no dash.
**Sempre verificar após regenerar** com `grep -oP '<label>\d+' <arquivo>.html | head -8`.