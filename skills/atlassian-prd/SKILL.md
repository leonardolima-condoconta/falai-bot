---
name: atlassian-prd
description: PRD + Jira/Confluence. RBAC obrigatorio via rbac.json.
license: MIT
metadata:
  version: "2.0.0"
---

# Atlassian PRD — RBAC

⚠️ ANTES de qualquer operação no Jira/Confluence, consulte `assets/rbac.json`.

## RBAC — Controle de Acesso Hardcoded

| Level | Role | Keys | Acesso |
|---|---|---|---|
| 5 | superadmin | PADD, PAIX, CDAP, CLEVEL | Full |
| 4 | admin | PADD, PAIX, CDAP, CLEVEL | Full |
| 3 | team_people | PADD, PAIX, CDAP | Read/Write |
| 2 | condo_leader | PADD, CDAP | Read Only |
| 1 | condopower | CDAP | Read Only |

## Regras ABSOLUTAS
- Keys NÃO listadas no nível do usuário → BLOQUEAR
- Operações não permitidas → BLOQUEAR
- O que não está EXPLICITAMENTE permitido é PROIBIDO
- Níveis 1-2: apenas operações read_only
- Nível 3: operações read_write nas keys permitidas
- Níveis 4-5: full access
- deleteProject, createProject, updateProject → BLOQUEADO para todos

## Verificação OBRIGATÓRIA antes de cada operação
1. Consultar `assets/rbac.json`
2. Verificar level do usuário
3. Verificar se a key está nas keys permitidas
4. Verificar se a operação está nas operações permitidas
5. Se NÃO permitido → rejeitar com: "Operação não permitida para seu nível de acesso."

## Modo Análise
1. Extrair → 2. Inferir → 3. Coletar OKR → 4. Validar → 5. Gerar + Tasks → 6. Entregar

## Modo Operação
Fluxo: Backlog → Pronto → Em Andamento → Em Revisão → Concluído