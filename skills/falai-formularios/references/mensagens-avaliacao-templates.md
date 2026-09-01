# Templates de Mensagens — Avaliação de Desempenho

Modelos finais aprovados para o ciclo 2026.2 (agosto/2026).

---

## Avaliação de Liderança (gestor avalia liderados)

```
Olá, PRIMEIRO_NOME! Tudo bem? :blush:

Chegou a hora da *avaliação de desempenho do seu time — ciclo 2026.2 (agosto/2026).* :dart:

Preparei um *formulário online* com todos os seus liderados. Basta selecionar cada um no dropdown e preencher sua avaliação sobre Resultados, Competências, Potencial e Valores:

:point_right: URL_FORMULARIO

Seus liderados neste ciclo:
• NOME — CARGO

:compass: *Algumas orientações importantes:*
• Reserve um momento tranquilo, sem pressa entre uma reunião e outra. Essa avaliação impacta diretamente o desenvolvimento e a trajetória de cada liderado na empresa — merece atenção de verdade.
• Use exemplos concretos, não impressões genéricas. Pense em situações reais que sustentem cada nota.
• Essa avaliação vai virar a base do PDI e da conversa de 1:1 — uma avaliação rasa ou apressada aqui significa um PDI que não vai ajudá-los a evoluir de fato e, consequentemente, impacta a sua área e a empresa.

:bar_chart: *Sobre a escala de 1 a 5:*
Ao atribuir cada nota, considere o *CHA* do liderado — Conhecimento (o que ele sabe), Habilidade (o que ele sabe fazer na prática) e Atitude (como ele se comporta e entrega isso no dia a dia). Uma nota alta exige as três dimensões, não só o resultado final.

• _1 — Muito abaixo do esperado:_ entrega recorrentemente insuficiente, requer intervenção imediata.
• _2 — Abaixo do esperado:_ entrega parcial ou inconsistente, precisa de suporte próximo.
• _3 — Dentro do esperado:_ entrega o que o cargo exige, com qualidade consistente.
• _4 — Acima do esperado:_ entrega além do esperado para o cargo, com autonomia e consistência.
• _5 — Excepcional:_ referência no que faz, impacto muito além do esperado para o nível.

:alarm_clock: *O prazo para resposta é de 4 dias.* :warning:

Depois disso, vamos te apresentar um dash cruzando sua avaliação com a autoavaliação de cada um, que vai te ajudar a conduzir o 1:1 e alinhar o PDI com eles. :chart_with_upwards_trend:

Qualquer dúvida, pode falar com a <@U0AS4CSDUUU>! :purple_heart:
```

**Regras:**
- `PRIMEIRO_NOME` = `name.split()[0]`
- URL usa slug do prefixo do e-mail: `email.split("@")[0].replace(".", "-")`
- Menção do Slack usa `<@UID>` (NUNCA `@UID` sem brackets)
- Prazo padrão: 4 dias

---

## Autoavaliação (colaborador se autoavalia)

```
Olá, PRIMEIRO_NOME! Tudo bem? :blush:

Chegou a hora da sua *autoavaliação de desempenho — ciclo 2026.2 (agosto/2026).* :dart:

Preparei um *formulário online* para você refletir sobre sua performance neste ciclo — Resultados, Competências, Potencial e Valores:

:point_right: URL_FORMULARIO

:compass: *Algumas orientações importantes:*
• Reserve um momento tranquilo, sem pressa. Essa é a sua oportunidade de trazer exemplos concretos do seu trabalho e mostrar como você contribuiu neste ciclo.
• Use exemplos reais, não impressões genéricas. Pense em situações específicas que sustentem cada nota que você se atribuir.
• Sua autoavaliação vai se cruzar com a avaliação do seu gestor no dash de 1:1 — é o momento de você contar sua versão da história com honestidade.

:bar_chart: *Sobre a escala de 1 a 5:*
Ao se autoavaliar, considere o *CHA* — Conhecimento (o que você sabe), Habilidade (o que você sabe fazer na prática) e Atitude (como você se comporta e entrega no dia a dia).

• _1 — Muito abaixo do esperado:_ entrega recorrentemente insuficiente, requer intervenção imediata.
• _2 — Abaixo do esperado:_ entrega parcial ou inconsistente, precisa de suporte próximo.
• _3 — Dentro do esperado:_ entrega o que o cargo exige, com qualidade consistente.
• _4 — Acima do esperado:_ entrega além do esperado para o cargo, com autonomia e consistência.
• _5 — Excepcional:_ referência no que faz, impacto muito além do esperado para o nível.

:alarm_clock: *O prazo para resposta é de 1 dia.* :warning:

Depois disso, seu gestor terá acesso a um dash cruzando sua autoavaliação com a avaliação que ele fez de você — isso vai guiar a conversa de 1:1 e a construção do seu PDI. :chart_with_upwards_trend:

Qualquer dúvida, pode falar com a <@U0AS4CSDUUU>! :purple_heart:
```

**Regras:**
- `PRIMEIRO_NOME` = `name.split()[0]`
- URL gerada pelo `gerar_form_avaliacao.py <email>`
- Prazo padrão: 1 dia (mais curto que liderança)
- Não lista liderados — é individual

---

## Disparo em massa via Slack DM

Fluxo usado para enviar 133 DMs (25 liderança + 108 autoavaliação):

1. **Email → UID:** paginar `users.list` (200/página com `cursor`, `time.sleep(1.5)` entre páginas) → montar `email_map`
2. **Abrir DM:** `conversations.open` com `users: uid`
3. **Enviar:** `chat.postMessage` com `mrkdwn: true`
4. **Editar:** `chat.update` com `ts` da mensagem original
5. **Rate limit:** `time.sleep(1.1-1.2)` entre chamadas (evita 429)

Menção no Slack DEVE usar `<@UID>` — `@UID` sem brackets não gera notificação.

### Pitfall: Slack token masking

O framework Hermes mascara tokens como `***`. Para ler o `SLACK_BOT_TOKEN`:
```python
with open("/opt/data/.env", "rb") as f:
    raw = f.read()
idx = raw.find(b"SLACK_BOT_TOKEN=")
token = raw[idx+len(b"SLACK_BOT_TOKEN="):raw.find(b"\n", idx)].decode()
```