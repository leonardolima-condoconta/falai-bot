# Troubleshooting de acesso à Pesquisa Pulse

Quando um colaborador (normalmente level 1 `condopower`) reporta que **não consegue
acessar o link da pesquisa Pulse**, siga este fluxo antes de assumir qualquer causa.

## Fluxo de diagnóstico

1. **Não assuma problema do lado do cliente.** VPN configurada + `ERR_CONNECTION_TIMED_OUT`
   no navegador quase sempre é o servidor offline, não a rede do colaborador.
2. **Teste o servidor a partir do próprio container:**
   ```bash
   curl -sv --connect-timeout 10 --max-time 15 \
     "https://static-server.aiexpert-condoconta.info/" 2>&1 | head -30
   ```
   - Código `000` / `Connection timed out` após o DNS resolver (IPs `54.159.25.239`,
     `100.49.158.148`) = servidor estático fora do ar.
   - DNS resolve mas a porta 443 não responde → é outage de infra, NÃO VPN do usuário.
3. **Confira o path do link encaminhado.** O path correto do formulário é
   `/pesquisa-pulse`, não `/pesquisa-pulses`. Se o comunicado saiu com path errado,
   isso é um segundo problema a reportar (além da queda).
4. **Escale para o time de People** (ver contatos abaixo) com o diagnóstico completo.

## Contatos do time de People no Slack (escalação)

Encontre SEMPRE via API (não hardcode cegamente — pessoas entram e saem):

```bash
# Lista membros ativos com título People/RH
curl -s -H "Authorization: Bearer ${SLACK_BOT_TOKEN}" \
  "https://slack.com/api/users.list?limit=300" | python3 -c "
import json,sys
for m in json.load(sys.stdin).get('members',[]):
    t=(m.get('profile',{}).get('title') or '')
    if any(k in t.lower() for k in ('people','rh','human','gente')) and not m.get('deleted',False):
        print(m['real_name'], m['id'], t, m.get('profile',{}).get('email','?'))
"
```

**Estado em 24/08/2026:**
| Pessoa | UID | Status |
|---|---|---|
| Amanda Almeida (Analista de Endomarketing, dept People, level 3) | `U031XPZ0AUT` | ✅ ativa — **escalar para ela** |
| Luana Caetano (People - DP) | `U02PMR8KNUT` | ❌ deletada do Slack |
| Luana Barros | `U042NTYEAMS` | ❌ deletada do Slack |
| Cá (Head de People) | `U027FPF32EN` | ❌ deletada |
| Scheizer Kuntze / Marcus Paulo | — | ❌ deletados |

⚠️ Quando o usuário disser "avisa a Amanda ou a Luana", confirme quem está **ativa** via
`users.list` — Luana saiu, Amanda Almeida é a referência viva do time de People.

## Envio da DM de escalação

Usar o mesmo padrão de `references/slack-dm-notification.md` (bot token + `chat.postMessage`).
Pode abrir a DM primeiro com `conversations.open` (users=[UID]) e postar no channel retornado,
ou passar o UID cru direto em `channel`. Incluir no corpo: quem reportou (nome/cargo/depto),
o sintoma, o diagnóstico (servidor offline + path correto), e o próximo passo (voltar quando
subir e avisar o colaborador com o link certo).

## Nota sobre acesso do container

O container da Falai também NÃO alcança `static-server.aiexpert-condoconta.info` quando ele
cai — o teste de `curl` acima serve justamente para provar que não é problema de VPN do
usuário: se falha daqui também, é a infra que caiu.
