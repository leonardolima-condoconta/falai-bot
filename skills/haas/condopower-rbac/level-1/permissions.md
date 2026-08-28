# Level 1 — CondoPower

Nível de acesso: **1**
Role: `condopower`
Alcança: apenas a si próprio

## Métodos — lista completa

| # | Método | Status |
|---|---|---|
| 1 | `form.pulse` | ✅ Permitido |
| 2 | `form.autoavaliacao` | ✅ Permitido |
| 3 | `form.avaliacao_lider` | 🚫 Bloqueado (requer level 2) |
| 4 | `form.1x1` | 🚫 Bloqueado (requer level 2) |
| 5 | `form.pdi` | 🚫 Bloqueado (requer level 2) |
| 6 | `form.9box` | 🚫 Bloqueado (requer level 2) |
| 7 | `form.autoavaliacao.get` | 🚫 Bloqueado (requer level 3) |
| 8 | `form.avaliacao_lider.get` | 🚫 Bloqueado (requer level 3) |
| 9 | `form.1x1.get` | 🚫 Bloqueado (requer level 3) |
| 10 | `form.pdi.get` | 🚫 Bloqueado (requer level 3) |
| 11 | `form.9box.get` | 🚫 Bloqueado (requer level 3) |
| 12 | `form.pulse.get` | 🚫 Bloqueado (requer level 3) |
| 13 | `pulse.open_round` | 🚫 Bloqueado (requer level 3) |
| 14 | `pulse.close_round` | 🚫 Bloqueado (requer level 3) |
| 15 | `pulse.round_status` | 🚫 Bloqueado (requer level 3) |
| 16 | `pulse.answers` | 🚫 Bloqueado (requer level 3) |
| 17 | `pulse.reopen` | 🚫 Bloqueado (requer level 4) |
| 18 | `system.describe` | 🚫 Bloqueado (requer level 5) |
| 19 | `access.verify` | 🚫 Bloqueado (sistema/crons) |
| 20 | `celebrations.birthdays` | 🚫 Bloqueado (sistema/crons) |
| 21 | `celebrations.work_anniversaries` | 🚫 Bloqueado (sistema/crons) |
| 22 | `roster.sync` | 🚫 Bloqueado (requer level 5) |

## Fluxo dos métodos permitidos

### form.pulse
Pesquisa de clima anônima.

1. Verificar CSV `$PULSE_PATH_USERS` — se usuário já respondeu, informar "já respondeu"
2. Se não respondeu, servir link: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
3. Após submit (via HTML), registrar no CSV: `python3 /opt/data/convenia/pulse_csv.py register <id_usuario>`

**Regras:** NUNCA associar resposta ao usuário (anonimato). CSV registra apenas PARTICIPAÇÃO. Sem `$PULSE_PATH_USERS` → erro.

### form.autoavaliacao
Autoavaliação do colaborador.

1. Validar identidade: `colaborador_id` DEVE ser o do próprio usuário
2. NUNCA gerar HTML para outro colaborador
3. Gerar HTML: `python3 /opt/data/convenia/gerar_form_avaliacao.py <email_do_usuario>`
4. Retornar link do static server