# Level 4 — Admin

Nível de acesso: **4**
Role: `admin`
Alcança: tudo

## Métodos permitidos

### Herdados de todos os níveis
| Nível | Métodos |
|---|---|
| 1 | `form.pulse`, `form.autoavaliacao` |
| 2 | `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box` |
| 3 | `pulse.open_round`, `pulse.close_round`, `pulse.round_status`, `pulse.answers` |

### Exclusivo do level 4
| Método | Arquivo |
|---|---|
| `pulse.reopen` | [pulse-reopen.md](pulse-reopen.md) |

## Métodos NÃO permitidos
- `system.describe`, `access.verify`, `celebrations.*`, `roster.sync` — exclusivos level 5