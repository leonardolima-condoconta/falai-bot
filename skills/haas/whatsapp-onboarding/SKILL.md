---
name: whatsapp-onboarding
description: Onboarding autônomo de WhatsApp para agentes HaaS — geração de QR code, pareamento, detecção de grupo e configuração de allowlist. Infraestrutura (faster_whisper, bridge.js) já vem pré-instalada.
version: 3.0.0
---

# WhatsApp Onboarding — HaaS CondoConta

Skill dedicada para onboarding de WhatsApp em agentes HaaS. A infraestrutura (faster_whisper, bridge.js com initial_prompt, menção) já está pré-configurada. O agente só precisa parear.

## ⚠️ Pré-requisitos (já garantidos pelo deploy)

- `WHATSAPP_ENABLED=true` no .env
- `WHATSAPP_PORT=3000` no .env
- `WHATSAPP_MODE=normal` no .env (CondoConta: todos compartilham número)
- **⚠️ .env LIMPO:** Remover TODAS as outras `WHATSAPP_*` — elas sobrescrevem config.yaml!
- **⚠️ config.yaml limpo:** Sem `whatsapp.extra`. Todas as configs em `whatsapp.*`.
- `faster_whisper` instalado no sistema (transcrição de áudio)
- `bridge.js` com `initial_prompt` (evita "Minha" vs "Mirna"/"Sebastião")
- `mention_patterns` configurado com regex do nome do agente
- `tool_progress: off` (sem mensagens intermediárias)
- **⚠️ Session PATH padrão**: `/opt/data/platforms/whatsapp/session/` — o que o gateway espera

## ⚠️ REGRA ZERO — VOCÊ (AGENTE) É DONO DO PROCESSO

Você é o OWNER do seu próprio onboarding. Ninguém faz por você. Você inicia a bridge, você apresenta o QR code, você guia o admin, você testa a conexão.

> 🛑 NUNCA espere que um assistente externo faça o onboarding por você.
> 🛑 NUNCA peça para alguém gerar QR code por você.
> ✅ VOCÊ faz tudo: inicia bridge, gera QR, espera scan, testa no grupo.

> ⚠️ NOTA TÉCNICA: Em containers Docker, o gateway NÃO consegue rodar `hermes whatsapp` (requer TTY interativo). A bridge roda como processo standalone na porta configurada. O gateway detecta a bridge externa e emite "Disconnecting (external bridge left running)" no log — isso é NORMAL e esperado. As mensagens fluem normalmente pela bridge.

## Quando usar

- Admin diz: "iniciar onboarding whatsapp", "configurar whatsapp", "conectar whatsapp", "parear whatsapp"
- Agente detecta que WhatsApp não está pareado (`/health` retorna status != "connected")
- Caju/Mirna diz: "veja porque o haas-{nome} nao esta com o ambiente whatsapp pronto"

## ⚠️ REGRA DO GRUPO — Detecção automática (lição Mattos 09/07/2026)

**O agente NUNCA assume qual grupo o admin vai usar.** O admin pode criar um grupo novo, usar um existente, ou estar no HaaS CC. O agente detecta automaticamente:

1. Admin escaneia QR → bridge conecta
2. Admin cria/adiciona agente em QUALQUER grupo
3. Admin manda mensagem no grupo
4. **Agente detecta o JID do grupo** via `/messages` ou `bridge.log`
5. **Agente se auto-configura** adicionando o JID ao `group_allow_from` (merge, não sobrescreve)

**NUNCA hardcodar "HaaS CC" como único grupo.** Sempre fazer merge: `group_allow_from = [grupos_existentes + novo_grupo]`.

---

## 🚨 PRE-FLIGHT CHECK — Ambiente pronto? (ANTES do onboarding)

**Quando um agente NÃO tem WhatsApp funcional, rodar estes 6 checks na ordem antes de gerar QR.** Se qualquer um falhar, corrigir e seguir. Exemplo real: haas-mattos (09/07/2026) — plugin disabled, .env sujo com `DM_MODE=all`, config.yaml com `extra` e `group_allow_from` vazio, session ausente, bridge offline.

