# Turnover via SQLite backups — snapshot diff (método rápido)

Substitui o cross-reference lento (Convenia × condopower-api, ~120 chamadas) descrito em
`references/turnover-analysis.md`. **Use SEMPRE este método primeiro** para turnover,
headcount, admissões e desligamentos.

## Fonte

Backups diários do cadastro em `/opt/data/convenia_data/backups/convenia_YYYY-MM-DD.db`
(~23 snapshots a partir de 28/07). O snapshot mais recente é o estado atual.

Tabelas úteis:
- `employees`: `id, name, last_name, email, birth_date, hiring_date, department_id,
  cost_center_id, job_id, supervisor_id, is_active, synced_at, senioridade,
  nivel_senioridade, cellphone`
- `departments`: `id, name` (JOIN via `employees.department_id`)
- `jobs`, `cost_centers`

Rodar com `/opt/data/.venv/bin/python3` (sqlite3 é stdlib, não precisa de pip).

## O que calcular

1. **Headcount ativo por área** — `COUNT(*) WHERE is_active = 1` agrupado por `departments.name`.
2. **Admissões por mês / por área** — agrupa `hiring_date[:7]` (ano-mês) por departamento.
3. **Desligamentos (data aproximada)** — diff de snapshots consecutivos, cada backup num dict
   `{employee_id: (name, email, is_active, hiring_date, dept)}`:
   - **ID novo** → admissão
   - **ID removido** → desligamento (saiu do cadastro)
   - **`is_active` flip 1→0** → desligamento (data = dia do backup que registrou o flip)
   - **`is_active` flip 0→1** → reativação

O token Convenia (`Falai-Bot`) **não expõe data de desligamento** (HTTP 403). O snapshot diff é
a ÚNICA forma de obter a data aproximada — e cobre só a partir de 28/07/2026.

## Script reutilizável

`scripts/turnover_snapshot_diff.py` — roda o diff completo de uma vez:

```
/opt/data/.venv/bin/python3 skills/haas/falai-rbac/scripts/turnover_snapshot_diff.py
```

Saída: headcount por snapshot (linha do tempo), admissões/desligamentos (diff), headcount ativo
por área, admissões do ano por mês e por área.

## Estado conhecido (19/08/2026)

121 ativos / 122 cadastrados. 1 desligamento detectável no período coberto: Thiago Araujo
(Implantação), marcado inativo em ~04/08.

## Pitfalls

- Colaborador sem email (ex.: Schaiane da Cruz) não passa por `access.verify`, mas aparece
  normalmente no SQLite — o snapshot diff não depende de email.
- Snapshots só a partir de 28/07 — desligamentos anteriores são invisíveis no diff.
- Endpoint condopower-api é SEM sufixo `/rpc` (ver pitfalls de `turnover-analysis.md`).
- `departments.name` = área funcional; 16 áreas (Sales, Engineering, Relacionamento, etc.).
