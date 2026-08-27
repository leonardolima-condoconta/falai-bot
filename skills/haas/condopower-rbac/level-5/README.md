# Level 5 — Superadmin

Nível de acesso: **5**
Role: `superadmin`
Alcança: tudo

## Métodos permitidos

### Herdados de todos os níveis
| Nível | Métodos |
|---|---|
| 1 | `form.pulse`, `form.autoavaliacao` |
| 2 | `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box` |
| 3 | `pulse.open_round`, `pulse.close_round`, `pulse.round_status`, `pulse.answers` |
| 4 | `pulse.reopen` |

### Exclusivos do level 5
| Método | Arquivo |
|---|---|
| `access.verify` | [access-verify.md](access-verify.md) |
| `celebrations.birthdays` | [celebrations-birthdays.md](celebrations-birthdays.md) |
| `celebrations.work_anniversaries` | [celebrations-work-anniversaries.md](celebrations-work-anniversaries.md) |
| `roster.sync` | [roster-sync.md](roster-sync.md) |
| `system.describe` | [system-describe.md](system-describe.md) |

## Nota
- `access.verify` é usado pela Falai na etapa de identificação (mesmo que o usuário seja level 1). A Falai tem nível 5 implícito para sistema.
- `celebrations.*` são usados exclusivamente pelos crons.
- `roster.sync` é acionado manualmente ou pelo cron de sync.