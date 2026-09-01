# Pulse — Canais de Broadcast e Dados de Adesão

## Canais (verificado 28/08/2026 via conversations.info)

| Canal | ID | Membros | Uso |
|---|---|---|---|
| `#comunicação` | `C01H5UESZJN` | 131 | **Broadcast geral de People** — Pesquisa Pulse, aniversários, tempo de casa, oportunidades, novos CondoPowers, feriados. É AQUI que comunicados de Pulse vão. |
| `#people-hr` | `C0BJLA3H16F` | 7 | Time de People (interno). NÃO é canal de broadcast para o time inteiro. |

⚠️ **Pitfall recorrente:** jobs de lembrete Pulse agendados apontando para `#people-hr` só alcançam 7 pessoas.
O broadcast correto é `#comunicação` (C01H5UESZJN). Confirmar o canal antes de postar comunicado.

## Link canônico

- ✅ `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
- ❌ `pulse-satisfacao` — legado, REMOVIDO (timeout/timeout ao acessar)

## Adesão — `pulse.round_status`

- **`requester_email` PRECISA ser o e-mail de uma pessoa real do cadastro.**
  - ✅ `leonardo.lima@condoconta.com.br` (superadmin, level 5)
  - ✅ `luana.xavier@condoconta.com.br` (team_people, level 3)
  - ❌ `people@condoconta.com.br` → `404 EMPLOYEE_NOT_FOUND` (não existe no cadastro)
- Resposta traz `convidados`, `responderam`, `faltam`, `adesao_pct` (string, ex `"41.3"`).

## Envio do comunicado

- `chat.postMessage` com `SLACK_BOT_TOKEN` → posta como `@Falai People` (bot).
- Usar `<!channel>` para notificar todos no `#comunicação`.
- Prazo da rodada e adesão dinâmicos — consultar `pulse.round_status` ANTES de redigir o texto.
