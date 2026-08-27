# pulse.round_status — Level 3

## Pré-condições
- Usuário level 3+ (`team_people`)
- `requester_email` = email do usuário autenticado

## Fluxo

### 1. Coletar parâmetros DE UMA VEZ
```
Para consultar o status do pulse, informe (ou deixe em branco para a rodada mais recente):
- Ano (opcional)
- Mês (opcional)
```

### 2. Enviar para API
```json
{
  "method": "pulse.round_status",
  "params": { "requester_email": "<email>", "ano": 2026, "mes": 8 }
}
```
Se `ano` e `mes` omitidos → rodada mais recente.

### 3. Formatar resposta
Retornar tabela com todas as rodadas retornadas:

```
📊 *Status das Rodadas Pulse*

| Mês | Período | Aberta | Convidados | Responderam | Adesão |
|---|---|---|---|---|---|
| 2026-08 | 01/08 - 31/08 | ✅ | 121 | 37 | 30.6% |
| 2026-07 | 01/07 - 31/07 | ❌ | 120 | 89 | 74.2% |
```