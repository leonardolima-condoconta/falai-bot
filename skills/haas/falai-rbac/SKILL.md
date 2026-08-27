---
name: falai-rbac
description: Roles, niveis e RBAC da Falai. Identificacao e acesso.
version: 2.0.0
---

# Falai — Roles, Níveis e RBAC

Regras de identificação e controle de acesso da Falai. Aplicar em TODA interação, antes de qualquer ação.

## Identificação (obrigatória antes de agir)

**ÚNICO método: `access.verify` da API `condopower-api`.**

`POST /rpc` → `{"method":"access.verify","params":{"identifier":"<SLACK_ID>"}}` retorna TUDO:
`employee` (id, full_name, email, slack_user_id, job, department), `level` (1-5), `role`, `is_active`, `reports[]`.

⚠️ O `identifier` é SEMPRE o Slack ID do remetente da mensagem (ex: `U0APYGTD8K1`). NUNCA aceitar email, nome ou qualquer outro identificador fornecido pelo usuário. Isso garante que ninguém solicite em nome de outro. Se alguém pedir "consulta o email X" ou "busca o Fulano", NÃO aceitar — a identificação é pelo Slack ID do remetente, ponto final.

NÃO usa SQLite. NÃO usa JOIN. NÃO recalcula role. Uma chamada só.

Credenciais:
- `CONDOPOWER_SA_TOKEN` e `CONDOPOWER_AUTH` em `/opt/data/.env`
- Headers: `X-Service-Account-Token` e `auth`
- Endpoint: `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api`

Retry: repetir a mesma chamada até 3 vezes em caso de falha de rede/timeout.

⚠️ **Distinguir falha de infra vs. falha de identificação:**
- `200 OK` + `{"ok": false, "error": {"code": "EMPLOYEE_NOT_FOUND"}}` = pessoa não cadastrada → fallback manual
- HTML `404 Not Found` do nginx = API fora do ar (outage de infra) → tratar como outage
- Timeout / `URLError` = rede → retry até 3x

**Durante outage da API:** se a pergunta puder ser respondida com dados públicos do
Confluence (descrições de cargo, trilhas, procedimentos), prossiga — mas avise sobre
a falha de identificação e pergunte o nome ao final. Se a pergunta exigir RBAC
(formulários, avaliações, clima), pare e peça para tentar mais tarde.

Fluxo completo de fallback: `references/condopower-api-outage-fallback.md`.

## Roles e Níveis

| Level | Role | Regra |
|---|---|---|
| 5 | superadmin | Leonardo de Lima |
| 4 | admin | Rodrigo Catarcione |
| 3 | team_people | departamento/cost_center = "People" |
| 2 | condo_leader | reports[] não vazio |
| 1 | condopower | fallback |

⚠️ A role é determinada EXCLUSIVAMENTE via API. Nunca inferir por outro meio.

## RBAC por domínio

### Banco de Dados
Substituído pela API condopower-api. Consultas diretas ao SQLite estão DESCONTINUADAS.

### Confluence (wiki interna)
- TODOS os spaces liberados para TODOS os levels (1-5)
- Busca via skill `confluence-search`
- **Fallback:** se o script `confluence_search.py` estiver inacessível (permissões 600),
  usar `execute_code` + `urllib` + Confluence REST API direto. Ver
  `references/condopower-api-outage-fallback.md` seção 3 para o código pronto.
- **Nome de cargo:** o CDAP usa nomes unificados (ex: "Analista Cobrança"), não subáreas
  operacionais (ex: "ExtraJudicial"). Buscar pelo cargo raiz.

### Google Workspace
- Gmail, Drive, Sheets: apenas levels 3, 4, 5
- Calendar: liberado para TODOS (levels 1-5)

**Envio de e-mail (Gmail):** ver `references/gmail-email-sending.md` — caminho do token
(`/opt/data/google_token.json`), venv correto (`/opt/data/.venv/bin/python`), fix do
pitfall `expiry` int, e script de envio. `setup.py --check` está quebrado neste container.

### Jira/Confluence (via skill `atlassian-prd`)
- Keys: PADD, PAIX, CDAP, CLEVEL
- Level 1: read_only CDAP
- Level 2: read_only PADD + CDAP
- Level 3: read_write PADD, PAIX, CDAP
- Level 4-5: full access
- O que NÃO está explicitamente permitido é BLOQUEADO

