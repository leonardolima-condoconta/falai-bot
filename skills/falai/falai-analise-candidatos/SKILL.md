---
name: falai-analise-candidatos
description: Analise candidatos InHire. Knockout, matriz, recomendacao.
version: 1.0.0
---

# Falai — Análise de Candidatos (InHire)

Fluxo completo para análise de pessoas candidatas do InHire contra a descrição da vaga.
Formato padrão usado pelo time People CondoConta.

## Gatilhos

- "analisar candidato", "analisar essa candidatura", "o que essa candidata tem para a vaga"
- "fazer a análise de sempre"
- Qualquer URL do InHire com `?card=` (card de candidato)
- "quantos candidatos", "contar candidatos", "candidatos na vaga", "quantos se inscreveram"
- "localizar vaga", "vaga de [nome]"

## ⛔ REGRA DE AMOSTRA — OBRIGATÓRIO

**NUNCA apresente um "top N" ou ranking comparativo com menos de 5 candidatos analisados.**

Se você só analisou 2 candidatos, você NÃO tem um top 5. Você tem uma amostra inicial.
Seja transparente: "Analisei X de Y candidatos ativos. Aqui está o que encontrei ATÉ AGORA."

Um "top" é um ranking com pretensão de representatividade. Só existe após analisar
no mínimo 5 candidatos (e idealmente passando pelas páginas 2+ quando houver).

⚠️ NÃO confunda "etapa avançada no pipeline" com "melhor candidata". Uma candidata
que passou pelo screening NÃO é automaticamente a melhor — avalie pelo CV, não pela
coluna do Kanban. Se a única pessoa em etapa avançada for analisada primeiro, isso
é logística, não mérito. Deixe isso EXPLÍCITO na análise.

Corrigido por Rodrigo Catarcione em 20/08/2026.

## Fluxo (6 etapas)

### 1. Coletar descrição da vaga

Navegar até a URL pública da vaga (sem `?card=`):
`https://condoconta.inhire.app/vagas/<job-id>/<slug>`

Extrair com `browser_console` → `document.body.innerText`.
A página da vaga é pública — não requer login.

**O que extrair:**
- Título e nível da vaga
- Atividades principais
- Requisitos mandatórios
- Diferenciais
- Localização e modelo (presencial/remoto/híbrido)

### 2. Autenticar no InHire

Se o card de candidato redirecionar para `/login`:

1. Navegar para `https://condoconta.inhire.app/login`
2. Preencher email (`browser_type` no campo "Email *")
3. Preencher senha (`browser_type` no campo "Senha *")
4. Clicar "Acessar conta"
5. Confirmar login: snapshot deve mostrar "Olá, [Nome]!"

**Credenciais:** solicitar ao usuário se não estiverem no `.env`.
Não há segredo armazenado atualmente no Infisical nem no `.env`.

⛔ **NUNCA divulgar senhas ou credenciais** no texto visível da conversa.
Senhas são usadas APENAS em background (autenticação em sistemas) sem eco.
Se precisar digitar senha num formulário, use `browser_type` ou preencha via JS —
nunca mostre a senha na resposta. Regra reiterada por Rodrigo Catarcione em 18/08/2026.

### API Auth (alternativa ao browser)

Endpoint de autenticação: `POST https://auth.inhire.app/login`
Headers obrigatórios: `Content-Type: application/json`, `X-Tenant: condoconta`
Body: `{"email":"...", "password":"..."}`
Retorna: `{"accessToken": "...", "refreshToken": "..."}`
Token é JWT com `iss: "auth.inhire.app"`, `tenantId: "condoconta"`.

⚠️ A API REST (`api.inhire.app`) retorna 403 mesmo com token válido —
a SPA usa um mecanismo adicional (possivelmente cookie de sessão ou
header customizado). O browser com sessão ativa é mais confiável que curl.

### 3. Acessar card da candidata

Após login, navegar direto para a URL do card:
`https://condoconta.inhire.app/jobs/<job-id>?card=<card-id>`

Se o snapshot vier incompleto (SPA), usar `browser_console`:
```
document.body.innerText
```

Isso retorna TODO o conteúdo visível: dados cadastrais, currículo, etapa no funil,
pretensão salarial, localização, disponibilidade presencial, etc.

### 4. Extrair dados relevantes

Do card da candidata:
- Nome completo
- Localização (cidade/estado)
- Pretensão salarial
- Disponibilidade presencial (SIM/NÃO) ← **KNOCKOUT mais comum**
- Etapa atual no funil
- Fonte (LinkedIn, Indeed, etc.)
- Tempo na etapa (dias)
- Experiências profissionais (empresa, cargo, período, responsabilidades)
- Formação acadêmica
- Habilidades e ferramentas
- Certificações
- Idiomas

### 5. Montar a matriz de análise

Formato padrão:

