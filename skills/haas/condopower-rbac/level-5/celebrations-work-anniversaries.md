# celebrations.work_anniversaries — Level 5 / Crons

## Uso
- Exclusivo dos crons automáticos
- NUNCA exposto para chamada direta de usuário

## Fluxo (cron `tempo-casa-mensal`)
1. Executar `condopower_scripts.py work_anniversaries`
2. O script chama:
```json
{"method":"celebrations.work_anniversaries","params":{}}
```
3. Para cada celebrant, resolve Slack mention via `access.verify`
4. Envia mensagem no #people-hr

## Regras
- Conta a partir de 1 ano completo
- `years` = anos de casa
- `hiring_date` = data de admissão