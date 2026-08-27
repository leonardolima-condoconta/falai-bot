# pulse.answers — Level 3

## Pré-condições
- Usuário level 3+ (`team_people`)
- `requester_email` = email do usuário autenticado

## Fluxo

### 1. Coletar parâmetros DE UMA VEZ
```
Para consultar as respostas do pulse, informe (ou deixe em branco para a rodada mais recente):
- Ano (opcional)
- Mês (opcional)
```

### 2. Enviar para API
```json
{
  "method": "pulse.answers",
  "params": { "requester_email": "<email>", "ano": 2026, "mes": 8 }
}
```

### 3. Formatar resposta
Para cada rodada retornada, exibir as respostas agrupadas:

```
📊 *Respostas — Pulse 2026-08*

*Qtd: 37 respostas*

*Sentimento Pessoal:*
╵ 😥 Muito Mal → 1
╵ 😔 Mal → 3
╵ 😐 Neutro → 8
╵ 😁 Bem → 18
╵ 🤩 Muito Bem → 7

*eNPS:*
╵ Promotores: 22 | Neutros: 10 | Detratores: 5
╵ eNPS: 45.9
```

⚠️ **Regra de anonimato:** Em times com menos de 5 pessoas, NÃO exibir texto livre (`motivo_nota`) pois pode identificar o respondente.