```
🔴 KNOCKOUT — Atenção imediata
(tabela: critério | vaga exige | candidata | status)

✅ Pontos Fortes
(numeração, cada ponto com evidência do CV)

🟡 Pontos de Atenção
(tabela: aspecto | observação)

📋 Resumo da Matriz
(tabela: dimensão | nota 1-5 | peso)

🎯 Recomendação
(aprovar/reprovar/avançar com ressalva + justificativa)
```

### 6. Critérios de knockout (sempre verificar primeiro)

| Knockout | Como verificar |
|---|---|
| Disponibilidade presencial | Campo "Disposto(a) a trabalhar no modelo presencial em Florianópolis?" |
| Localização inviável | Cidade/estado vs. exigência da vaga |
| Pretensão fora da faixa | "Pretensão salarial" vs. budget da vaga |
| Formação obrigatória | Requisitos de curso superior vs. formação da candidata |

⚠️ Se um knockout for detectado, a recomendação é **reprovar**, mas SEMPRE
mencionar se há candidatos em etapas mais avançadas que podem ser priorizados.

## Localizar vaga e contar candidatos (job lookup)

Além de analisar um card individual, é comum precisar localizar uma vaga pelo nome
e contar quantos candidatos se inscreveram.

### Pelo Dashboard (Home)

Após login, a Home (`/`) mostra a tabela "Minhas vagas" com:
`ID`, `Nome da Vaga`, `Talentos Ativos`, `Posições Abertas`, `Área da vaga`.

O ID aparece truncado (ex: `d337e1`). Para obter o UUID completo, clique na vaga
ou extraia o `href` do link via `document.querySelector`.

Use `document.body.innerText` — a SPA não renderiza bem no `browser_snapshot`.

### Pela página da vaga (`/jobs/<uuid>`)

`document.body.innerText` retorna o resumo do pipeline:

```
Talentos na vaga
<total>
Ativos  <N>  Desistentes <N>  Reprovados <N>  Hunting <N>
```

E contagem por etapa: `Inscrição <N>`, `Qualificados <N>`, `Screening <N>`, etc.

**Regras de interpretação:**
- "Talentos na vaga" = total de candidaturas = Ativos + Reprovados + Desistentes + Hunting
- "Ativos" = candidatos ainda no pipeline (não reprovados/desistentes). Cada etapa mostra a contagem de ativos nela.
- "Posições Abertas: 0" **NÃO** significa que a vaga está fechada — verifique o label `Aberta`/`Fechada`.
- Para "quantos se inscreveram", use o total de **Talentos na vaga**.

### Exemplo real (14/08/2026)

Vaga "HR Business Partner" (`d337e149-54e5-4a84-b378-b83dd849bbb3`):
- Dashboard: Talentos Ativos 26, Posições Abertas 0
- Página da vaga: **61** candidaturas totais (26 ativos + 35 reprovados)
- Pipeline: 26 na etapa Inscrição, 0 nas demais

## Navegação no pipeline (lista de candidatos)

### Escolha da visualização: use Lista, NÃO Kanban

Na página da vaga (`/jobs/<uuid>`), há dois modos: **Lista** e **Kanban**.

- **Lista** (`e22`): tabela com nome, empresa, fonte, data, etapa. Botões e links são
  elementos HTML distintos e confiáveis. **SEMPRE use este modo.**
- **Kanban** (`e23`): colunas arrastáveis. Cliques em cards NÃO são confiáveis —
  o `browser_click` pode não registrar. **NUNCA use para abrir cards.**

Para alternar: clique em "Lista" no toggle acima da tabela.

### Abrindo o card de um candidato: clique no BOTÃO, não no link

Cada linha da lista tem DOIS elementos clicáveis com o nome:
- `<button>` — botão com nome + ícone de expandir → **abre o card no InHire** ✅
- `<a>` (link) — link para o perfil do LinkedIn → **redireciona para linkedin.com** ❌

No `browser_snapshot`, o botão aparece como `button "Nome Candidato" [ref=eXX]`
e o link como `link "Nome Candidato" [ref=eYY]`. **SEMPRE clique no button, NUNCA no link.**

Exemplo no snapshot:
```
button "Laura Schmidt de Oliveira" [ref=e87]   ← CLIQUE AQUI
link "Laura Schmidt de Oliveira" [ref=e88]      ← EVITE (abre LinkedIn)
```

### Busca por nome para isolar candidato

Use o campo de busca (`textbox "Digite para buscar..."`) para isolar um candidato
específico. Após digitar e pressionar Enter, a lista filtra e mostra apenas o match.
Isso facilita encontrar o botão correto sem scroll horizontal no Kanban.

Após analisar, limpe a busca ou re-navegue para `/jobs/<uuid>` para ver a lista completa.

### Sessão expira durante análise longa

A sessão do InHire expira após ~10-15 minutos de inatividade do browser.
Se a página redirecionar para `/login`:

1. Refaça login (email + senha) — as credenciais continuam válidas
2. Navegue de volta para `/jobs/<uuid>`
3. Retome de onde parou — os dados dos cards já extraídos estão salvos na conversa

Para análises com muitos candidatos, priorize extrair os dados de cada card
imediatamente (não acumule navegação antes de extrair).

## Dicas

- O InHire é uma SPA React — o `browser_snapshot` pode vir vazio ou incompleto.
  Nesses casos, `browser_console` com `document.body.innerText` é mais confiável.
- A página de vaga é pública e carrega mesmo sem login.
- O card de candidato exige autenticação.
- Se o browser redirecionar para login, é só logar e re-navegar para a URL do card.
- SEMPRE começar pelo knockout — se a pessoa não pode trabalhar presencial e a vaga exige,
  não faz sentido analisar o resto (mas faça mesmo assim, para o registro).
- Para análises com muitos candidatos (15+), priorize qualidade sobre quantidade:
  analise os mais avançados no funil + os 3-4 mais recentes da Inscrição.
- Após abrir um card, EXTRAIA IMEDIATAMENTE os dados com `document.body.innerText`
  antes de navegar para outro — os dados extraídos persistem na conversa.
- ⛔ **TRANSPARÊNCIA:** Sempre informe quantos candidatos foram analisados vs. total
  de ativos. Ex: "Analisei 4 dos 28 candidatos ativos." NUNCA insinue que uma análise
  parcial é completa.
- ⛔ **VIÉS DE PIPELINE:** Não ranqueie candidatas pelo estágio no funil. Uma pessoa
  em "Bate-papo com People" não é objetivamente melhor que uma em "Inscrição" —
  ela só foi triada antes. O ranking deve vir da análise do CV, não da coluna.
- **Extração de dados do painel:** Ao clicar no botão do candidato na Lista, o painel
  lateral abre e `document.body.innerText` concatena lista + painel. Os dados do painel
  SEMPRE vêm depois do marcador de paginação (`"1 a 10 de 120 itens"`). Use
  `body.split('1 a 10 de ...')` para isolar o conteúdo — veja `references/panel-extraction-patterns.md`.
- **Prioridade de entrega:** Se o usuário pedir "um doc" ou "o documento", priorize
  GERAR o entregável com os dados já coletados em vez de continuar extraindo
  candidatos indefinidamente. Inclua sempre a % de cobertura da amostra e recomende
  export CSV do InHire para análise completa.

## 📐 Formato Executivo — Visão de Diretoria (Rodrigo Catarcione)

Rodrigo Catarcione usa estas análises para **tomar decisões de contratação**.
Ele espera insumo executivo, não apenas dados brutos. Toda entrega DEVE:

1. **Matriz comparativa** — tabela com TODAS as candidatas analisadas lado a lado,
   cada dimensão com nota 1-5. Sem matriz = análise incompleta.
2. **Recomendações estratégicas** — \"contratar\", \"avançar para entrevista\",
   \"qualificar com ressalva\", \"reprovar\". Com justificativa clara para cada uma.
3. **Próximos passos sugeridos** — ações concretas (mover etapa, agendar conversa,
   pedir mais informações). Ele não quer decidir o passo a passo, quer opções.
4. **Visão de pipeline** — contextualizar cada candidata no funil geral:
   quantas estão em cada etapa, se há gargalos, se o volume é saudável.
5. **Custo-benefício** — pretensão salarial é critério de decisão. Ranking
   NÃO é só fit técnico; inclua análise de quanto cada uma custa.

⚠️ Essa preferência foi reiterada em 20/08/2026: \"análises completas com visão
de Diretoria para eu poder tomar decisões.\" Se a entrega não tiver esses 5 elementos,
não está pronta.

## 🚫 NUNCA assuma identidade de Slack ID

Se um usuário pedir para enviar algo para `@UXXXXX` e:
- `access.verify` retornar `EMPLOYEE_NOT_FOUND` para esse ID, **E**
- `users.info` da Slack API retornar nome ambíguo (ex: \"Aloha - Bot\"),

**Pergunte ao usuário quem é.** NUNCA deduza pelo departamento, pelo contexto,
ou por \"quem faria sentido receber isso\". Um palpite errado corrói confiança.

Corrigido por Rodrigo Catarcione em 20/08/2026 (assumi U0BR6ALDVJP = Luana; era outra pessoa).

## Ver também

- `falai-rbac` — identificação e controle de acesso
- `falai-fluxos-conversacionais` — fluxos 1x1, PDI, avaliação
- `references/browser-interaction-pitfalls.md` — button vs link, Kanban, sessão expirando, snapshot vazio
- `references/inhire-access.md` — credenciais e acesso ao InHire
- `references/job-lookup-pitfalls.md` — pitfalls de contagem de candidatos
- `references/panel-extraction-patterns.md` — extração de dados do painel lateral via split de paginação