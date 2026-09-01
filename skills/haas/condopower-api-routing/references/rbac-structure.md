# RBAC — Estrutura e decisões

## Arquitetura final (Agosto/2026)

```
condopower-rbac/
├── SKILL.md                              ← mapa geral + geradores Python
├── level-1/permissions.md                ← condopower (22 métodos: 2 ✅, 20 🚫)
├── level-2/permissions.md                ← condo_leader (22: 6 ✅, 16 🚫)
├── level-3/permissions.md                ← team_people (22: 12 ✅, 10 🚫)
├── level-4/permissions.md                ← admin (22: 17 ✅, 5 🚫)
└── level-5/permissions.md                ← superadmin (22: 22 ✅)
```

## Decisão: um arquivo por nível, não um arquivo por método

O RBAC original tinha 5+ arquivos por nível (README.md + blocked-methods.md + um .md por método). Foi consolidado em um único `permissions.md` por nível porque:

1. Cada `permissions.md` lista TODOS os 22 métodos com ✅/🚫 — visão completa sem navegar entre arquivos
2. Métodos permitidos têm fluxo detalhado (passo a passo + comandos)
3. Métodos bloqueados têm o nível mínimo necessário
4. Um arquivo = uma fonte de verdade por nível

## Métodos não cobertos inicialmente

`form.*.get` (6 métodos de leitura) não estavam no RBAC inicial. Adicionados em 27/08/2026:
- Level 1: 🚫 Bloqueado
- Level 2: 🚫 Bloqueado
- Level 3: ✅ Permitido
- Level 4: ✅ Herdado
- Level 5: ✅ Herdado

## Geradores Python pendentes

| Método | Status |
|---|---|
| `form.pdi` | ❌ Gerador não criado |
| `form.9box` | ❌ Gerador não criado |

Quando criados, atualizar a tabela em `SKILL.md`.

## Referência: SOUL.md rules

O SOUL.md define que apenas levels 3+ podem editar skills, crons e comunicados. Isso foi adicionado em 27/08/2026:
```
### 🚫 REGRA DE SEGURANÇA — Edição/criação de skills, fluxos, crons e comunicados
Qualquer solicitação de EDIÇÃO, CRIAÇÃO ou ALTERAÇÃO de skills, fluxos de execução, 
cron jobs e comunicados SÓ pode ser aceita de usuários level 3, 4 ou 5.
```