# Renomeação de métodos da API — `desempenho.*` → `form.*`

## ⚠️ Discrepância detectada (24/08/2026)

Há inconsistência entre skills sobre o nome dos métodos da `condopower-api`:

| Assunto | Nome antigo (nesta skill + `json-exemplos.md`) | Nome ATUAL (skill `condopower-api`) |
|---|---|---|
| PDI | `desempenho.register_pdi` | `form.pdi` (exige `lider_id`) |
| Autoavaliação | `desempenho.register_avaliacao` | `form.autoavaliacao` (exige `colaborador_id`) |
| Avaliação de liderado | `desempenho.register_avaliacao` | `form.avaliacao_lider` (exige `lider_id`) |
| 1x1 | — (já `form.1x1`) | `form.1x1` |

## Fonte autoritativa

A skill `condopower-api` (v2.0.0, atualizada 2026-08-21) lista os SEIS métodos `form.*`:
`form.pulse`, `form.autoavaliacao`, `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box`.

Ela mesma declara: **"O catálogo é autoritativo, esta skill não"** — em caso de dúvida sobre um
contrato, consultar `system.describe` (devolve o schema real que valida a chamada).

## Onde o nome antigo ainda aparece

- `SKILL.md` (esta skill): "Fluxo PDI" → `desempenho.register_pdi`; JSON de submit da avaliação → `desempenho.register_avaliacao`.
- `references/json-exemplos.md`: payloads de autoavaliação e avaliação do líder usam `desempenho.register_avaliacao`.
- A skill `falai-rbac` já usa a nomenclatura `form.*` (não tem o nome antigo).

## O que fazer

- Ao registrar PDI/avaliação, usar o método `form.*` com o id obrigatório da tabela acima.
- Os campos são LIVRES (sem schema fixo) — a skill `condopower-api`: "Não existe lista fechada de campos".
- Não montar `lider_id`/`colaborador_id` na mão — tirar de `access.verify`.

## Nota sobre o PDI

A API atual (`form.pdi`) exige `lider_id` e aceita campos livres. O roteiro de 8 etapas desta
skill (`competencia_foco`, `gap_evidencia`, `tipo_acao_id`, `descricao_acao`, `prazo`,
`evidencia_conclusao`, `status_id`) é o guia de COLETA da conversa, não um schema rígido.
`colaborador_id` é opcional — mandar quando o PDI for sobre alguém específico.
