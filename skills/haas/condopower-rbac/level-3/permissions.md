# Level 3 — Team People

Nível de acesso: **3**
Role: `team_people`
Alcança: tudo (administra clima, lê todos os formulários)

## Métodos — lista completa

| # | Método | Status |
|---|---|---|
| 1 | `form.pulse` | ✅ Permitido |
| 2 | `form.autoavaliacao` | ✅ Permitido |
| 3 | `form.avaliacao_lider` | 🚫 Bloqueado (requer level 2 — líder) |
| 4 | `form.1x1` | 🚫 Bloqueado (requer level 2 — líder) |
| 5 | `form.pdi` | 🚫 Bloqueado (requer level 2 — líder) |
| 6 | `form.9box` | 🚫 Bloqueado (requer level 2 — líder) |
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
| 17 | `pulse.reopen` | 🚫 Bloqueado (requer level 4) |
| 18 | `system.describe` | 🚫 Bloqueado (requer level 5) |
| 19 | `access.verify` | 🚫 Bloqueado (sistema/crons) |
| 20 | `celebrations.birthdays` | 🚫 Bloqueado (sistema/crons) |
| 21 | `celebrations.work_anniversaries` | 🚫 Bloqueado (sistema/crons) |
| 22 | `roster.sync` | 🚫 Bloqueado (requer level 5) |

## Fluxo dos métodos permitidos

### form.pulse + form.autoavaliacao
Mesmo fluxo do level 1.

### form.*.get — Leitura de formulários (6 métodos)
Coletar email/área → resolver `colaborador_id` via `access.verify` → chamar API com `requester_email` + filtros.

### pulse.open_round
Pedir ano, mês, início, fim (uma vez) → chamar API → criar CSV em `$PULSE_PATH_USERS`.

### pulse.close_round
Confirmar criticidade → chamar API → exportar CSV para Slack #people-hr → excluir CSV → limpar `$PULSE_PATH_USERS`.

### pulse.round_status
Pedir ano/mês (opcional) → chamar API → formatar tabela.

### pulse.answers
Pedir ano/mês (opcional) → chamar API → agrupar por pergunta. ⚠️ Não expor texto livre em times pequenos.