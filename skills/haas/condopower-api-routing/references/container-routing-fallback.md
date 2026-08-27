# Endpoint discovery: container vs browser

**Problema (27/08/2026):** O agente carregou `condopower-api` e usou a URL direta `https://condopower-api.aiexpert-condoconta.info` — 3 timeouts (15s, 30s, 60s). A rota de recuperação:

1. Carregou `condopower-api-routing` → descobriu que o container precisa do webhook-proxy
2. Leu as credenciais com `grep -E 'CONDOPOWER_SA_TOKEN|CONDOPOWER_AUTH' /opt/data/.env`
3. Usou o endpoint correto:
   ```
   POST https://webhook-proxy.condoconta.com.br/webhooks/condopower-api
   Headers: X-Service-Account-Token + auth
   ```
4. Sucesso imediato — `access.verify` retornou em <1s

**Lição:** A skill `condopower-api` (v2.1.0) tem a URL direta mas NÕ menciona o webhook-proxy nem os headers de auth. O agente perde ~60s em timeouts antes de descobrir que precisa da skill de routing. Sempre que `condopower-api` for carregada, considere carregar `condopower-api-routing` em seguida se a chamada para a URL direta falhar.

**Tokens:** `CONDOPOWER_SA_TOKEN` e `CONDOPOWER_AUTH` estão em `/opt/data/.env` e sã acessíveis via `grep` no terminal.