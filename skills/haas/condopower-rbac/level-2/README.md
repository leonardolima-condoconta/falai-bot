# Level 2 — Condo Leader

Nível de acesso: **2**
Role: `condo_leader`
Alcança: a si próprio e seus liderados diretos

## Métodos permitidos

### Herdados do level 1 (mesmo fluxo)
| Método | Arquivo |
|---|---|
| `form.pulse` | [level-1/form-pulse.md](../level-1/form-pulse.md) |
| `form.autoavaliacao` | [level-1/form-autoavaliacao.md](../level-1/form-autoavaliacao.md) |

### Exclusivos do level 2
| Método | Arquivo |
|---|---|
| `form.avaliacao_lider` | [form-avaliacao-lider.md](form-avaliacao-lider.md) |
| `form.1x1` | [form-1x1.md](form-1x1.md) |
| `form.pdi` | [form-pdi.md](form-pdi.md) |
| `form.9box` | [form-9box.md](form-9box.md) |

## Métodos BLOQUEADOS

Todos os métodos administrativos (`pulse.*`, `system.describe`, `access.verify`, `celebrations.*`, `roster.sync`) são bloqueados.

## Regra do líder
- `lider_id` é SEMPRE o id do próprio líder (de `access.verify`)
- `colaborador_id` deve estar em `reports[]` do líder
- Se o `colaborador_id` não pertence aos liderados → BLOQUEAR