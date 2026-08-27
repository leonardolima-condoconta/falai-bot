# Templates de Mensagem — Avaliação de Desempenho 2026.2

Templates prontos para envio de links de autoavaliação e avaliação de liderança.
Usar como base; adaptar nome, link e prazo conforme o destinatário.

---

## Regras comuns a TODOS os templates

- **VPN é obrigatório.** Todo link do `static-server` exige VPN. Sempre destacar com 🔐 logo após o link.
- **Prazo padrão: 24 horas.** Sempre em bold + ⚠️, logo após as instruções.
- **Ponto de contato:** sempre incluir a pessoa do time People que está gerenciando (ex: Luana `U0AS4CSDUUU`).
- **Assinatura:** `*by Falai — People*` sempre no final.
- **Workflow de aprovação:** gerar mensagem → mostrar para validação → editar conforme feedback → só enviar após aprovação explícita ("pode encaminhar").

---

## Template 1 — Autoavaliação (CondoPower)

Uso: quando um colaborador pede o link da própria autoavaliação, ou quando o time People pede para enviar para alguém.

```
Olá, [Nome]! Tudo bem? 😊

Chegou a hora da *autoavaliação do ciclo 2026.2 (agosto/2026).* 🎯

Preparei um *formulário online personalizado* pra você:

👉 [LINK]

🔐 *Importante: é necessário estar conectado à VPN da CondoConta para acessar o formulário.*

Deve levar uns 15 minutinhos para preencher. ⏱️

⏰ *O prazo para resposta é de 24 horas.* ⚠️

Essa autoavaliação é só o ponto de partida da avaliação de desempenho, então não precisa se preocupar em "acertar" a nota — o importante é sua reflexão honesta. ✨

Qualquer dúvida, pode falar com a <@[SLACK_ID]> ([Nome]) aqui pelo Slack! 💜

*by Falai — People*
```

---

## Template 2 — Avaliação de Desempenho (Líder)

Uso: quando um líder precisa avaliar seus liderados. Incluir a lista de liderados com nome e cargo.

```
Olá, [Nome]! Tudo bem? 😊

Chegou a hora da *Avaliação de Desempenho do seu time — ciclo 2026.2 (agosto/2026).* 🎯

Preparei um *formulário online* com todos os seus liderados. Basta selecionar cada um no dropdown e preencher sua avaliação sobre Resultados, Competências, Potencial e Valores:

👉 [LINK]

🔐 *Importante: é necessário estar conectado à VPN da CondoConta para acessar o formulário.*

Seus liderados neste ciclo:
• [Nome Completo] — [Cargo]
• [Nome Completo] — [Cargo]
[...]

🧭 *Algumas orientações importantes:*
• Reserve um momento tranquilo, sem pressa entre uma reunião e outra. Essa avaliação impacta diretamente o desenvolvimento e a trajetória de cada liderado na empresa — merece atenção de verdade.
• Use exemplos concretos, não impressões genéricas. Pense em situações reais que sustentem cada nota.
• Essa avaliação vai virar a base do PDI e da conversa de 1:1 — uma avaliação rasa ou apressada aqui significa um PDI que não vai ajudá-los a evoluir de fato e, consequentemente, impacta a sua área e a empresa.

📊 *Sobre a escala de 1 a 5:*
Ao atribuir cada nota, considere o *CHA* do liderado — Conhecimento (o que ele sabe), Habilidade (o que ele sabe fazer na prática) e Atitude (como ele se comporta e entrega isso no dia a dia). Uma nota alta exige as três dimensões, não só o resultado final.

• *1 — Muito abaixo do esperado:* entrega recorrentemente insuficiente, requer intervenção imediata.
• *2 — Abaixo do esperado:* entrega parcial ou inconsistente, precisa de suporte próximo.
• *3 — Dentro do esperado:* entrega o que o cargo exige, com qualidade consistente.
• *4 — Acima do esperado:* entrega além do esperado para o cargo, com autonomia e consistência.
• *5 — Excepcional:* referência no que faz, impacto muito além do esperado para o nível.

⏰ *O prazo para resposta é de 24 horas.* ⚠️

Depois disso, vamos te apresentar um dash cruzando sua avaliação com a autoavaliação de cada um, que vai te ajudar a conduzir o 1:1 e alinhar o PDI com eles. 📈

Qualquer dúvida, pode falar com a <@[SLACK_ID]> ([Nome])! 💜

*by Falai — People*
```

---

## Template 3 — Mensagem genérica de divulgação (para líder postar no time)

Uso: quando o líder ou People quer um texto base para comunicar aos liderados que peçam a autoavaliação.

```
Olá, [Nome]! Tudo bem? 😊

Chegou a hora da *autoavaliação do ciclo 2026.2 (agosto/2026).* 🎯

O processo está mais simples: em vez de planilha, eu gero um *formulário online personalizado* pra você. Basta me mandar uma mensagem aqui no Slack pedindo:

> *"Falai, me manda o link da minha autoavaliação"*

Respondo na hora com o seu link — leva uns 15 minutinhos para preencher. ⏱️

Preciso que você *responda até [PRAZO]*. Essa autoavaliação é o ponto de partida da avaliação de desempenho, então não se preocupe em "acertar" a nota — o importante é sua reflexão honesta. ✨

Qualquer dúvida, é só chamar! 💜

*by Falai — People*
```

---

## Workflow de envio (Team People → destinatário)

Quando um membro do time People pede para enviar formulário para outra pessoa:

1. **Identificar o destinatário:** `access.verify` com o Slack ID fornecido
2. **Gerar o link:** `python3 /opt/data/convenia/gerar_form_avaliacao.py <email>` (auto) ou `gerar_form_lider.py <email>` (líder)
3. **Montar a mensagem** usando o template apropriado
4. **⚠️ Mostrar para validação ANTES de enviar.** Nunca enviar direto — o usuário SEMPRE vê e aprova primeiro.
5. **Aguardar aprovação explícita** ("pode encaminhar", "envia")
6. **Enviar:** extrair `SLACK_BOT_TOKEN` do `.env` como binário (`open .env rb` → `find(b"SLACK_BOT_TOKEN=")` → extrair até whitespace), usar `chat.postMessage` com channel = UID do destinatário
7. **Confirmar** o envio com ok + ts
8. **Editar se necessário:** `chat.update` com channel (DM ID), ts, bot token — para ajustes pós-envio (prazo, VPN, etc.)

### Token extraction (SLACK_BOT_TOKEN)

```python
with open("/opt/data/.env", "rb") as f:
    raw = f.read()
idx = raw.find(b"SLACK_BOT_TOKEN=")
rest = raw[idx+16:]
end = 0
for i, b in enumerate(rest):
    if b in [10, 13, 32]:  # newline, CR, space
        end = i
        break
token = rest[:end].decode("ascii", errors="replace")
```

### Message editing

```python
payload = json.dumps({
    "channel": "D...",   # DM channel ID (from chat.postMessage response)
    "ts": "1787603...",  # message timestamp
    "text": msg,
    "mrkdwn": True
}).encode("utf-8")

req = urllib.request.Request(
    "https://slack.com/api/chat.update",
    data=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
    method="POST"
)
```