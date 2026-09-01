# Como Encontrar o Líder de um Colaborador

## O problema

`access.verify` **não retorna o supervisor** de um colaborador. O campo `reports[]` mostra
quem essa pessoa lidera, não quem a lidera. Não existe método `supervisor.get` ou campo
`supervisor_id` na API.

## O Workaround

Três passos, nesta ordem:

### 1. Match por departamento com a lista de líderes

Consulte o CSV de líderes conhecidos:
`/opt/data/skills/falai-fluxos-conversacionais/references/lideres-slack-ids.csv`

Este CSV mapeia nome, email, Slack ID, cargo e **departamento** de cada líder.

Se o colaborador é de `Banking Operations`, os candidatos a líder naquele departamento são
o ponto de partida (ex: Renata Paim, Treasury Manager).

### 2. Confirme com `access.verify` no candidato

Chame `access.verify` com o e-mail do candidato a líder. Se o colaborador-alvo aparecer
no `reports[]` do candidato, **esse é o líder direto**.

### 3. Se não encontrou nos reports diretos

Se o colaborador não aparece nos `reports[]` de nenhum líder do departamento dele,
pode ser:

- **Liderado indireto** (2 níveis abaixo): para cada `report` do líder candidato, chame
  `access.verify` com o e-mail e inspecione o `reports[]` dele também.
- **Erro de atribuição no Convenia**: notifique o time de People.

## Exemplo real (28/08/2026)

Pergunta: "Quem é o líder do Vito Pacheco?"

1. `access.verify` com `vitor.pacheco@condoconta.com.br` → departamento `Banking Operations`, sem `reports` (nível 1)
2. CSV de líderes → Renata Paim (`renata.paim@condoconta.com.br`) é Treasury Manager de Banking Operations
3. `access.verify` em Renata → `reports[]` inclui `Vitor Pacheco` ✅

## Dica extra: nicknames

Usuários frequentemente usam apelidos ("Vito" em vez de "Vitor"). Quando `access.verify`
retornar `EMPLOYEE_NOT_FOUND`, tente variações comuns antes de desistir:

- Remover/apagar acentos
- Usar o primeiro nome completo em vez do apelido
- Tentar `nome.sobrenome@condoconta.com.br` se tiver o sobrenome

**Nunca** recorra a `roster.sync` só porque um nome não foi encontrado — o sync não resolve
erro de digitação ou apelido.