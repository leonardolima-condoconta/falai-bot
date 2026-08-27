# pulse.close_round — Level 3

## Pré-condições
- Usuário level 3+ (`team_people`)
- `requester_email` = email do usuário autenticado
- `$PULSE_PATH_USERS` definido e arquivo CSV existe

## Fluxo

### 1. Confirmar com o usuário
```
Tem certeza que deseja encerrar a rodada atual?
Após o fechamento, novas respostas serão bloqueadas.
```

### 2. Enviar para API
```json
{
  "method": "pulse.close_round",
  "params": { "requester_email": "<email>" }
}
```

### 3. Após sucesso — enviar CSV no Slack (#people-hr)
```bash
python3 /opt/data/convenia/pulse_csv.py export-and-clean
```
O script:
- Lê o CSV de `$PULSE_PATH_USERS`
- Envia o arquivo no canal `#people-hr` (C0BJLA3H16F) via `files.upload` do Slack
- Mensagem: "📊 *Pulse encerrado!* Arquivo de participação anexo."
- Exclui o arquivo CSV
- Define `PULSE_PATH_USERS=""`

### 4. Confirmar ao usuário
```
✅ Rodada encerrada!
- Responderam: X / Y convidados
- Adesão: Z%
- Arquivo de participação enviado no #people-hr
```