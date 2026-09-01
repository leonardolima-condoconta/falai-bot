# Estrutura RBAC — um arquivo por nível

O usuário determinou que cada nível deve ter um único arquivo `permissions.md` contendo:
- Todos os métodos permitidos com fluxo completo
- Tabela de métodos bloqueados com nível mínimo

Arquivos criados em `skills/haas/condopower-rbac/`:
- `level-1/permissions.md` — form.pulse, form.autoavaliacao
- `level-2/permissions.md` — todos form.*
- `level-3/permissions.md` — pulse.*, form.*.get
- `level-4/permissions.md` — pulse.reopen
- `level-5/permissions.md` — system.describe, access.verify, celebrations.*, roster.sync

## Fluxos por formulário

### Pulses
- Link: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
- `max-age=864000` (10 dias)
- 8 campos obrigatórios + 1 opcional (comentário)

### Autoavaliação
- `colaborador_id` resolvido client-side via `/proxy`
- Todas as perguntas obrigatórias

### Avaliação do Líder
- Dropdown com liderados
- Cookie `avaliacao_lider_feitos` → JSON array de UUIDs
- Após avaliar: remove do dropdown, reseta form
- Última pergunta (Recomendação) removida

### 1x1
- Autoavaliação � + Líder� lado a lado
- 9box à direita + PDI abaixo
- Submit envia: `form.1x1` + `form.9box` + `form.pdi`