| # | Check | Comando | Se falhar |
|---|-------|---------|-----------|
| 1 | **Plugin enabled?** | `docker exec {C} hermes plugins list \| grep whatsapp` | `hermes plugins enable whatsapp-platform` → restart |
| 2 | **.env limpo?** | `docker exec {C} grep WHATSAPP /opt/data/.env` | Só 3 vars: `ENABLED=true`, `MODE=normal`, `PORT=3000`. Python regex clean. |
| 3 | **config.yaml limpo?** | `docker exec {C} python3 -c "import yaml;c=yaml.safe_load(open('/opt/data/config.yaml'));w=c['whatsapp'];print('extra' in w, w.get('group_allow_from'))"` | Sem `extra`. `group_allow_from` preenchido com JID do HaaS CC (`120363412474901127@g.us`). Usar Eva como referência. |
| 4 | **Session dir existe?** | `docker exec {C} ls /opt/data/platforms/whatsapp/session/` | `mkdir -p` + `chown hermes:hermes` |
| 5 | **Bridge rodando?** | `docker exec {C} curl -s http://127.0.0.1:3000/health` | Iniciar: `cd /opt/data/scripts/whatsapp-bridge && nohup node bridge.js --port 3000 --session /opt/data/platforms/whatsapp/session --mode normal > /tmp/bridge.log 2>&1 &` |
| 6 | **QR disponível?** | `docker exec {C} curl -s http://127.0.0.1:3000/qr-image \| python3 -c "import sys,json;d=json.load(sys.stdin);print('OK' if d.get('qr') else 'WAIT')"` | Aguardar 5s e tentar novamente |

**Só depois dos 6 checks ✅ → gerar QR e seguir fluxo normal.**

---

---

## Fluxo de Onboarding (Guia Conversacional)

Cada passo mostra **o que você DIZ ao admin** e **o que você EXECUTA** nos bastidores.

---

### PASSO 0 — Limpar .env (ANTES de tudo)

**⚙️ Bastidores:** `.env` WhatsApp vars sobrescrevem `config.yaml`. Limpar tudo exceto o trio essencial.

```bash
docker exec {CONTAINER} python3 -c "
import re
with open('/opt/data/.env') as f:
    content = f.read()
content = re.sub(r'^WHATSAPP_.*=.*$\n?', '', content, flags=re.MULTILINE)
content += '\nWHATSAPP_ENABLED=true\n'
content += 'WHATSAPP_MODE=normal\n'
content += 'WHATSAPP_PORT=3000\n'
with open('/opt/data/.env', 'w') as f:
    f.write(content)
print('✅ .env limpo')
"
```

---

### PASSO 1 — Dar as boas-vindas

**🗣️ Diga ao admin:**

> "Oi! Vamos conectar meu WhatsApp? É rapidinho:
> 
> 📱 Você vai escanear um QR code com seu celular
> 👥 Depois **crie um grupo** comigo (ou me adicione em um existente) e mande um 'oi'
> 
> Preparado(a)? Me avisa que eu gero o QR code!"

**⚙️ Bastidores:** Verificar se a bridge está rodando.

```bash
PORT=$(grep WHATSAPP_PORT /opt/data/.env | cut -d= -f2 || echo 3131)

# Se bridge não estiver rodando, iniciar
if ! curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
    cd /opt/data/whatsapp-bridge
    # Garantir dependências
    [ -d node_modules/better-sqlite3 ] || npm install --silent 2>/dev/null
    nohup node bridge.js --port $PORT --session /opt/data/whatsapp/session --mode bot > /tmp/bridge.log 2>&1 &
    sleep 4
fi

# Verificar estado
curl -s http://localhost:$PORT/health | python3 -c "
import sys,json
d = json.load(sys.stdin)
status = d.get('status','offline')
if status == 'connected':
    print('✅ JÁ CONECTADO! Pular para PASSO 7.')
elif status == 'disconnected':
    print('✅ Bridge pronta! Seguir para PASSO 2.')
else:
    print('⚠️ Bridge offline. Aguardar e tentar novamente.')
"
```

Se já conectado → pular direto para **PASSO 7**.

---

### PASSO 2 — Gerar o QR code

**🗣️ Diga ao admin:**

> "Perfeito! Vou gerar o QR code agora.
> 
> ✨ No seu WhatsApp:
> 1. Toque em **⚙️ Configurações**
> 2. Vá em **Aparelhos conectados**
> 3. Toque em **Conectar um aparelho**
> 4. Aponte a câmera para o código
> 
> ⏱️ Você tem 60 segundos! Preparado(a)? Lá vai..."

