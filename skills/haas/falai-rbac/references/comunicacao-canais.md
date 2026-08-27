# Canais de Comunicação — People

Canais usados pela Falai para comunicados de People.

## #comunicação (C01H5UESZJN)

Canal público para comunicados voltados às pessoas do CondoConta. Propósito oficial:
- **[People]** Comemoração — Aniversário e Tempo de casa; Oportunidades; Novos CondoPowers; Feriados.
- **[Geral]** Pesquisas; Políticas da empresa; Orientações; Centrais de Ajuda; Movimentações internas.

**Como postar:** Bot não tem scope `channels:join`, mas `chat:write.public` permite postar direto via `chat.postMessage` com o `SLACK_BOT_TOKEN`. Não precisa estar no canal — o scope público cobre.

**Exemplo de post via API:**
```python
payload = json.dumps({
    "channel": "C01H5UESZJN",
    "text": message,
    "mrkdwn": True
}).encode('utf-8')
req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=payload,
    headers={"Authorization": f"Bearer {bot_token}", "Content-Type": "application/json"},
    method="POST"
)
```

**Formato de comunicado padrão:**
- 🚨 emoji + título bold
- Corpo: contexto + orientações em bullets
- Assinatura: `*by Falai — People*`

**Histórico de uso:** 24/08/2026 — comunicado sobre falha de comunicação com VPN, acionando ITOps (Peter Parker, U0BGHJ8M9MK).