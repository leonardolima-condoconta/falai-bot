# Geradores de Formulários — Catálogo

## Scripts

| Script | Uso | Tipo |
|---|---|---|
| `gerar_form_avaliacao.py` | `python3 gerar_form_avaliacao.py <email>` | Autoavaliação (SOMENTE) |
| `gerar_form_lider.py` | `python3 gerar_form_lider.py <email_lider>` | Avaliação do líder (dropdown com liderados) |
| `pulse_csv.py` | `pulse_csv.py [create|register <id>|check <id>|export-and-clean]` | CSV temporário de participação do pulse |

## gerar_form_avaliacao.py
**Desde 21/08/2026:** só gera autoavaliação. Não aceita mais `[auto|lider]`.
- Lê `autoavaliacao_perguntas.json`
- Busca `colaborador_id` real via `access.verify` (fallback: vazio)
- Injeta `colaborador_id`, `colaborador_email`, `colaborador_nome`, `area` nos hidden inputs
- Submit → `form.autoavaliacao`
- Publica no static-server → retorna URL

## gerar_form_lider.py
- Chama `access.verify` para obter `reports[]` + `leader.id`
- Dropdown dinâmico com liderados
- Perguntas carregadas do `avaliacao_lider_perguntas.json`
- Injeta: `colaborador_id`, `colaborador_nome`, `area`, `lider_email`, `lider_id`
- Submit → `form.avaliacao_lider`

## pulse_csv.py
Gerenciador do CSV temporário `$PULSE_PATH_USERS`:
- `create` — cria CSV vazio com header, define env var
- `register <id>` — adiciona linha (id, true, timestamp)
- `check <id>` — retorna TRUE/FALSE/NOT_OPEN
- `export-and-clean` — upload no Slack #people-hr, exclui arquivo, limpa env var

## Arquivos de perguntas
- `/opt/data/convenia/autoavaliacao_perguntas.json` — 9 áreas, 121 colab., 968 perguntas
- `/opt/data/convenia/avaliacao_lider_perguntas.json` — 9 áreas, 120 colab., 960 perguntas
- Campos: nome, cargo, area, nivel, step, gestor, perguntas[] (n, pergunta, tipo, opcoes[])

## Pendentes (não criados)
- `gerar_form_1x1.py`
- `gerar_form_pdi.py`
- `gerar_form_9box.py`