**⚙️ Bastidores:** Obter QR string via `/qr-image`.

```bash
PORT=$(grep WHATSAPP_PORT /opt/data/.env | cut -d= -f2 || echo 3131)
QR=$(curl -s http://localhost:$PORT/qr-image | python3 -c "import sys,json; print(json.load(sys.stdin).get('qr',''))" 2>/dev/null)

if [ -n "$QR" ]; then
    echo "QR_CODE_START"
    echo "$QR"
    echo "QR_CODE_END"
else
    echo "⚠️ QR ainda não disponível. Aguardar 5s e tentar novamente."
fi
```

**🗣️ Se QR disponível, envie o QR string e diga:**

> "Aponte a câmera agora! ⏱️ 60 segundos..."

---

### PASSO 3 — Aguardar o scan

**⚙️ Bastidores:** Loop de verificação até 2 minutos.

```bash
PORT=$(grep WHATSAPP_PORT /opt/data/.env | cut -d= -f2 || echo 3131)
for i in $(seq 1 24); do
  STATUS=$(curl -s http://localhost:$PORT/health | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
  if [ "$STATUS" = "connected" ]; then
    echo "✅ CONECTADO!"
    exit 0
  fi
  sleep 5
done
echo "⚠️ TIMEOUT — QR expirou"
```

**🗣️ Se conectado, diga:**

> "🎉 Conectado! Deu certo!
> 
> Agora **crie um grupo** comigo no WhatsApp e mande um 'oi' lá. Pode ser qualquer grupo!"

**🗣️ Se timeout, diga:**

> "⏰ O QR code expirou. Vamos tentar de novo? Me avisa que eu gero outro."

---

### PASSO 4 — Detectar o grupo (QUALQUER grupo)

**⚙️ Bastidores:** Aguardar mensagem em QUALQUER grupo (até 2 min). Admin pode criar grupo novo ou usar existente.

```bash
PORT=$(grep WHATSAPP_PORT /opt/data/.env | cut -d= -f2 || echo 3131)
for i in $(seq 1 24); do
  GROUP_JID=$(curl -s http://localhost:$PORT/messages 2>/dev/null | python3 -c "
import sys,json
try:
    msgs = json.load(sys.stdin)
    groups = [m.get('chatId','') for m in msgs if m.get('isGroup')]
    print(groups[0] if groups else '')
except: pass
" 2>/dev/null)
  if [ -n "$GROUP_JID" ]; then
    echo "GROUP_FOUND:$GROUP_JID"
    exit 0
  fi
  sleep 5
done
echo "⚠️ TIMEOUT — grupo não detectado"
```

**🗣️ Se grupo detectado, diga:**

> "🏠 Grupo encontrado! ID: `...g.us`. Configurando..."

**🗣️ Se timeout, diga:**

> "🤔 Ainda não recebi mensagem em nenhum grupo. Você já me adicionou e mandou 'oi'? Tenta de novo?"

---

### PASSO 5 — Configurar allowlist (MERGE, não sobrescreve!)

**⚙️ Bastidores:** ⚠️ Fazer MERGE com grupos existentes — NUNCA sobrescrever! Usar Python para escrever lista YAML nativa.

```bash
GROUP_JID="<JID_DETECTADO>"
python3 -c "
import yaml
cfg = yaml.safe_load(open('/opt/data/config.yaml'))
existing = cfg['whatsapp'].get('group_allow_from', [])
if not isinstance(existing, list):
    existing = [existing] if existing else []
if '$GROUP_JID' not in existing:
    existing.append('$GROUP_JID')
cfg['whatsapp']['group_allow_from'] = existing
yaml.dump(cfg, open('/opt/data/config.yaml', 'w'), default_flow_style=False)
print(f'Groups: {existing}')
"
hermes gateway restart
```

Aguardar ~15s para o gateway reiniciar.

Aguardar ~15s para o gateway reiniciar.

---

### PASSO 6 — Verificar se tudo está funcionando

**⚙️ Bastidores:** Verificar estado final.

