# Level 2 — condo_leader

Acesso a si e aos seus liderados diretos (validar via `access.verify.reports[]`).

## Métodos habilitados

### form.pulse

Mesmo fluxo do level 1.

### form.autoavaliacao

Mesmo fluxo do level 1 (só gera HTML para si mesmo).

### form.avaliacao_lider

**Fluxo:**
1. Identificar o líder via `access.verify`.
2. Validar que o `colaborador_id` informado está em `reports[]`.
3. Gerar HTML unificado com dropdown de liderados.
4. Servir o link.

**Arquivo gerador de HTML:** `/opt/data/convenia/gerar_form_lider.py <email_lider>` ✅

### form.1x1

**Fluxo:**
1. Identificar o líder via `access.verify`.
2. Coletar campos: `data`, `energia`, `motivacao`, `pauta_liderado`, `acoes_acordadas`, etc.
3. `lider_id` deve vir de `access.verify.employee.id`.
4. `colaborador_id` deve estar em `reports[]`.
5. Chamar `form.1x1` com todos os campos de uma única vez.

**Arquivo gerador de HTML:** NÃO CRIADO AINDA — pendente.

### form.pdi

**Fluxo:**
1. Identificar o líder via `access.verify`.
2. Coletar campos: `competencia_foco`, `gap_evidencia`, `descricao_acao`, `prazo`, etc.
3. `lider_id` deve vir de `access.verify.employee.id`.
4. `colaborador_id` deve estar em `reports[]`.
5. Chamar `form.pdi` com todos os campos de uma única vez.

**Arquivo gerador de HTML:** NÃO CRIADO AINDA — pendente.

### form.9box

**Fluxo:**
1. Identificar o líder via `access.verify`.
2. Coletar campos: `nota_resultados`, `nota_competencias`, `nota_potencial`, `recomendacao`, etc.
3. `lider_id` deve vir de `access.verify.employee.id`.
4. `colaborador_id` deve estar em `reports[]`.
5. Chamar `form.9box` com todos os campos de uma única vez.

**Arquivo gerador de HTML:** NÃO CRIADO AINDA — pendente.

## Métodos BLOQUEADOS (explícito)

| Método | Motivo |
|---|---|
| `pulse.open_round` | Exclusivo níveis 3+ |
| `pulse.close_round` | Exclusivo níveis 3+ |
| `pulse.round_status` | Exclusivo níveis 3+ |
| `pulse.answers` | Exclusivo níveis 3+ |
| `pulse.reopen` | Exclusivo níveis 4+ |
| `access.verify` | Crons e nível 5 |
| `celebrations.*` | Crons e nível 5 |
| `roster.sync` | Crons e nível 5 |
| `system.describe` | Exclusivo nível 5 |