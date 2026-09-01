import os, subprocess, requests, json

# Carregar credenciais do .env
env_raw = subprocess.check_output(['cat', '/opt/data/.env'], text=True)
for line in env_raw.split('\n'):
    if '=' in line and not line.startswith('#'):
        k, v = line.strip().split('=', 1)
        os.environ[k] = v.strip("\"'")

host = os.environ['DATABRICKS_HOST'].replace('https://', '')
token_url = f"https://{host}/oidc/v1/token"

# OAuth token
resp = requests.post(token_url,
    data={'grant_type': 'client_credentials', 'scope': 'all-apis'},
    auth=(os.environ['DATABRICKS_CLIENT_ID'], os.environ['DATABRICKS_CLIENT_SECRET']),
    timeout=30)
token = resp.json()['access_token']

# Query
sql = """
SELECT 
    status_acordo,
    produto_receita,
    COUNT(*) AS acordos,
    ROUND(SUM(valor_total_recebido), 2) AS total_recebido,
    ROUND(AVG(valor_total_recebido), 2) AS media_recebido
FROM lakehouse.gold.vouch_acordos
GROUP BY status_acordo, produto_receita
ORDER BY status_acordo, produto_receita
"""

resp = requests.post(f"https://{host}/api/2.0/sql/statements",
    headers={'Authorization': f'Bearer {token}'},
    json={
        'statement': sql,
        'warehouse_id': os.environ['DATABRICKS_WAREHOUSE_ID'],
        'wait_timeout': '50s',
        'on_wait_timeout': 'RETURN_RESULT'
    },
    timeout=90)

result = resp.json()

# Output
cols = [c['name'] for c in result['result']['manifest']['schema']['columns']]
rows = result['result'].get('data_array', [])

# Print as TSV for easy reading
print('\t'.join(cols))
for row in rows:
    print('\t'.join(str(v) for v in row))

print(f"\n---\nTotal: {len(rows)} linhas")