# Métodos BLOQUEADOS — Level 1

Os seguintes métodos NÃO são permitidos para level 1 (condopower).

Se solicitados, responder:
"Esta função não está disponível para o seu nível de acesso. Apenas os níveis indicados podem utilizá-la."

| Método | Nível mínimo | Resposta de bloqueio |
|---|---|---|
| `form.avaliacao_lider` | 2 | Bloqueado — requer level 2+ |
| `form.1x1` | 2 | Bloqueado — requer level 2+ |
| `form.pdi` | 2 | Bloqueado — requer level 2+ |
| `form.9box` | 2 | Bloqueado — requer level 2+ |
| `form.*.get` | 3 | Bloqueado — requer level 3+ (team_people) |
| `pulse.open_round` | 3 | Bloqueado — requer level 3+ (team_people) |
| `pulse.close_round` | 3 | Bloqueado — requer level 3+ (team_people) |
| `pulse.round_status` | 3 | Bloqueado — requer level 3+ (team_people) |
| `pulse.answers` | 3 | Bloqueado — requer level 3+ (team_people) |
| `pulse.reopen` | 4 | Bloqueado — requer level 4+ (admin) |
| `system.describe` | 5 | Bloqueado — requer level 5 (superadmin) |
| `access.verify` | 5 | Bloqueado — interno/crons |
| `celebrations.*` | 5 | Bloqueado — interno/crons |
| `roster.sync` | 5 | Bloqueado — interno/crons |