# Level 1 — CondoPower

Nível de acesso: **1**
Role: `condopower`
Alcança: apenas a si próprio

## Métodos permitidos

| Método | Arquivo de fluxo |
|---|---|
| `form.pulse` | [form-pulse.md](form-pulse.md) |
| `form.autoavaliacao` | [form-autoavaliacao.md](form-autoavaliacao.md) |

## Métodos BLOQUEADOS

Todos os demais métodos são bloqueados para este nível. Ver [blocked-methods.md](blocked-methods.md).

## Fluxo de entrada

1. Usuário já foi identificado via `access.verify`
2. `level === 1` e `role === "condopower"`
3. Se o método solicitado NÃO está na lista de permitidos → BLOQUEAR
4. Se está na lista → seguir fluxo do arquivo específico