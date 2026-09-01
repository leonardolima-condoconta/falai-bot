# Level 5 — superadmin (Leonardo de Lima)

Contempla TODOS os níveis anteriores (1, 2, 3 e 4) + métodos exclusivos.

## Métodos habilitados

### Todos os métodos dos níveis 1-4

Ver referências:
- [level-1.md](level-1.md) — `form.pulse`, `form.autoavaliacao`
- [level-2.md](level-2.md) — `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box`
- [level-3.md](level-3.md) — `pulse.*` (open, close, round_status, answers)
- [level-4.md](level-4.md) — `pulse.reopen`

### system.describe

**Exclusivo do nível 5.**

**Fluxo:**
1. `method_name` é opcional. Sem ele, lista todos os métodos.
2. Solicitar ao servidor.
3. Retornar o JSON Schema de entrada/saída.

**Uso:** Sempre que houver dúvida sobre um contrato de método.

### access.verify

**Exclusivo do nível 5 e dos crons.**

Nível 5 pode consultar a identidade de QUALQUER colaborador (não apenas a própria). Slack ID ou email são aceitos como `identifier`.

### celebrations.birthdays

**Exclusivo dos crons e nível 5.**

Aniversariantes do dia (segunda cobre fim de semana).

### celebrations.work_anniversaries

**Exclusivo dos crons e nível 5.**

Tempo de casa (>1 ano completo).

### roster.sync

**Exclusivo dos crons e nível 5.**

Recarrega cadastro do Convenia. Chamada mais cara do serviço — usar com moderação.

## Nenhum método bloqueado

Level 5 tem acesso TOTAL a todos os métodos da API.