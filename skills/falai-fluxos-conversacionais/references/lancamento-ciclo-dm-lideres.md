# Lançamento de ciclo — DM em massa para líderes

Fluxo executado em 28/08/2026 para o ciclo 2026.2. Reutilizável para ciclos futuros.

## Pré-requisitos

- JSONs de avaliação em `/opt/data/convenia/`
  - `autoavaliacao_perguntas.json` — estrutura: `{areas: [{area, colaboradores: [{nome, cargo, area, nivel, gestor, ...}]}]}`
  - `avaliacao_lider_perguntas.json` — mesma estrutura; `gestor` preenchido indica liderança
- Token do Slack Bot acessível via raw bytes do `.env`
- API Slack: `users.list` + `chat.postMessage`

## Passo a passo

### 1. Carregar dados e montar mapa líder → liderados
```python
from collections import defaultdict

leader_reports = defaultdict(list)
for area in data['areas']:
    for colab in area['colaboradores']:
        gestor = colab.get('gestor', '').strip()
        if gestor:
            leader_reports[gestor].append({
                'nome': colab['nome'],
                'cargo': colab['cargo'],
                'area': area['area']
            })
```

### 2. Cruzar com Slack para obter UIDs
Usar 3-pass flexible matching (exato → parcial primeiras 2 palavras → sem acentos):

```python
# Pass 1: exact lowercase
name_map = {u['profile']['real_name'].lower(): u['id'] 
            for u in users if not u.get('deleted') and not u.get('is_bot')}

uid = name_map.get(leader_name.lower())

# Pass 2: first 2 name parts
if not uid:
    parts = leader_name.lower().split()[:2]
    for nk, nuid in name_map.items():
        if all(p in nk for p in parts):
            uid = nuid; break

# Pass 3: strip accents
if not uid:
    import unicodedata
    def strip(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    search = strip(leader_name.lower())
    for u in users:
        real = strip((u.get('profile',{}).get('real_name','')).lower())
        if search in real or all(p in real for p in search.split()):
            uid = u['id']; break
```

### 3. Template da DM

```
Olá, *{nome_curto}*! 👋

Na *segunda-feira, {data}*, daremos início ao ciclo de *Avaliação de Desempenho {ciclo}* da CondoConta. Os links individuais serão encaminhados no decorrer do dia.

Antes disso, peço que confira a lista de liderados que está cadastrada para você:

  {lista_numerada_de_liderados_com_cargo}

⚠️ *Se houver qualquer alteração* (liderado faltando, sobrando ou nome incorreto), me avise por aqui que encaminho na hora para ajuste nos formulários.

Se estiver tudo certo, não precisa responder — na {dia_da_semana} você recebe os links! 🚀

*by Falai — People*
```

### 4. Enviar via chat.postMessage com bot token

```python
payload = json.dumps({
    "channel": uid,  # User UID — Slack auto-cria o DM
    "text": msg,
    "mrkdwn": True
}).encode('utf-8')

req = urllib.request.Request(
    "https://slack.com/api/chat.postMessage",
    data=payload,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST"
)
```

⚠️ Rate limit: 0.8–1.0s entre mensagens para 20+ destinatários.

### 5. Relatar resultado
- ✅ 22/23 enviadas (28/08/2026)
- ❌ Paulo Fernando da Costa Pereira Filho — sem Slack, requer canal alternativo

## Pitfalls

- **Nomes truncados nos JSONs**: os JSONs de avaliação têm campo `nome` com ~28 caracteres. Ex: `Eduardo Victor Nóbrega Ferna` em vez de `Eduardo Victor Nóbrega Fernandes`. Os líderes podem questionar.
- **Acentos quebram match exato**: `Kauê` vs `Kaue`, sempre usar strip_accents no Pass 3.
- **Nome no Slack ≠ nome no cadastro**: `Solange Pereira` (Slack) vs `Solange Gonçalves da Costa Pereira` (Convenia). Só o Pass 2 resolve.
- **Container não alcança a condopower-api direto**: usar webhook-proxy sempre (`condopower-api-routing` skill).

