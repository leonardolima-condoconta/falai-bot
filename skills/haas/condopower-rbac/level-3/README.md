# Level 3 — Team People

Nível de acesso: **3**
Role: `team_people`
Alcança: tudo (administra clima, vê todos os dados)

## Métodos permitidos

### Herdados do level 1
| Método | Arquivo |
|---|---|
| `form.pulse` | [level-1/form-pulse.md](../level-1/form-pulse.md) |
| `form.autoavaliacao` | [level-1/form-autoavaliacao.md](../level-1/form-autoavaliacao.md) |

### Exclusivos do level 3 (administração de clima e leitura)
| Método | Arquivo |
|---|---|
| `pulse.open_round` | [pulse-open-round.md](pulse-open-round.md) |
| `pulse.close_round` | [pulse-close-round.md](pulse-close-round.md) |
| `pulse.round_status` | [pulse-round-status.md](pulse-round-status.md) |
| `pulse.answers` | [pulse-answers.md](pulse-answers.md) |
| `form.*.get` (6 métodos) | [form-get.md](form-get.md) |

## Métodos NÃO permitidos para level 3
- `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box` — são do level 2 (líderes)
- `pulse.reopen` — requer level 4+
- `system.describe`, `access.verify`, `celebrations.*`, `roster.sync` — level 5