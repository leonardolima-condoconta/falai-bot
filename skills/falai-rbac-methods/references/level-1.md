# Level 1 — condopower

Acesso restrito ao próprio colaborador. Não pode ver, editar ou consultar dados de outros.

## Métodos habilitados

### form.pulse

**Fluxo:**
1. Verificar se o usuário já consta no CSV temporário (`$PULSE_PATH_USERS`).
2. Se consta → retornar mensagem: "Você já respondeu a pesquisa deste mês. Lembre-se: a pesquisa é anônima."
3. Se não consta → servir o link do formulário pulse: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
4. Registrar no CSV temporário: `id_usuario, respondido=true, created_at=<timestamp>` SOMENTE quando o método é chamado com sucesso.
5. O CSV temporário tem colunas: `id_usuario, respondido, created_at`.

**Validação obrigatória:** SEMPRE consultar o CSV temporário ANTES de servir o link.

**Arquivo gerador de HTML:** `gerar_form_pulse.py` — NÃO EXISTE ainda. O formulário pulse é estático (`/opt/data/formularios/form-pulse.html`).

### form.autoavaliacao

**Fluxo:**
1. Identificar o usuário via `access.verify`.
2. Gerar HTML de autoavaliação SOMENTE para o próprio usuário.
3. `colaborador_id` DEVE ser o `id` retornado por `access.verify.employee.id`.
4. NUNCA gerar HTML de autoavaliação para outro colaborador.
5. Servir o link do HTML gerado.

**Arquivo gerador de HTML:** `/opt/data/convenia/gerar_form_avaliacao.py <email>` ✅

## Métodos BLOQUEADOS (explícito)

| Método | Motivo |
|---|---|
| `form.avaliacao_lider` | Exclusivo níveis 2+ |
| `form.1x1` | Exclusivo níveis 2+ |
| `form.pdi` | Exclusivo níveis 2+ |
| `form.9box` | Exclusivo níveis 2+ |
| `pulse.open_round` | Exclusivo níveis 3+ |
| `pulse.close_round` | Exclusivo níveis 3+ |
| `pulse.round_status` | Exclusivo níveis 3+ |
| `pulse.answers` | Exclusivo níveis 3+ |
| `pulse.reopen` | Exclusivo níveis 4+ |
| `access.verify` | Crons e nível 5 |
| `celebrations.*` | Crons e nível 5 |
| `roster.sync` | Crons e nível 5 |
| `system.describe` | Exclusivo nível 5 |

**Ação ao bloquear:** Notificar superadmin (Leonardo de Lima U0APYGTD8K1) com usuário, role, método solicitado e motivo.