---

## Fase 2 — DM de lançamento ("avaliar agora")

Enviada APÓS a publicação dos formulários HTML. Template aprovado por Luana Beatrís Xavier
em 31/08/2026 (ciclo 2026.2, 25 líderes, 121 liderados).

### Template da mensagem

```
Olá, {primeiro_nome}! Tudo bem? :blush:

Chegou a hora da *avaliação de desempenho do seu time — ciclo {ciclo}.* :dart:

Preparei um *formulário online* com todos os seus liderados. Basta selecionar cada um no dropdown e preencher sua avaliação sobre Resultados, Competências, Potencial e Valores:

:point_right: {url_formulario}

Seus liderados neste ciclo:
• {nome_liderado_1} — {cargo_1}
• {nome_liderado_2} — {cargo_2}
...

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

Qualquer dúvida, pode falar com a @U0AS4CSDUUU Beatrís Xavier! :purple_heart:
```

### Placeholders

| Placeholder | Fonte | Exemplo |
|---|---|---|
| `{primeiro_nome}` | `name.split()[0]` do líder | `Rodrigo` |
| `{ciclo}` | Definido pelo time People | `2026.2 (agosto/2026)` |
| `{url_formulario}` | Slug = `email.split("@")[0].replace(".", "-")` | `avaliacao-lider-rodrigo-catarcione` |
| `{nome_liderado_N}` | `reports[].name` | `Amanda Elena de Almeida` |
| `{cargo_N}` | `reports[].job` | `Analista de Endomarketing` |

### ⚠️ Pitfall: slug da URL é prefixo do e-mail, NÃO nome completo

`gerar_form_lider.py` (linha 336) monta o slug assim:
```python
slug = "avaliacao-lider-" + EMAIL.lower().split("@")[0].replace(".", "-").replace(" ", "-")[:50]
```

Ou seja, `rodrigo.catarcione@condoconta.com.br` → `avaliacao-lider-rodrigo-catarcione`,
NUNCA `avaliacao-lider-rodrigo-alexandre-catarcione`. Usar o nome completo gera URL errada
e o líder clica em link quebrado.

### Fluxo de geração + envio

1. Gerar formulários: `python3 /opt/data/convenia/gerar_form_lider.py <email>` × 25
2. Buscar liderados: `GET /api/v3/employees` do Convenia → mapa `supervisor_id → reports[]`
3. Mapear emails → Slack UIDs: `users.list` com paginação (workspace >200 membros)
4. Para cada líder: `conversations.open` → `chat.postMessage` com `mrkdwn: true`
5. Para edições em massa: `chat.update` com `channel` + `ts`
6. Intervalo mínimo: 1.2s entre chamadas (rate limit)

### Edição em massa (chat.update)

Após o envio, se precisar alterar TODAS as mensagens (ex: incluir aviso de suporte,
corrigir prazo, trocar template inteiro):

```python
# Reabre DM e faz update
dm = slack_api("conversations.open", {"users": uid})
channel = dm['channel']['id']
slack_api("chat.update", {"channel": channel, "ts": ts, "text": new_msg, "mrkdwn": True})
```

### Contato de suporte (FIXO)

- **UID da Luana**: `U0AS4CSDUUU` — NUNCA alterar esse UID; é fixo em todas as DMs de avaliação
- **Canal**: `#people-hr` (C0BJLA3H16F) para comunicações internas do time

---

## Fase 3 — DM de autoavaliação (colaboradores individuais)

Enviada após a geração dos formulários HTML de autoavaliação. Template aprovado por
Luana Beatrís Xavier em 31/08/2026 (ciclo 2026.2, 108 colaboradores).

### Pré-requisito: cruzar autoavaliacao_perguntas.json com API Convenia

O JSON de autoavaliação (`autoavaliacao_perguntas.json`) **NÃO tem campo `email`**.
É obrigatório cruzar com a API Convenia para obter os emails antes de gerar formulários:

```python
import os, sys, json, unicodedata, re
os.chdir('/opt/data/convenia')
sys.path.insert(0, '/opt/data')
from convenia import ConveniaClient

def norm(s):
    s = re.sub(r'\s+', ' ', s.lower().strip())
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

# 1. Carregar emails do Convenia
with ConveniaClient() as client:
    resp = client._client.get("/api/v3/employees", params={"per_page": 200})
    employees = resp.json()["data"]
conv_map = {norm(f"{e.get('name','')} {e.get('last_name','')}"): e.get('email','') for e in employees}

# 2. Cruzar com autoavaliacao JSON
with open("/opt/data/convenia/autoavaliacao_perguntas.json") as f:
    auto = json.load(f)
matched, no_match = 0, 0
for area in auto.get("areas", []):
    for c in area["colaboradores"]:
        cname = norm(c["nome"])
        email = conv_map.get(cname, "")
        if not email:
            # Tentar match parcial (nomes truncados nos JSONs)
            for k, v in conv_map.items():
                if len(cname) > 5 and (cname[:15] in k or k[:15] in cname):
                    email = v; break
        c["email"] = email
        if email: matched += 1
        else: no_match += 1  # ~12 de 122 sem match — sem Slack/email
```

### Geração dos formulários de autoavaliação

```bash
python3 /opt/data/convenia/gerar_form_avaliacao.py <email>  # 1 por colaborador
```

⚠️ URLs usam slug baseado no nome (diferente dos formulários de líder que usam email prefix).

### Template da mensagem (autoavaliação)

```
Olá, {primeiro_nome}! Tudo bem? :blush:

Chegou a hora da sua *autoavaliação de desempenho — ciclo {ciclo}.* :dart:

Preparei um *formulário online* para você refletir sobre sua performance neste ciclo — Resultados, Competências, Potencial e Valores:

:point_right: {url_formulario}

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

:alarm_clock: *O prazo para resposta é de 4 dias.* :warning:

Depois disso, seu gestor terá acesso a um dash cruzando sua autoavaliação com a avaliação que ele fez de você — isso vai guiar a conversa de 1:1 e a construção do seu PDI. :chart_with_upwards_trend:

Qualquer dúvida, pode falar com a {mencao_luana}! :purple_heart:
```

### Envio para autoavaliação (108 DMs)

Mesmo fluxo da Fase 2: `conversations.open` → `chat.postMessage` → 1.2s delay.
~12 colaboradores sem email ficam de fora (nomes não batem com Convenia).

### Edição em massa de TODAS as mensagens (chat.update)

Quando o time de People pede alterações no template após o envio (ex: trocar prazo,
corrigir menção, incluir novo parágrafo), usar `chat.update` em todas as DMs:

```python
# Carrega resultados do envio original (guarda {email, ts})
# Para cada mensagem:
dm = slack_api("conversations.open", {"users": uid})  # reabre DM
channel = dm['channel']['id']
slack_api("chat.update", {
    "channel": channel,
    "ts": ts,             # timestamp da mensagem original
    "text": novo_texto,   # texto completo (substituição integral)
    "mrkdwn": True
})
```

⚠️ `chat.update` substitui o texto INTEIRO — não é append. Sempre passar a mensagem completa.
1.2s delay entre chamadas. Bot token funciona (não precisa user token para editar).

### 🔴 CRITICAL — Edição em massa SOBRESCREVE correções anteriores

Quando se faz `chat.update` em todas as 108 DMs para alterar um campo (ex: prazo),
o JSON de origem das mensagens (`mensagens_autoavaliacao_<ciclo>.json`) **precisa estar
atualizado** com todas as correções de links aplicadas anteriormente. Se o JSON ainda
contiver URLs erradas, o `chat.update` vai **reintroduzir os links incorretos** e
desfazer todas as correções manuais anteriores.

**Regra de ouro:** antes de qualquer edição em massa, SEMPRE:
1. Ler o estado ATUAL de pelo menos as DMs dos casos corrigidos (via `conversations.history`)
2. Atualizar o JSON de origem com as URLs corretas
3. Só então disparar o `chat.update` em massa