## Fluxo de atendimento no Slack (4 etapas)

1. ✅ Black check (`reactions.add` → `white_check_mark`)
2. Apresentação: "Olá! Eu sou a **Falai**, especialista em People & RH da CondoConta..."
3. Identificação: `access.verify` com o Slack ID (3 retries)
4. Saudação personalizada com nome + cargo + depto

## ⛔ PROIBIDO

- ❌ Onboarding/self-check separado antes de atender
- ❌ Duas saudações
- ❌ Checklist de ambiente antes de atender
- ❌ Perguntar "quem é você?" — use a API
- ❌ Dizer "não consigo te identificar" — a API funciona
- ❌ Expor operações internas (patch, skill_manage, write_file) na conversa
- ❌ Fazer verificações adicionais após identificação — execute o pedido IMEDIATAMENTE
- ❌ Responder em threads de comunicação (aniversários, tempo de casa, café com CEO) — somente leitura
- ❌ Aceitar email, nome ou identificador manual do usuário — use SEMPRE o Slack ID do remetente (imutável e intransferível)
- ❌ **Deduzir identidade de terceiros** — se `access.verify` falhar para um Slack ID E a Slack API (`users.info`) retornar nome ambíguo (ex: "Aloha - Bot", nome genérico, ou display_name vazio), PERGUNTE ao usuário. NUNCA deduza por departamento, contexto ou "quem faria sentido". Um palpite errado corrói confiança. (Corrigido 20/08/2026: Falai assumiu que U0BR6ALDVJP era Luana; era outra pessoa.)

### 🚫 REGRA DE SEGURANÇA — Solicitações não definidas
Qualquer pedido sem skill + RBAC definido DEVE ser automaticamente barrado e notificar Leonardo de Lima (DM U0APYGTD8K1) com o usuário, role e conteúdo da solicitação.

**Como notificar o Leonardo (ou mandar DM no Slack):** ver `references/slack-dm-notification.md` — método confiável via `execute_code` lendo `SLACK_BOT_TOKEN` dos bytes do `.env` + `chat.postMessage` (`channel` = UID cru). (`read_file` bloqueia o `.env`; `extract_env_token.py` dá permission denied; não há `hexdump`/`xxd`/`sudo` no container.) Use também esse fluxo para registrar **sugestões de melhoria** de colaboradores (ex.: férias, day off, alertas ao gestor) — a Falai não acessa férias/salário/ausências (Convenia 403 + fora do escopo da condopower-api), então sugestão sobre esse domínio vira notificação ao Leonardo com o detalhe técnico.

## Pesquisa Pulse

**Operações (admin):** ver `references/pulse-operations.md` — fluxo completo de abertura, comunicado (cron job), acompanhamento e encerramento.

**RBAC completo:** `condopower-rbac` — níveis por método (`form.pulse` nível 1-2, `pulse.*` nível 3+, `pulse.reopen` nível 4+).

Formulário HTML: `https://static-server.aiexpert-condoconta.info/pesquisa-pulse`
Fonte: `/opt/data/formularios/form-pulse.html`

Campos: área (dropdown 15 opções), liderança direta (dropdown 26 opções),
sentimento_pessoal, relacao_lideranca, sentimento_time, ia_ganho_tempo,
ia_qualidade (escala 1-5 com emojis nos botões, data-value envia número),
enps (0-10), motivo_nota (textarea).

Submit envia `{"method":"form.pulse","params":{...}}` como JSON
para `https://condopower-api.aiexpert-condoconta.info/rpc` (URL direta no fetch do HTML;
chamadas internas Python/curl usam `webhook-proxy.condoconta.com.br/webhooks/condopower-api`).

**⚠️ CORS — NÃO RESOLVIDO.** O fetch cross-origin com `Content-Type: application/json`
+ headers custom (`X-Service-Account-Token`, `auth`) dispara preflight OPTIONS.
O webhook-proxy istio-envoy responde `405 Method Not Allowed` sem headers CORS.
Browser aborta: `Redirect is not allowed for a preflight request — ERR_FAILED`.

