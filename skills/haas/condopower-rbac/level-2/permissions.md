# Level 2 — Condo Leader

Nível de acesso: **2**
Role: `condo_leader`
Alcança: a si próprio e seus liderados diretos

## Métodos — lista completa

| # | Método | Status |
|---|---|---|
| 1 | `form.pulse` | ✅ Permitido |
| 2 | `form.autoavaliacao` | ✅ Permitido |
| 3 | `form.avaliacao_lider` | ✅ Permitido |
| 4 | `form.1x1` | ✅ Permitido |
| 5 | `form.pdi` | ✅ Permitido |
| 6 | `form.9box` | ✅ Permitido |
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

### form.pulse (herdado do level 1)
Mesmo fluxo do level 1.

### form.autoavaliacao (herdado do level 1)
Mesmo fluxo do level 1 — gera HTML apenas do próprio líder.

### form.avaliacao_lider
Avaliação dos liderados pelo líder.

1. Verificar `reports[]` — se vazio: "Você não possui liderados diretos"
2. Gerar HTML: `python3 /opt/data/convenia/gerar_form_lider.py <email_lider>`
3. Dropdown com liderados + perguntas dinâmicas
4. Submit → cookie de "já avaliado" + remoção do dropdown
5. Só mostra agradecimento quando todos forem avaliados

**Regra:** `lider_id` é SEMPRE o do próprio líder. `colaborador_id` deve estar em `reports[]`.

### form.1x1
Registro de 1x1 consolidado.

1. Gerar HTML: `python3 /opt/data/convenia/gerar_form_1x1.py <email_lider> <email_colaborador>`
2. Mostra autoavaliação 🟡 + líder 🔵 lado a lado. 9box à direita. PDI abaixo do 9box.
3. Submit envia: `form.1x1` + `form.9box` + `form.pdi`

### form.pdi
Plano de Desenvolvimento Individual.
❌ Gerador Python NÃO CRIADO. Coletar conversacionalmente: competência foco, gap, tipo ação (70-20-10), descrição, prazo, evidência.

### form.9box
Posicionamento no Nine Box.
❌ Gerador Python NÃO CRIADO. Coletar conversacionalmente: nota resultados (1-5), nota potencial (1-5).