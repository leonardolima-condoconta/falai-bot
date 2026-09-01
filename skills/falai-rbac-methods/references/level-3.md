# Level 3 — team_people

Acesso a tudo (departamento ou centro de custo = People). Administra a pesquisa de clima.

## Métodos habilitados

### form.pulse (herdado do level 1)

Mesmo fluxo do level 1.

### form.autoavaliacao (herdado do level 1)

Mesmo fluxo do level 1.

### ⚠️ Métodos do level 2 NÃO são herdados

`form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box` são exclusivos do level 2 e level 4+.

### pulse.open_round

**Fluxo:**
1. Exigir TODOS os parâmetros de uma única vez: `requester_email`, `ano`, `mes`, `inicio`, `fim`, `observacao` (opcional).
2. Solicitar ao servidor via POST `/rpc`.
3. Criar CSV temporário em `$PULSE_PATH_USERS` com colunas: `id_usuario, respondido, created_at`.
4. Salvar o path em variável de ambiente.

**Atenção:** Só existe uma rodada por mês. Repetir devolve `409 ROUND_ALREADY_EXISTS`.

### pulse.close_round

**Fluxo:**
1. Exigir `requester_email`. Sem `ano`/`mes`, fecha a rodada aberta hoje.
2. Solicitar ao servidor.
3. Enviar o CSV temporário (`$PULSE_PATH_USERS`) no Slack `#people_hr`.
4. Excluir o arquivo CSV temporário.
5. Limpar a variável: `echo "" > $PULSE_PATH_USERS` (tornar nulo).

### pulse.round_status

**Fluxo:**
1. Exigir `requester_email`.
2. Sem `ano`/`mes`: rodada mais recente. Com `ano`: todas do ano. Com `ano`+`mes`: aquela específica.
3. Solicitar ao servidor.
4. Retornar `competencia`, `aberta`, `convidados`, `responderam`, `faltam`, `adesao_pct`.

**NUNCA tentar obter quem respondeu — a API não expõe.**

### pulse.answers

**Fluxo:**
1. Exigir `requester_email`.
2. Mesmo recorte de `round_status`: sem `ano`/`mes` = mais recente.
3. Solicitar ao servidor.
4. Retornar `respostas[]` com `id`, `created_at` e `raw` (preenchimento original).

**⚠️ Cuidado com anonimato:** em time pequeno, texto livre pode identificar a pessoa. Não repasse `motivo_nota` em recortes pequenos.

## Métodos BLOQUEADOS (explícito)

| Método | Motivo |
|---|---|
| `form.avaliacao_lider` | Exclusivo níveis 2 e 4+ |
| `form.1x1` | Exclusivo níveis 2 e 4+ |
| `form.pdi` | Exclusivo níveis 2 e 4+ |
| `form.9box` | Exclusivo níveis 2 e 4+ |
| `pulse.reopen` | Exclusivo níveis 4+ |
| `access.verify` | Crons e nível 5 |
| `celebrations.*` | Crons e nível 5 |
| `roster.sync` | Crons e nível 5 |
| `system.describe` | Exclusivo nível 5 |