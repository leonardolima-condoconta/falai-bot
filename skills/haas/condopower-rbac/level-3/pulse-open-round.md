# pulse.open_round — Level 3

## Pré-condições
- Usuário level 3+ (`team_people`)
- `requester_email` = email do usuário autenticado

## Fluxo

### 1. Coletar todos os parâmetros DE UMA VEZ
Peça ao usuário (em uma única mensagem, todos os campos):
```
Para abrir a rodada de pulse, preciso de:
- Ano (ex: 2026)
- Mês (ex: 8)
- Data de início (ex: 2026-08-01)
- Data de fim (ex: 2026-08-31)
- Observação (opcional)
```

### 2. Enviar para API
```json
{
  "method": "pulse.open_round",
  "params": {
    "requester_email": "<email>",
    "ano": 2026,
    "mes": 8,
    "inicio": "2026-08-01",
    "fim": "2026-08-31",
    "observacao": "..."
  }
}
```

### 3. Criar CSV temporário
Após sucesso da API:
```bash
python3 /opt/data/convenia/pulse_csv.py create
```
O script:
- Cria arquivo CSV vazio com header: `id_usuario,respondido,created_at`
- Define `PULSE_PATH_USERS` com o path do arquivo
- Exibe o path para o agente registrar

### 4. Confirmar ao usuário
```
✅ Rodada <competencia> aberta!
- Período: <inicio> até <fim>
- Convidados: <convidados>
- CSV de participação criado em: <PULSE_PATH_USERS>
```