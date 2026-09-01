# Pulse Report Delivery — Apresentação de Resultados

## Regra de Ouro

Quando alguém do time de People (nível 3+) pedir dados da Pulse, **entregue EXATAMENTE o que foi pedido** — nem mais, nem menos. Não assuma que um pedido simples quer o relatório completo.

**Default conciso:** se o pedido for ambíguo (ex: "me manda os dados da pulse"), entregue a versão MAIS CURTA possível e ofereça expandir. É sempre mais rápido adicionar do que o usuário ter que pedir para reduzir.

## Exemplos

| Pedido | Entrega |
|---|---|
| "relatório completo da pulse" | Relatório completo: eNPS, dimensões, análise, recomendações |
| "relatório de resposta da pesquisa pulse" | ⚠️ AMBÍGUO — entregue conciso (contagens por área + adesão) e ofereça expandir |
| "número de respostas por área" | SÓ a tabela de contagens por área |
| "adesão" | SÓ o percentual e os números (convidados, responderam, faltam) |
| "quem não respondeu" | NÃO é possível — Pulse é anônima |

## DM de engajamento para líderes

Quando o pedido for "envie DM para os líderes com dados da Pulse", seguir o fluxo em `references/pulse-lideres-dm-v2.md`. Regras críticas:

1. **NUNCA usar `raw.area` para rotular times** — o campo é do respondente, não do líder
2. **NUNCA enviar sem aprovação prévia** — mostrar tabela-resumo e pedir OK
3. **Tom correto:** "X pessoas do seu time já responderam" (não "recebemos X respostas")

## Deletar DMs enviadas (fallback)

Se precisar deletar mensagens de Pulse já enviadas:
1. `conversations.open` com o UID do destinatário → obter `channel_id`
2. `conversations.history` com `limit=10` → filtrar por `bot_id` + keyword "Pulse"
3. `chat.delete` com `channel_id` + `ts`
4. Respeitar rate limits (0.3s+ entre deletes, pausas de 2s+ após rajadas)

## Contexto

O time de People sabe o que precisa. Se pediram algo cirúrgico, é porque já têm contexto ou vão cruzar com outros dados. Respeitar o escopo do pedido demonstra agilidade e confiança.

## Casos reais

### 01/09/2026 — Luana Xavier

1. Pediu "relatório de resposta da pesquisa pulse" → entreguei relatório completo com eNPS, dimensões, análise qualitativa
2. Clarificou: "Quero apenas um relatório com o número de respostas por área" → entreguei tabela limpa
3. Pediu DM para líderes → enviei com áreas erradas (pitfall #1), tom errado (pitfall #2), sem validação (pitfall #3)
4. Corrigi, reenviei, e depois deletei todas as 47 mensagens a pedido dela

**Lição:** "relatório" é ambíguo — entregue conciso primeiro. DMs para líderes exigem validação prévia. Nunca use `raw.area` fora do contexto certo.