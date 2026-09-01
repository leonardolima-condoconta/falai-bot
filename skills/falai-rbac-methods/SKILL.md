---
name: falai-rbac-methods
description: "RBAC metodos condopower-api — 1 arquivo por level (1-5)."
version: 1.0.0
---

# RBAC — Métodos condopower-api por nível

Estrutura de permissões para cada método da skill `condopower-api`, organizada por nível de acesso (1-5).

Cada nível tem seu próprio arquivo em `references/`, com:
- Métodos habilitados e fluxo de execução
- Métodos bloqueados (explícito)
- Referência ao gerador de HTML quando aplicável

## Índice por nível

| Nível | Role | Arquivo |
|---|---|---|
| 1 | condopower | [references/level-1.md](references/level-1.md) |
| 2 | condo_leader | [references/level-2.md](references/level-2.md) |
| 3 | team_people | [references/level-3.md](references/level-3.md) |
| 4 | admin | [references/level-4.md](references/level-4.md) |
| 5 | superadmin | [references/level-5.md](references/level-5.md) |

## Regra geral

- `access.verify` é a PRIMEIRA chamada de todo atendimento, SEMPRE.
- Nenhum método aceita Slack ID exceto `access.verify`.
- O nível é determinado EXCLUSIVAMENTE via API.
- O que não está explicitamente permitido é BLOQUEADO.
- Bloqueio deve ser registrado e notificado ao superadmin (Leonardo de Lima).

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `$PULSE_PATH_USERS` | Path do CSV temporário de controle de participação pulse |