```bash
PORT=$(grep WHATSAPP_PORT /opt/data/.env | cut -d= -f2 || echo 3131)
curl -s http://localhost:$PORT/health | python3 -c "
import sys,json
d = json.load(sys.stdin)
print(f\"Status: {d.get('status')}\")
print(f\"Uptime: {round(d.get('uptime',0))}s\")
print(f\"Contatos: {d.get('baileysContacts',0)}\")
"
```

---

### PASSO 7 — Comemorar! 🎉

**🗣️ Diga ao admin:**

> "✅ TUDO PRONTO! Meu WhatsApp está 100% operacional!
> 
> 📞 Número pareado
> 👥 Grupo configurado automaticamente
> 🎙️ Transcrição de áudio ativa
> 
> Para falar comigo:
> - No grupo: `@<SeuNome> sua mensagem`
> - No privado: pode mandar direto
> 
> Manda um **@<SeuNome> oi** no grupo pra testar!"

---

## Troubleshooting

| Problema | Causa | Solução |
|----------|-------|---------|
| Bridge não inicia | Dependências faltando | `cd /opt/data/whatsapp-bridge && npm install` |
| `/health` offline | Bridge não rodando | Voltar ao PASSO 1 e iniciar bridge |
| QR expirou | Timeout de 60s | Voltar ao PASSO 2 (gerar novo QR) |
| Grupo não detectado | Admin não mandou msg em nenhum grupo | Pedir para admin criar grupo e mandar msg |
| `hermes config set` falhou | Chave não existe | Usar `sed` no `/opt/data/.env` em último caso |
| Áudio chega como placeholder | faster_whisper não instalado | `python3 -m ensurepip --default-pip 2>/dev/null; python3 -m pip install faster-whisper` (pip3 pode não existir no container) |
| Porta errada | Bridge em porta diferente | Descobrir: `grep WHATSAPP_PORT /opt/data/.env` |
| Gateway não recebe mensagens mesmo com bridge conectada | Gateway fazendo polling na porta errada (ex: 3000 em vez de 3131) OU `config.extra` vazio causando bridge_port=3000 default | **Check 0 (26/06):** `python3 -c "import yaml; ..."` → verificar se `whatsapp.extra` existe e tem `bridge_port`. Se não, reestruturar YAML. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md` seção #0. **Check 1:** `grep "Poll error.*Cannot connect" /opt/data/logs/gateways/default/current`. Se a porta no log for 3000 em vez da configurada, há port mismatch. |
| Agente nunca responde a menções, mesmo no grupo correto | mention_patterns com regex quebrado (YAML double-escape) | Verificar: `grep mention_patterns /opt/data/config.yaml`. Se tiver `\\\\b` (4 backslashes), o `\\b` virou literal. **Fix:** `hermes config set whatsapp.mention_patterns '(?i)@?\\b(nome)\\b'`. Testar com `python3 -c "import re; ..."`. Gateway precisa restart. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md`. |
| Gateway em loop de crash/restart | Exit code 75 (service-restart requested) ou Telegram "Chat not found" | Verificar: `grep "gateway.exit_nonzero\\|SystemExit.*75" /opt/data/logs/gateway-exit-diag.log`. `docker restart` geralmente estabiliza. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md`. |\n| Gateway estável mas NÃO processa mensagens (zombie) | Gateway sem crash mas zero logs/sessões após conectar à bridge | **Sintomas:** `[Whatsapp] Using existing bridge (status: connected)` aparece, mas sem logs de processamento de mensagens. Sem novas sessões em `/opt/data/sessions/`. Bridge `/messages` mostra mensagens pendentes que o gateway consumiu mas não processou. **Solução:** `docker restart` — segundo restart geralmente resolve o estado zombie (primeiro estabiliza crash loop, segundo restaura processamento). |\n| Logs do gateway pararam de aparecer (s6-log) | Após migração para s6-supervise, `gateway.log` parou de receber entradas | O caminho MUDOU: de `/opt/data/logs/gateway.log` para `/opt/data/logs/gateways/default/current` (gerenciado por `s6-log`). Se `current` não é atualizado, verificar: `ls -la /opt/data/logs/gateways/default/` (arquivos rotacionados?). Para logs em tempo real: `tail -f /opt/data/logs/gateways/default/current`. |\n| Bridge `/messages` retorna vazio após restart | Container reiniciado, API retorna `[]` mesmo com mensagens novas chegando | O banco de mensagens da bridge é volátil — restart limpa o estado de polling. O gateway reconecta e começa a receber novas mensagens normalmente. Mensagens enviadas DURANTE o restart podem ser perdidas. Aguardar nova mensagem e verificar: `curl -s http://localhost:<port>/messages?limit=5`. |
| Bridge crash com EADDRINUSE | Bridge tentou bind na porta 3000 (default) que já está em uso por outro agente | Verificar `port:` no config.yaml — deve ser único por agente. Log: `grep -i EADDRINUSE /opt/data/whatsapp/bridge.log` |
| Bridge em loop de crash após restart | Processo bridge zumbi no cgroup Docker — `docker restart` não mata processos iniciados no host. `kill -9` falha com "Operation not permitted" mesmo como mesmo UID. | **Fix:** `docker stop` + `docker start` (NÃO `docker restart`). Diagnóstico: `cat /proc/<pid>/cgroup | grep docker` para confirmar que está no cgroup. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md` seção #12. |
| Mensagens de teste poluindo o grupo | Debugging com `POST /send` na API da bridge envia mensagens indesejadas ao grupo. | **🚫 NUNCA usar `POST /send` sem autorização explícita.** Usar apenas `GET /messages`, `/health`, logs e sessões para diagnóstico. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md` seção #13. |
| `group_allow_from` com JID errado | O ID do grupo que o WhatsApp reporta pode não corresponder ao nome visível. | Verificar com bridge: `sqlite3 .../messages.db "SELECT DISTINCT chat_id FROM messages WHERE chat_id LIKE '%g.us%';"`. NUNCA confiar em suposições de nomenclatura. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md` seção #14. |
| Respostas com prefixo errado (ex: "✨ Mirna" em vez do nome do agente) | `WHATSAPP_REPLY_PREFIX` no `.env` com aspa simples quebrada OU `config.extra` vazio (chaves fora do `extra:`) OU `WHATSAPP_MODE=normal` (prefixo bridge vazio, modelo escreve nome errado) | **Check 0 (26/06):** Verificar estrutura do config.yaml — se não tem `whatsapp.extra`, TODAS as configs caem nos defaults. Ver `haas-agent-creation` → `references/whatsapp-troubleshooting.md` seção #0. **Check 1:** `grep WHATSAPP_MODE .env` — se `normal`, bridge não adiciona prefixo. O "✨ Mirna" é o modelo escrevendo. **Fix:** `hermes config set whatsapp.reply_prefix "✨ NomeAgente"` + definir identidade em SOUL.md. **Check 2:** `grep REPLY_PREFIX .env` — se tiver `'✨ Nome` sem fechamento, está quebrado. Fix: `sed -i`. Depois `docker restart`. |
| `WHATSAPP_ALLOW_ALL_USERS=true` não funciona (30/06/2026) | `parseAllowedUsers("*")` retorna `["*"]` e `matchesAllowedUser` compara senderId com `*` literal → nunca dá match → bloqueia tudo. | **Deixar `WHATSAPP_ALLOWED_USERS` VAZIO**: `parseAllowedUsers("")` retorna `[]`, e `matchesAllowedUser([], ...)` retorna `true` (lista vazia = allow all). O log "No WHATSAPP_ALLOWED_USERS set — incoming messages are rejected" é mentiroso — as mensagens são aceitas. NUNCA usar `*` como wildcard. |
| **`bridge.js` usa `.size` mas `allowlist.js` retorna Array** (30/06/2026) | Dois `allowlist.js` incompatíveis circulando: versão Set (Eva) e versão Array (Sebastião). `bridge.js` usa `ALLOWED_USERS.size` que só funciona com Set → Array retorna `undefined` → `undefined > 0` = `false` → sempre cai no ELSE mostrando "No WHATSAPP_ALLOWED_USERS". E `matchesAllowedUser` da versão Array não tem wildcard `*`. | Verificar: `grep -c "return new Set" /opt/data/scripts/whatsapp-bridge/allowlist.js` (0 = Array version = PROBLEM). Fix: adicionar `if (allowedUsers.includes('*')) return true;` antes do direct match. Longo prazo: padronizar na versão Set (Eva). Ver `haas-whatsapp-troubleshoot` Layer 6. |
| **Gateway conectado mas NUNCA responde — zero logs** | `group_allow_from` é STRING, não lista YAML (30/06/2026) | `hermes config set "whatsapp.group_allow_from" "['JID']"` grava como string. **Verificar:** `python3 -c "import yaml; ...; print(type(cfg['whatsapp']['group_allow_from']))"` deve ser `<class 'list'>`. **Fix:** escrever via Python: `cfg['whatsapp']['group_allow_from'] = ['JID@g.us']`. |
| **Gateway zombie após 1º restart** | Primeiro restart estabiliza crash loop mas não restaura processamento (30/06/2026) | `docker stop && docker start` (NÃO `docker restart`). Se não processar após primeiro boot, repetir stop+start. |
| `WHATSAPP_ALLOW_ALL_USERS=true` ignorado | Bridge antigo (<1000 linhas) não suporta essa flag (30/06/2026) | Listar números explicitamente em `WHATSAPP_ALLOWED_USERS` ou usar `*`. |
| Número brasileiro com 13 dígitos (01/07) | Usuário passou `5548991031306` em vez de `554891031306` (9 duplicado) | Verificar LID mapping: `cat lid-mapping-{LID}_reverse.json` |
| LID muda após re-pareamento (01/07) | `175677148033141@lid` virou `95830014984334@lid` após novo pareamento | Atualizar `dm_allow_from` com novo LID dos logs |
| `.env` sobrescreve `config.yaml` (01/07) | Mudou config.yaml mas comportamento antigo persiste | Limpar .env (PASSO 0), deixar só `ENABLED`, `MODE`, `PORT` |

