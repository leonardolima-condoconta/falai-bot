# Level 4 — Admin

Nível de acesso: **4**
Role: `admin`
Alcança: tudo

## Métodos — lista completa

| # | Método | Status |
|---|---|---|
| 1 | `form.pulse` | ✅ Permitido |
| 2 | `form.autoavaliacao` | ✅ Permitido |
| 3 | `form.avaliacao_lider` | ✅ Permitido |
| 4 | `form.1x1` | ✅ Permitido |
| 5 | `form.pdi` | ✅ Permitido |
| 6 | `form.9box` | ✅ Permitido |
| 7 | `form.autoavaliacao.get` | ✅ Permitido |
| 8 | `form.avaliacao_lider.get` | ✅ Permitido |
| 9 | `form.1x1.get` | ✅ Permitido |
| 10 | `form.pdi.get` | ✅ Permitido |
| 11 | `form.9box.get` | ✅ Permitido |
| 12 | `form.pulse.get` | ✅ Permitido |
| 13 | `pulse.open_round` | ✅ Permitido |
| 14 | `pulse.close_round` | ✅ Permitido |
| 15 | `pulse.round_status` | ✅ Permitido |
| 16 | `pulse.answers` | ✅ Permitido |
| 17 | `pulse.reopen` | ✅ Permitido (exclusivo) |
| 18 | `system.describe` | 🚫 Bloqueado (requer level 5) |
| 19 | `access.verify` | 🚫 Bloqueado (sistema/crons) |
| 20 | `celebrations.birthdays` | 🚫 Bloqueado (sistema/crons) |
| 21 | `celebrations.work_anniversaries` | 🚫 Bloqueado (sistema/crons) |
| 22 | `roster.sync` | 🚫 Bloqueado (requer level 5) |

## Fluxo adicional

### pulse.reopen (exclusivo)
⚠️ **Método crítico** — reabre rodada encerrada, alterando dados consolidados.

Pedir ano, mês, nova data fim → ALERTAR sobre criticidade → confirmar EXPLICITAMENTE → chamar API.

## Nota
Demais métodos seguem os fluxos dos seus respectivos níveis de origem (1, 2, 3).