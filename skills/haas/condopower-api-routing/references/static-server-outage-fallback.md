# Static-Server Outage — Fallback para Formulários People

> **Skill pai:** `condopower-api-routing`
> **Caso real:** 31/08/2026 — Caroline Monguilhott Duarte tentou acessar formulário de autoavaliação, servidor inacessível.

## Sintomas

| Teste | Resultado esperado | Resultado na outage |
|---|---|---|
| `curl https://static-server.aiexpert-condoconta.info/...` | HTTP 200 | Timeout (exit code 28) |
| `ping static-server.aiexpert-condoconta.info` | Resposta | 100% packet loss |
| `publish.sh` (republicação) | Sucesso | Timeout ou erro de conexão |

## Diagnóstico rápido (3 comandos)

```bash
# 1. Verificar se o servidor responde
curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 \
  https://static-server.aiexpert-condoconta.info/avaliacao-<slug>

# 2. Verificar conectividade de rede
ping -c 2 -W 3 static-server.aiexpert-condoconta.info

# 3. Verificar se o arquivo HTML local existe (foi gerado pelo script)
ls -la /tmp/avaliacao-<slug>.html
```

Se (1) retornar `000` e (2) mostrar 100% loss → **static-server fora do ar**.

## O que NÃO fazer

- ❌ **Republicar o formulário** — o `publish.sh` também depende do static-server. Vai falhar igual.
- ❌ **Ficar tentando retries** — o problema é de infraestrutura, não de rede do container.
- ❌ **Dizer "tente mais tarde" e encerrar** — o colaborador tem prazo e merece alternativa.

## Fallback: Coleta por chat via API

Quando o static-server está fora do ar e o colaborador precisa preencher um formulário:

### Passo 1 — Identificar o colaborador
`access.verify` pelo webhook-proxy (NÃO depende do static-server):
```python
POST https://webhook-proxy.condoconta.com.br/webhooks/condopower-api
Headers: X-Service-Account-Token + auth
Body: {method: "access.verify", params: {identifier: "<slack_id>"},
       sa_token: "...", auth: "..."}
```

### Passo 2 — Oferecer as alternativas
```
🅰️ Preencher por chat — eu faço as perguntas, você responde, eu registro.
🅱️ Aguardar o servidor voltar — te aviso quando normalizar.
```

### Passo 3 — Se escolher chat: carregar perguntas do JSON local
Os arquivos estão em `/opt/data/convenia/`:
- `autoavaliacao_perguntas.json` — perguntas de autoavaliação
- `avaliacao_lider_perguntas.json` — perguntas de avaliação de liderança

Buscar o colaborador pelo email no JSON.

### Passo 4 — Coletar respostas em blocos
Fazer as perguntas em blocos de 5-7, com o número e o texto exato. Para escalas (1-5), apresentar os botões como opções numeradas. Para texto livre, pedir parágrafos.

### Passo 5 — Gravar via API
```python
POST https://webhook-proxy.condoconta.com.br/webhooks/condopower-api
Body: {
  method: "form.autoavaliacao",  # ou form.avaliacao_lider, etc.
  params: {
    colaborador_id: "<uuid>",
    colaborador_email: "...",
    colaborador_nome: "...",
    area: "...",
    perguntas: {"q1": "4", "q2": "texto...", ...}
  }
}
```

## Quando o servidor voltar

1. Verificar com `curl --connect-timeout 5` se voltou a responder
2. Republicar o formulário com `publish.sh` (para garantir versão fresca)
3. Avisar o colaborador que o link voltou a funcionar

## Referências

- `condopower-api` — métodos `form.autoavaliacao`, `access.verify`
- `condopower-api-routing` — endpoints corretos (webhook-proxy)
- `gerar_form_avaliacao.py` — geração de HTML de autoavaliação