import subprocess, requests, os

# Carregar credenciais do .env
env_raw = subprocess.check_output(['cat','/opt/data/.env'], text=True)
for line in env_raw.split('\n'):
    if '=' in line and not line.startswith('#'):
        k, v = line.strip().split('=', 1)
        os.environ[k] = v.strip('"').strip("'")

host = os.environ['DATABRICKS_HOST'].replace('https://','')
warehouse_id = os.environ['DATABRICKS_WAREHOUSE_ID']

# OAuth token
token_url = f'https://{host}/oidc/v1/token'
token_resp = requests.post(token_url,
    data={'grant_type': 'client_credentials', 'scope': 'all-apis'},
    auth=(os.environ['DATABRICKS_CLIENT_ID'], os.environ['DATABRICKS_CLIENT_SECRET']))
token = token_resp.json()['access_token']

# Query
sql = 'SELECT status_acordo, COUNT(*) AS qtd FROM lakehouse.gold.vouch_acordos GROUP BY 1 ORDER BY 2 DESC'

resp = requests.post(f'https://{host}/api/2.0/sql/statements',
    headers={'Authorization': f'Bearer {token}'},
    json={'statement': sql, 'warehouse_id': warehouse_id,
          'wait_timeout': '50s', 'on_wait_timeout': 'RETURN_RESULT'},
    timeout=90)

result = resp.json()
rows = result['result']['data_array']
columns = [c['name'] for c in result['manifest']['schema']['columns']]

print('| ' + ' | '.join(columns) + ' |')
print('|' + '|'.join(['---']*len(columns)) + '|')
for row in rows:
    status = str(row[0]) if row[0] else 'NULO'
    qtd = f'{row[1]:,}'.replace(',', '.')
    print(f'| {status} | {qtd} |')

total = sum(r[1] for r in rows)
print(f'\nTotal de acordos: {total:,}'.replace(',', '.'))
