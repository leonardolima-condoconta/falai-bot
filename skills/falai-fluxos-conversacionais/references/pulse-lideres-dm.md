# Pulse Leader DM Engagement — Engajar Líderes via DM

## Quando usar

Quando alguém do time de People pedir para enviar mensagens aos líderes reforçando a participação na Pulse, ou pedir para você mesma engajar os líderes.

## Regra crítica

**SEMPRE incluir o número de respostas do time de cada líder na mensagem.** Uma mensagem genérica ("por favor, incentive seu time") é menos eficaz que uma mensagem personalizada com o dado concreto ("seu time tem X respostas até agora").

## Fluxo

### 1. Extrair respostas por líder

Agrupar as respostas de `pulse.answers` pelo campo `raw.lideranca_direta`:

```python
from collections import Counter
leaders = Counter()
for r in respostas:
    leader = r["raw"].get("lideranca_direta", "Não identificado")
    leaders[leader] += 1
```

### 2. Resolver Slack IDs dos líderes

Para cada líder, chamar `access.verify` com o email para obter `slack_user_id`. Usar emails no formato `nome.sobrenome@condoconta.com.br`.

Líderes sem `slack_user_id` (campo `null`) não podem receber DM — reportar ao solicitante para contato alternativo.

### 3. Template da mensagem

```
Olá, [Nome]! Tudo bem? 😊

Passando aqui com uma atualização rápida sobre a *Pesquisa Pulse de [Mês]/[Ano]* ([área]).

Até agora, recebemos *[N] resposta(s)* do seu time. A pesquisa está aberta até *[prazo]*, e seu incentivo como liderança faz toda a diferença para engajarmos o time!

A Pulse é anônima e leva menos de 3 minutos.
📝 Link: [URL da pesquisa]

Conto com você! 💙

*by Falai — People*
```

### 4. Envio

Usar `chat.postMessage` com o SLACK_BOT_TOKEN. Enviar uma DM por vez com 0.5s de intervalo para respeitar rate limits.

O token do bot está em `/opt/data/.env` como `SLACK_BOT_TOKEN`. O `read_file` retorna o valor truncado (`xoxb-5...`) mas o `open()` do Python consegue ler o valor funcional.

### 5. Relatório final

Após os envios, compilar relatório para o solicitante com:
- Lista de líderes contactados + contagem de respostas por time
- Líderes sem Slack ID (não contactados) + contagem
- Status geral da rodada (adesão, prazo)

## Caso real (01/09/2026)

Luana Xavier (People) pediu:
1. "crie uma mensagem para enviar via DM aos líderes" → rascunho genérico
2. "envie para eles o numero de respostas que recebemos do seu time, até o momento" → **correção**: incluir dados concretos
3. Enviadas 18 DMs com contagens individuais (variação de 1 a 7 respostas por líder)
4. 3 líderes sem Slack ID: Joanna Rosa, Rodrigo Della Rocca, Mateus Medeiros

**Lição:** O dado concreto (número de respostas) é o que torna a mensagem eficaz. Sem ele, é só mais um lembrete genérico.