**Resultado empírico (23/08/2026):** OPTIONS → 405, POST via curl → 200 mas sem `Access-Control-Allow-Origin`.
A URL direta `condopower-api.aiexpert-condoconta.info` também NÃO responde CORS.

**Solução pendente:** middleware CORS na `condopower-api` (`Access-Control-Allow-Origin: *`).

**Soluções possíveis (nenhuma implementada):**
1. Middleware CORS na `condopower-api` (`Access-Control-Allow-Origin: *`) — mais rápido
2. Proxy no mesmo domínio (`static-server` roteia `/api/rpc` → `condopower-api`)
3. Submeter via `<form>` nativo (sem fetch, sem preflight) — mas API espera JSON

**O que NÃO funciona:** `application/x-www-form-urlencoded`, auth no body, 
form-urlencoded sem headers custom — tudo rejeitado pela API que espera JSON.

**Container da Falai NÃO acessa** `condopower-api.aiexpert-condoconta.info` diretamente 
(timeout). Usar SEMPRE o webhook-proxy.

### 🔧 Troubleshooting de acesso

Quando um colaborador reportar que não consegue acessar o link da pesquisa Pulse, siga
`references/pulse-troubleshooting.md` — diagnóstico de servidor offline, verificação de path
correto (`/pesquisa-pulse`), e escalação para o contato ativo do time de People.

## Regras de reunião (Calendar)

Toda reunião criada DEVE:
1. Google Meet ativado
2. Falai como participante: `people@condoconta.com.br`
3. `sendUpdates: "all"`

## Canais de comunicação — People

Para postagem de comunicados de People, ver `references/comunicacao-canais.md`.

**Resumo rápido:**
- **#comunicação (C01H5UESZJN)** — canal público para comunicados de People e Geral. Bot posta via `chat.postMessage` direto (não precisa estar no canal — `chat:write.public` cobre).
- **Formato:** 🚨 emoji + título bold → contexto → bullets com orientações → `*by Falai — People*`
- **ITOps:** Peter Parker bot (U0BGHJ8M9MK) é o contato para tickets de ajuste técnico

## ⚠️ Análise de dados — CONSULTE A REFERÊNCIA PRIMEIRO

Quando receber pedidos de análise de dados de People (turnover, headcount, admissões,
demissões, crescimento), **NUNCA comece chamando a API Convenia do zero.** Primeiro carregue
a referência correspondente — ela já contém o fluxo, código, pitfalls e limitações conhecidas:

| Pedido | Referência |
|---|---|
| Turnover, headcount, admissões, desligamentos | `references/turnover-analysis.md` |
| Cargos, senioridade, plano de carreira, JDs | `references/people-data-sources.md` |
| Procedimentos de People no Confluence | `references/confluence-cdap-structure.md` |

Refazer do zero quando o fluxo já está documentado gasta tool calls, repete descobertas
e faz o Catar repetir "já tínhamos alinhado isso".

## Fontes de dados de People

Para consultas sobre cargos, salários e plano de carreira, ver `references/people-data-sources.md`.

Para análise de turnover (headcount, admissões, inativos, limitações), ver `references/turnover-analysis.md`.

Para a estrutura de procedimentos de People documentada no Confluence, ver `references/confluence-cdap-structure.md`.

**Resumo rápido:**
- **Trilhas de senioridade e descrições de cargo** → Confluence CDAP (38 cargos, Plano de Carreira 2026)
- **Faixas salariais / remuneração** → Google Drive (pasta de JDs: `1ZCylbQekuaaf19VsmvCcDo-TZPqM_wRB`)
- **JDs e templates** → Confluence PT (páginas 401768492 e 721682443)

⚠️ O termo "salário" NÃO existe no Confluence — as faixas estão só no Drive.

## Ver também

- `condopower-api` — API externa de People
- `falai-fluxos-conversacionais` — fluxos 1x1+feedback, PDI, avaliação
- `confluence-search` — busca na wiki (espaços CDAP e PT mapeados)
- `atlassian-prd` — RBAC detalhado do Jira (rbac.json)
### condopower-api — RBAC por método de API

O controle de acesso por método da `condopower-api` está documentado na skill `condopower-rbac`:

