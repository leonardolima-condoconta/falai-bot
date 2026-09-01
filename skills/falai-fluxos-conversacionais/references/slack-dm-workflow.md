# Slack DM Workflow para Falai

Quando a Falai precisar entrar em contato com alguem no Slack (repassar pergunta do Catarcione, pedir definicao, etc.).

## ⛔ Passo 0 — VALIDACAO PREVIA (OBRIGATORIO, corrigido por Catarcione 14/08/2026)

NUNCA enviar DM sem o solicitante aprovar o texto antes. Fluxo correto:
1. Resolver destinatario (email no banco → UID via `users.lookupByEmail`).
2. Montar o rascunho da mensagem.
3. Apresentar o texto integral ao solicitante e aguardar "ok" EXPLICITO.
4. So entao abrir DM e `chat.postMessage`.

Enviar direto sem aprovação é violação grave. "Quem pede, aprova": se Catarcione pediu, o draft vai pra ele; se Amandinha pediu, vai pra ela. Não repassar aprovação entre eles.

## Passos

### 1. Encontrar a pessoa no banco
```python
import sqlite3
conn = sqlite3.connect('/opt/data/convenia_data/convenia.db')
cur = conn.cursor()
cur.execute("SELECT name, email FROM employees WHERE name LIKE ? AND is_active = 1", (f"%{nome}%",))
```

### 2. Achar UID do Slack via email
`users.lookupByEmail` e MAIS confiavel que `users.list` (workspace grande pode ter 400+ membros, paginacao falha).

```python
url = f"https://slack.com/api/users.lookupByEmail?email={email}"
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
```

### 3. Abrir DM e enviar mensagem

Salvar script em `/opt/data/scripts/` (nao em `/tmp/` — HERMES_WRITE_SAFE_ROOT bloqueia) e executar.

Token sempre extraido do `.env` binario:
```python
with open("/opt/data/.env", "rb") as f:
    data = f.read()
idx = data.find(b"SLACK_BOT_TOKEN=")
start = idx + len(b"SLACK_BOT_TOKEN=")
end = data.find(b"\n", start)
token = data[start:end].decode("utf-8", errors="replace")
```

**NUNCA** colocar token literal no comando do terminal — Hermes bloqueia `xoxb-` no shell.

### Pitfalls
- `users.list` pode nao retornar a pessoa nas primeiras 200 paginas. Prefira `users.lookupByEmail`.
- `people.db` e `condoconta.db` estao vazios. Use `convenia.db`.
- `/tmp/` esta fora do `HERMES_WRITE_SAFE_ROOT`. Escrever scripts em `/opt/data/scripts/`.