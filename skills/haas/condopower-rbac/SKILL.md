---
name: condopower-rbac
description: "RBAC CondoPower: fluxos por nivel de acesso."
version: 1.0.0
---

# CondoPower RBAC — Fluxos por Nível

Mapa de permissão e fluxo para cada método da `condopower-api`.

## Estrutura

```
level-1/   → condopower  (form.pulse, form.autoavaliacao)
level-2/   → condo_leader (todos form.*)
level-3/   → team_people  (form.pulse, pulse.*)
level-4/   → admin        (todos + pulse.reopen)
level-5/   → superadmin   (todos + system.describe, access.verify, celebrations.*, roster.sync)
```

## Regras gerais

1. Sempre identificar o usuário via `access.verify` (nível 5 executa; demais níveis recebem o resultado da identificação)
2. Aplicar o arquivo de fluxo correspondente ao nível
3. Nunca contornar RBAC — bloqueios são EXPLÍCITOS em cada nível
4. CSV temporário de pulse em `$PULSE_PATH_USERS`

## Variáveis de ambiente (obrigatórias)

| Variável | Descrição |
|---|---|
| `PULSE_PATH_USERS` | Caminho do CSV temporário de participação do pulse |

## Arquivos Python geradores de HTML

| Método | Gerador Python | Status |
|---|---|---|
| `form.autoavaliacao` | `gerar_form_avaliacao.py` | ✅ Criado |
| `form.avaliacao_lider` | `gerar_form_lider.py` | ✅ Criado |
| `form.pulse` | `form-pulse.html` (estático) | ✅ Criado |
| `form.1x1` | — | ❌ NÃO CRIADO |
| `form.pdi` | — | ❌ NÃO CRIADO |
| `form.9box` | — | ❌ NÃO CRIADO |