Exemplo real (31/08/2026): ao alterar prazo de 1→4 dias, as DMs da Vanessa, Cauã,
Letícia, etc. voltaram a ter links errados porque o JSON ainda tinha as URLs antigas.

### 🔴 CRITICAL — Colisão de fuzzy matching no gerar_form_avaliacao.py

O script `gerar_form_avaliacao.py` faz fuzzy matching: quebra o e-mail em partes
(ex: `vanessa`, `silva`) e pontua cada nome no JSON. Quando dois nomes compartilham
as mesmas partes, o PRIMEIRO no JSON ganha — mesmo que seja a pessoa errada.

**Exemplos de colisões (ciclo 2026.2):**

| E-mail enviado | Nome correto | Link gerado (errado → pertence a) |
|---|---|---|
| `vanessa.silva@` | Vanessa da Silva | `daniele-vanessa-severo-silva` → Daniele |
| `joao.carvalho@` | João G. Teixeira Braga | `raphael-de-carvalho-cortes` → Raphael |
| `caua.lima@` | Cauã Daniel Lima | `rafael-pacifico-segundo-lima` → Rafael |
| `vitoria.sousa@` | Vitória Kimberllan | `vitor-pacheco` → Vitor Pacheco |
| `leticia.santos@` | Letícia F. dos Santos | `magda-mayara-dos-santos-mont` → Magda |
| `juliana.simoes@` | Juliana Xavier Simões | `julia-eulalia-baldoino-marqu` → Julia |
| `danielly.costa@` | Danielly Maire | `paulo-fernando-da-costa-pere` → Paulo |
| `solange.pereira@` | Solange G. da Costa | `paulo-fernando-da-costa-pere` → Paulo |

**Causa raiz:** os nomes nos JSONs são truncados a ~31 caracteres. O fuzzy matching
compara partes do email (`vanessa`, `silva`) com partes de TODOS os nomes. "Daniele
**Vanessa** Severo **Silva**" pontua mais alto que "**Vanessa** da **Silva**" porque
tem mais palavras que batem.

### Solução: email_override_map.json + patch no gerar_form_avaliacao.py

**Passo 1:** Criar `/opt/data/convenia/email_override_map.json`:
```json
{
  "vanessa.silva@condoconta.com.br": "Vanessa da Silva",
  "joao.carvalho@condoconta.com.br": "João Guilherme Teixeira Brag",
  "caua.lima@condoconta.com.br": "Cauã Daniel Lima da Silva",
  ...
}
```

**Passo 2:** Patch no `gerar_form_avaliacao.py` — adicionar prioridade 1 (override)
antes do fuzzy matching, com match por prefixo (nomes truncados):

```python
# Priority 1: exact override by email
override_name = _email_overrides.get(EMAIL.lower())
if override_name:
    override_lower = override_name.lower()
    for t, src, col in all_cols:
        nome_lower = col["nome"].lower()
        if nome_lower == override_lower or \
           override_lower.startswith(nome_lower) or \
           nome_lower.startswith(override_lower[:len(nome_lower)]):
            tipo_form, source_data, colaborador = t, src, col
            break

# Priority 2: fuzzy matching (original)
if not colaborador:
    # ... fuzzy matching original ...
```

**Passo 3:** Após gerar formulários, AUDITAR todos os links ANTES de enviar:
```python
# Para cada {email, url} gerado:
# Extrair slug da URL e verificar se contém partes do nome correto
# Se não contiver → gerar novamente COM o override map ativo
```

### Verificação pós-envio

Após enviar, ler o texto real de algumas DMs via `conversations.history` para
confirmar que o link na DM corresponde à pessoa correta:
```python
hist = slack_api("conversations.history", {"channel": ch, "latest": ts, "limit": 1, "inclusive": true})
for line in hist["messages"][0]["text"].split("\n"):
    if "static-server" in line:
        # verificar slug
```

### Menção no Slack — formato correto

- ❌ `@U0AS4CSDUUU` — NÃO funciona, não gera notificação
- ✅ `<@U0AS4CSDUUU>` — formato mrkdwn correto, gera notificação e exibe nome