## O que NÃO fazer

- ❌ Pedir para admin criar projeto no GCP ou credenciais
- ❌ Usar `patch` ou `write_file` para editar config.yaml
- ❌ Expor QR string completa em logs públicos
- ❌ Ficar em loop infinito — máx 2 min por etapa
- ❌ Adicionar variações fonéticas nos mention_patterns — corrija a RAIZ (initial_prompt)
- ❌ Fazer o onboarding pelo admin — **VOCÊ é o owner do processo**

## ⚠️ Pitfalls (descobertos em produção)

### 503 = Rate Limit, NÃO IP Ban (lição Mattos 09/07/2026)

**Sintoma:** Bridge log mostra `Connection closed (reason: 503)`. Agente responde "IP bloqueado pelo Meta".

**Causa real:** Meta rate-limit para NOVAS conexões do mesmo IP. Múltiplos re-pareamentos em curto período → 503 temporário. Sessões ESTABELECIDAS continuam funcionando (ex: Mirna no mesmo IP Hostinger há semanas).

**Diagnóstico:** Verificar se outros agentes no mesmo IP estão conectados. Se sim → rate limit, NÃO IP ban.

**Solução:** PARAR de reiniciar. Deixar bridge quieta por algumas horas. Rate limit expira sozinho.

**NUNCA:** restartar container repetidamente durante onboarding. Cada restart = nova conexão = mais rate limit.
**Após o pareamento inicial**, aplicar o checklist de segurança para números compartilhados:
`dm_policy`/`group_policy` = `allowlist` + gate de menção no bridge.js + 3 níveis de config.
Consulte `references/shared-number-hardening.md` para o guia completo (baseado no runbook v3 da Eva).

