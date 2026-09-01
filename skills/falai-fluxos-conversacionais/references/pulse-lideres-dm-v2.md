# Pulse Leader DM Engagement — Engajar Líderes via DM (v2)

> Esta é a versão atualizada do fluxo de engajamento de líderes para a Pulse.
> Versão anterior: `pulse-lideres-dm.md`

## Quando usar

Quando alguém do time de People pedir para enviar mensagens aos líderes reforçando a participação na Pulse.

## ⛔ Pitfalls — ERROS QUE JÁ ACONTECERAM (NÃO REPITA)

### 1. Usar `raw.area` da resposta para rotular times (01/09/2026)

O campo `raw.area` é o **departamento do respondente**, NÃO o time que o líder lidera.
Ex: Solange lidera ExtraJudicial. Um liderado dela da área CondoJud respondeu. Rotular
a DM como "Collection ExtraJudicial + CondoJud" foi ERRADO — CondoJud não é time dela.

**REGRA:** NUNCA mencione áreas/departamentos nas DMs. Só a contagem. Se precisar de
contexto, use `access.verify` no líder e pegue `employee.department`.

### 2. Tom da mensagem parecia instruir o líder a responder (01/09/2026)

"Recebemos X resposta(s) do seu time" → o líder pode interpretar como se ELE precisasse responder.
"X pessoa(s) do seu time já respondeu(ram)" → deixa claro que é sobre o time.

### 3. Enviar sem validação prévia (01/09/2026)

Enviei 18 DMs sem mostrar os dados para a Luana. Resultado: 52 mensagens para corrigir e deletar.

**REGRA:** SEMPRE mostre a tabela-resumo antes de disparar e peça confirmação explícita.

## Fluxo completo

### 1. Extrair contagens por líder

Agrupar `pulse.answers` por `raw.lideranca_direta`:

```python
from collections import Counter
leaders = Counter()
for r in respostas:
    leader = r["raw"].get("lideranca_direta", "Não identificado")
    leaders[leader] += 1
```

### 2. Resolver Slack IDs

`access.verify` com email `nome.sobrenome@condoconta.com.br`. Líderes sem `slack_user_id` → reportar ao solicitante.

### 3. Validar com o solicitante (OBRIGATÓRIO)

Montar tabela e pedir OK:

```
Vou enviar para [N] líderes:

| Líder               | Respostas |
|---------------------|-----------|
| Solange Pereira     |     7     |
| Franco Brognoli     |     6     |
| ...                 |    ...    |

⚠️ Sem Slack ID: Joanna Rosa, Rodrigo Della Rocca, Mateus Medeiros

Confirma o envio?
```

### 4. Template da mensagem

```
Olá, [Nome]! Tudo bem? 😊

Passando aqui com uma atualização sobre a *Pesquisa Pulse de [Mês]/[Ano]*.

Até agora, *[N] pessoa(s) do seu time já respondeu(ram)* à pesquisa. Ela fica aberta até *[prazo]*, e seu incentivo como liderança faz toda a diferença para engajarmos quem ainda não respondeu!

A Pulse é anônima e leva menos de 3 minutos.
📝 Link: [URL da pesquisa]

Conto com você para chegarmos numa adesão bem representativa! 💙

*by Falai — People*
```

⚠️ NÃO incluir áreas/departamentos. Só nome, contagem, prazo e link.

### 5. Enviar

`chat.postMessage` com SLACK_BOT_TOKEN, 0.5s de intervalo.
Token: leitura binária (`open("/opt/data/.env", "rb")`) → buscar `SLACK_BOT_TOKEN=`.

### 6. Relatório pós-envio

Lista de contactados + contagens + sem-Slack + status geral da rodada.

## Deletar mensagens enviadas (fallback)

Se precisar deletar, fluxo: `conversations.open` → `conversations.history` (últimas 10) → filtrar por `bot_id` + keyword "Pulse" → `chat.delete`. Respeitar rate limits (0.3s+ entre deletes).

## Caso real completo (01/09/2026)

1. Luana pediu DM para líderes sobre Pulse
2. Rascunho genérico → ela corrigiu: "inclua número de respostas"
3. Enviei com ÁREAS ERRADAS (usei `raw.area` dos respondentes)
4. Luana: "você enviou errado, mencionando times que eles não lideram. Verifique um a um."
5. Luana: "a mensagem também não ficou legal, parecia instruindo os líderes a responder"
6. Reenviei 18 DMs corrigidas (só contagem, tom ajustado)
7. Luana: "delete todas que se referem à pulses"
8. Deletei 47 mensagens (5 já não existiam)
9. 3 líderes sem Slack ID: Joanna Rosa, Rodrigo Della Rocca, Mateus Medeiros

**Lição definitiva:** contagem + tom certo + validação prévia = zero retrabalho.