# WhatsApp Shared-Number Security Hardening (Runbook v3)

> Baseado no runbook da Eva (01/07/2026). Aplicar APÓS o pareamento inicial.
> Padrão testado: Hermes Agent v0.17.0, container HaaS, `HERMES_HOME=/opt/data`.

## Problema

Quando agente e humano compartilham o mesmo número WhatsApp:
- `dm_policy: open` (default) → agente responde DMs privadas do humano (**vazamento**)
- `group_policy: open` (default) → agente responde em qualquer grupo do humano
- Mensagens do humano chegam como `fromMe: true` → ignoradas sem gate de menção

## Checklist pós-pareamento

### 1. Descobrir LID do humano
```bash
# Opção A: creds.json (se companion device)
python3 -c "import json; c=json.load(open('<session_path>/creds.json')); print(c['me']['lid'])"

# Opção B: messages.db (se creds.json não tem LID)
python3 -c "
import sqlite3
c = sqlite3.connect('/opt/data/.hermes/whatsapp/messages.db')
for row in c.execute('SELECT DISTINCT sender_id, sender_name FROM messages WHERE from_me=1 AND sender_name NOT LIKE \"%~\" LIMIT 5'):
    print(row[0], '|', row[1])
"
```

### 2. Fechar dm_policy e group_policy (CRÍTICO)
```bash
# Em TODOS os 3 níveis (senão bridging reverte para open)
hermes config set whatsapp.dm_policy allowlist
hermes config set whatsapp.extra.dm_policy allowlist
hermes config set platforms.whatsapp.extra.dm_policy allowlist

hermes config set whatsapp.allow_from "<LID>@lid"
hermes config set whatsapp.extra.allow_from "<LID>@lid"
hermes config set platforms.whatsapp.extra.allow_from "<LID>@lid"
```

### 3. .env
```bash
WHATSAPP_MODE=normal        # obrigatório p/ número compartilhado
WHATSAPP_DM_MODE=all        # loga TODAS as DMs (não só watchlist)
WHATSAPP_ALLOWED_USERS=<num>@s.whatsapp.net,<LID>@lid
```

### 4. Gate de menção no bridge.js (PATCH B)
```javascript
// No bloco fromMe, adicionar antes do self-chat validation:
if (isGroup && WHATSAPP_MODE === 'normal') {
  const _mc = getMessageContent(msg);
  const _txt = (_mc?.conversation || _mc?.extendedTextMessage?.text || '') + '';
  const _mentionsAgent = /@?(nome)[\u00e3a]o/i.test(_txt);
  if (!_mentionsAgent) continue;
}
```

### 5. Validar config efetiva (ANTES de reiniciar)
```bash
HERMES_HOME=/opt/data /opt/hermes/.venv/bin/python3 -c "
from gateway.config import load_gateway_config, Platform
wa = load_gateway_config().platforms.get(Platform.WHATSAPP)
for k in ('dm_policy','allow_from','group_policy','group_allow_from'):
    print(f'{k}: {wa.extra.get(k)}')
"
# Deve mostrar allowlist, NÃO open
```

### 6. Permissões
```bash
# session_path deve ser hermes-owned
chown -R hermes:hermes /opt/data/platforms/whatsapp-<AGENTE>/
```

## Resultado esperado
```
Self-chat do dono     → ✅ responde
Grupo autorizado+@nome → ✅ responde
Outros grupos/DMs     → ❌ não responde (mas loga tudo)
```

## Pitfalls

- **LID não aparece no creds.json**: normal se não for companion device. Descobrir via `messages.db` ou `sock.user.lid` no runtime.
- **`Logged out` após restart**: sessão WhatsApp expirou. Re-parear (deletar sessão, gerar QR).
- **Config revertendo para `open`**: bridging do loader sobrescreve. SEMPRE validar com loader real (§2.3).