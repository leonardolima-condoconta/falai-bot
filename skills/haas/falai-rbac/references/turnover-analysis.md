# Análise de Turnover — Fluxo

Como gerar relatórios de turnover com as ferramentas disponíveis hoje (Convenia + condopower-api).

## O que dá pra calcular TODAY

### Admissões por mês → Convenia (completo)

A lista `/api/v3/employees` do Convenia tem `hiring_date` para todos os 120 cadastrados. Agrupar por ano-mês cobre 100% das entradas:

```python
from convenia import ConveniaClient
from collections import Counter

with ConveniaClient() as client:
    resp = client._client.get('/api/v3/employees?page=1&limit=150')
    employees = resp.json().get('data', [])

monthly = Counter()
for e in employees:
    hd = e.get('hiring_date')
    if hd:
        monthly[hd[:7]] += 1   # "2026-08"
```

### Inativos → cross-reference Convenia × condopower-api

O Convenia lista todo mundo (ativos + inativos), mas sem campo `active`. A `condopower-api` (`access.verify`) responde `is_active: true/false`. Cruzar os dois revela quem saiu:

```python
import os, json, subprocess

sa_token = os.environ['CONDOPOWER_SA_TOKEN']
auth = os.environ['CONDOPOWER_AUTH']

for e in employees:
    email = e.get('email')
    if not email:
        continue  # sem email = não dá pra verificar
    cmd = ['curl', '-s', '-X', 'POST',
           'https://webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc',
           '-H', 'Content-Type: application/json',
           '-H', f'X-Service-Account-Token: {sa_token}',
           '-H', f'auth: {auth}',
           '-d', json.dumps({'method': 'access.verify', 'params': {'identifier': email}})]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    data = json.loads(result.stdout)
    if data.get('ok'):
        is_active = data['result'].get('is_active')
        # classificar...
```

**Performance:** ~120 chamadas sequenciais (~10s de timeout cada). Sempre rodar de `/opt/data/convenia` com o `.env` isolado.

## ⛔ O que NÃO dá pra calcular TODAY

### Datas de desligamento

O token `Falai-Bot` do Convenia **não tem permissão** para dados de desligamento/terminação — retorna HTTP 403. Sem a data de saída, não é possível:
- Calcular taxa de turnover mensal (saídas ÷ headcount médio)
- Saber em qual mês cada pessoa saiu
- Analisar sazonalidade de desligamentos

### Escalação

Para ter turnover completo, precisa de uma das opções:
1. Ampliar escopo do token Convenia `Falai-Bot` (adicionar permissão de leitura de `terminations`)
2. Adicionar endpoint `turnover` na `condopower-api`
3. Dados manuais de datas de saída fornecidos pelo time People

Notificar **Leonardo de Lima** (DM: U0APYGTD8K1) para avaliar viabilidade técnica das opções 1 ou 2.

## Headcount ativo

O total de ativos sai do `condopower-api`: soma de todos que respondem `is_active: true` ao `access.verify`. Em 25/08/2026: **116 ativos** de 120 cadastrados no Convenia.

## Pitfalls

- Colaboradores sem email no Convenia (ex: Schaiane da Cruz) não passam pelo `access.verify` — contar como "status desconhecido", não como ativo nem inativo
- `condopower-api` resolve por email, não por UUID do Convenia — o `access.verify` aceita ambos, mas o batch usa email porque é o campo comum
- O Convenia lista 120; o `condopower-api` conhece quem passou pelo `roster.sync`. Divergências podem existir se o sync estiver desatualizado
- Rodar cross-reference sempre de `/opt/data/convenia/` (`.env` isolado) com `PYTHONPATH=/opt/data` e `/opt/data/.venv/bin/python3`