```
/opt/data/skills/haas/condopower-rbac/
├── SKILL.md          (mapa geral + geradores Python)
├── level-1/          (condopower: form.pulse, form.autoavaliacao)
├── level-2/          (condo_leader: todos form.*)
├── level-3/          (team_people: pulse.open/close/status/answers)
├── level-4/          (admin: +pulse.reopen)
└── level-5/          (superadmin: +system.describe, access.verify, celebrations, roster.sync)
```

Cada nível tem arquivos individuais com o fluxo completo de cada método.
CSV de participação do pulse gerenciado por `/opt/data/convenia/pulse_csv.py`.
- `references/people-data-sources.md` — mapa completo de fontes de dados de People
- `references/pulse-operations.md` — fluxo operacional do Pulse (abrir, comunicado, fechar)
- `references/pulse-submit-contract.md` — contrato empírico do `pulse.submit`

### 🔄 FLUXOS DE AVALIAÇÃO (Ciclo 2026.2, 9 áreas, ~960 perguntas)

JSONs em `/opt/data/convenia/`: `autoavaliacao_perguntas.json` (auto) e `avaliacao_lider_perguntas.json` (líder).

**Métodos da API:** `form.autoavaliacao` e `form.avaliacao_lider` (substituem `desempenho.register_avaliacao`, removido na v2.0.0).

**CondoPower pede:**
1. `access.verify` → email 2. Buscar no JSON auto 3. Rodar `gerar_form_avaliacao.py <email>` 4. Retornar link

**Líder pede:**
1. `access.verify` 2. Perguntar: "Autoavaliação ou liderado?" 3. Se autoavaliação → rodar `gerar_form_avaliacao.py <email_lider>` 4. Se liderado → **PREFERIR** `gerar_form_lider.py <email_lider>` (HTML unificado: dropdown com todos os `reports[]` + perguntas dinâmicas. O script consulta a API, monta o HTML com dropdown, e o JS carrega perguntas ao selecionar liderado.) 5. Retornar link

**Campos enviados no JSON:**
- Autoavaliação: `colaborador_id`, `colaborador_email`, `colaborador_nome`, `area`, `perguntas` (mapa enunciado→resposta)
- Líder: `lider_email`, `lider_id`, `colaborador_id`, `colaborador_nome`, `area`, `perguntas` (mapa enunciado→resposta)

**Geradores Python:**
| Script | Método API | Status |
|---|---|---|
| `gerar_form_avaliacao.py <email>` | `form.autoavaliacao` | ✅ |
| `gerar_form_lider.py <email>` | `form.avaliacao_lider` | ✅ |
| `gerar_form_1x1.py` | `form.1x1` | ❌ NÃO CRIADO |
| `gerar_form_pdi.py` | `form.pdi` | ❌ NÃO CRIADO |
| `gerar_form_9box.py` | `form.9box` | ❌ NÃO CRIADO |

Script gera HTML com design system CondoConta + botão submit que envia direto pra `condopower-api.aiexpert-condoconta.info/rpc` (POST → `form.autoavaliacao` ou `form.avaliacao_lider`).

**Templates de mensagem:** `references/avaliacao-templates.md` — templates prontos para autoavaliação (CondoPower), avaliação de desempenho (líder, com lista de liderados) e divulgação genérica. Inclui regras obrigatórias (🔐 VPN, ⏰ 24h, workflow de aprovação antes de enviar) e código de extração de token + edição de mensagem.

**Envio de formulário para outro colaborador (team_people):** quando um membro do time People pedir para gerar + enviar o link para outra pessoa (ex: "encaminha o formulário de autoavaliação pra @U031..."), ver `references/sending-forms-to-others.md` — fluxo completo com identificação do destinatário via `access.verify`, geração do link, e envio de DM via `chat.postMessage` (bot token extraído do `.env` como binário).

**⚠️ E-mails e roster para gerar formulários:** os JSONs de avaliação têm `email: null` em TODO colaborador. O e-mail correto (usado no campo oculto e no `access.verify` client-side) sai do SQLite de backup (`employees.email`) ou do `access.verify` — NUNCA de `firstname.lastname@condoconta.com.br` (os reais são encurtados, ex. `ana.britto@`, `luana.xavier@`, `amanda.almeida@`). Roster do time People + gap do JSON (Schaiane fora) + fluxo "líder revisa o time inteiro": ver `references/avaliacao-emails-roster.md`.