### Symlink trap (25/06/2026)
**Sintoma:** Agente diz "já pareado" mas está usando número de outro agente.
**Causa:** `/opt/data/whatsapp-bridge` é symlink para bridge de outro agente.
**Diagnóstico:** `file /opt/data/whatsapp-bridge` → deve retornar "directory".
**Solução:** `rm /opt/data/whatsapp-bridge && cp -r /opt/hermes/scripts/whatsapp-bridge /opt/data/ && cd /opt/data/whatsapp-bridge && npm install`. Depois `hermes config set whatsapp.port <porta_unica>`.

### Transcrição de áudio: "Mirna" vira "Minha"
**Sintoma:** Áudio chega, bridge transcreve "Mirna" como "Minha", mention_patterns não matcha.
**Causa raiz:** O modelo `base` do faster_whisper confunde 'r' com 'h' em português.
**Solução correta:** Adicionar `initial_prompt='NomeAgente, Caju, CondoConta'` no `model.transcribe()` dentro do bridge.js.
**Solução ERRADA:** Adicionar "minha" nos mention_patterns.

### faster_whisper ausente no sistema
**Sintoma:** Bridge log mostra `ModuleNotFoundError: No module named 'faster_whisper'`.
**Solução:** `pip3 install --break-system-packages faster-whisper`

