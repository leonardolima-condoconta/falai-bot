# celebrations.birthdays — Level 5 / Crons

## Uso
- Exclusivo dos crons automáticos
- NUNCA exposto para chamada direta de usuário

## Fluxo (cron `aniversarios-do-dia`)
1. Executar `condopower_scripts.py birthdays`
2. O script chama:
```json
{"method":"celebrations.birthdays","params":{}}
```
3. Para cada celebrant, resolve Slack mention via `access.verify`
4. Envia mensagem no #people-hr

## Segunda-feira
- `covered_dates` inclui sábado e domingo anteriores
- Agrupar mensagem por dia: "no sábado", "no domingo", "hoje"