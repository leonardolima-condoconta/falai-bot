# Level 4 — admin

Contempla TODOS os níveis anteriores (1, 2 e 3) + `pulse.reopen`.

## Métodos habilitados

### Todos os métodos dos níveis 1, 2 e 3

Ver referências:
- [level-1.md](level-1.md) — `form.pulse`, `form.autoavaliacao`
- [level-2.md](level-2.md) — `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box`
- [level-3.md](level-3.md) — `pulse.open_round`, `pulse.close_round`, `pulse.round_status`, `pulse.answers`

### pulse.reopen

**⚠️ ALERTA DE CRITICIDADE:** Este método altera dados já registrados da pesquisa. ANTES de executar:

1. Informar EXPLICITAMENTE ao usuário:
   - "⚠️ ATENÇÃO: Reabrir uma rodada estende a janela de coleta. Respostas enviadas na extensão são incorporadas à mesma rodada, sem reetiquetagem."
   - "Isso pode alterar a adesão, o eNPS e as métricas do mês."
   - "Confirma que deseja reabrir a rodada?"

2. Só prosseguir com confirmação explícita do usuário.

**Fluxo:**
1. Exigir TODOS os parâmetros: `requester_email`, `ano`, `mes`, `fim`.
2. `fim` é o NOVO prazo final (obrigatório — sem ele a rodada volta com janela no passado).
3. A rodada precisa estar ENCERRADA (`409 ROUND_NOT_CLOSED` se não estiver).
4. Solicitar ao servidor.

## Métodos BLOQUEADOS (explícito)

| Método | Motivo |
|---|---|
| `access.verify` | Crons e nível 5 |
| `celebrations.*` | Crons e nível 5 |
| `roster.sync` | Crons e nível 5 |
| `system.describe` | Exclusivo nível 5 |