# Suporte Nativo a Webhooks (Hermes)

Hermes suporta receber POST de serviços externos via `platforms.webhook`.

Ativar no `config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      port: 8644
      secret: "chave-secreta"
```

E no `.env`:
```
WEBHOOK_ENABLED=true
WEBHOOK_PORT=8644
WEBHOOK_SECRET=***
```

Criar subscription:
```bash
hermes webhook subscribe condopower-submit \
  --prompt "Formulário recebido: {payload.method}" \
  --deliver telegram \
  --deliver-chat-id "8523247194"
```

O serviço externo POSTa para `http://host:8644/webhook/condopower-submit` com HMAC-SHA256, e o agente processa.

Docs: `autonomous-ai-agents/hermes-agent/references/webhooks.md`