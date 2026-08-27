# roster.sync — Level 5 / Crons

## Uso
- Exclusivo do cron de sync (`sync-convenia-employees`) ou chamada manual por superadmin
- NUNCA exposto para chamada direta de usuário comum

## Fluxo
```json
{"method":"roster.sync","params":{}}
```

## Resposta
```json
{
  "ok": true,
  "result": {
    "employees": 121,
    "departments": 23,
    "jobs": 229,
    "cost_centers": 24,
    "slack_ids_matched": 117,
    "deactivated": 0
  }
}
```

## Regras
- Chamada mais cara da API — depende de credencial externa (Convenia + Slack)
- NUNCA usar às cegas quando alguém "não foi encontrado"
- Quem sai da listagem do Convenia é marcado como inativo, nunca apagado
- O serviço protege contra sync com lista vazia (não desativa todo mundo por erro)