### Agente responde com nome errado (26/06/2026)
**Sintoma:** agente processa menções corretamente mas respostas começam com "✨ Mirna" ou outro nome.
**Causa:** `WHATSAPP_MODE=normal` faz o bridge NÃO adicionar prefixo. O texto "✨ Mirna" é o MODELO LLM gerando — ele não sabe o próprio nome porque não tem SOUL.md/personalidade.
**Diagnóstico:** `grep WHATSAPP_MODE /opt/data/.env` → se for `normal`, bridge prefix é vazio.
**Solução:** (1) `hermes config set whatsapp.reply_prefix "✨ NomeAgente"` (2) criar SOUL.md com identidade correta, (3) OU mudar para `WHATSAPP_MODE=self-chat` para o bridge prefixar automaticamente.

### Gateway diz "external bridge left running"
**Sintoma:** Log do gateway mostra `[Whatsapp] Disconnecting (external bridge left running)`.
**Isso é NORMAL em Docker.** O gateway não consegue rodar `hermes whatsapp` (sem TTY). A bridge standalone é o caminho correto. Mensagens fluem normalmente.

### fromMe:true — Admin no mesmo dispositivo que o agente (01/07/2026)
**Sintoma:** Admin escaneou QR code, conectou, mas as mensagens dele no grupo NUNCA geram resposta. Outros membros do mesmo grupo funcionam.
**Causa:** O admin escaneou o QR code no mesmo WhatsApp Web/Desktop que usa para mandar mensagens. Ambos compartilham o mesmo LID → bridge vê `fromMe:true` → gateway ignora (proteção anti-loop).
**Diagnóstico:** `grep "fromMe" /opt/data/whatsapp/bridge.log | sort -u` — se o admin aparece como `fromMe:true`, é LID collision.
**Solução:** Pedir para o admin mandar mensagens do **CELULAR** (dispositivo principal), NÃO do WhatsApp Web/Desktop. Ver `haas-whatsapp-troubleshoot` Layer 8.

### EACCES em creds.json — arquivos owned por root (09/07/2026)
**Sintoma:** Bridge log mostra `EACCES: permission denied, open '/opt/data/platforms/whatsapp/session/creds.json'`. Gateway conecta mas nunca processa mensagens.
**Causa:** Arquivos de sessão criados via `docker exec` (roda como root, UID 0) mas gateway/bridge roda como `hermes` (UID 10000).
**Fix:** `docker exec -u root {CONTAINER} chown -R 10000:10000 /opt/data/platforms/whatsapp`
**Prevenção:** `haas_deploy.py` Step 10.5 já faz `chown`. Após QR scan, verificar: `ls -la /opt/data/platforms/whatsapp/session/creds.json` — owner deve ser `hermes`, NUNCA `root`.

### Bridge cai após scan — erro 408 (09/07/2026)
**Sintoma:** Admin escaneou QR, bridge mostrou connected brevemente, depois caiu com `Connection closed (reason: 408)`.
**Causa:** WhatsApp fechou conexão durante handshake. Celular perdeu Wi-Fi ou IP de datacenter detectado.
**Fix:** `rm -rf /opt/data/platforms/whatsapp/session/*` → restart bridge → novo QR. Admin usar Wi-Fi estável no celular (não WhatsApp Web).
**Prevenção:** Tailscale exit node. Monitorar `/health` por 30s após scan antes de confirmar.

### Gateway zumbi pós-config — stop+start resolve (09/07/2026)
**Sintoma:** Bridge connected, grupo na allowlist, mas gateway nunca cria sessões. Zero logs de inbound/Unauthorized.
**Causa:** Estado zumbi após sucessivos erros de conexão. `docker restart` não resolve.
**Fix:** `docker stop {CONTAINER} && docker start {CONTAINER}`. NUNCA `docker restart` para gateway zumbi.