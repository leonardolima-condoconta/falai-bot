# Confluence — fallback de busca direta via curl

## Quando usar
Quando o script `confluence-search/scripts/confluence_search.py` estiver ilegível no container
(arquivo com permissão `-rw-------` de outro uid, ex. `1000`, e `Permission denied` ao executar),
buscar/ler direto na API REST do Confluence usando as credenciais do Jira.

## Credenciais (já no `/opt/data/.env`)
- `JIRA_DOMAIN=condoconta.atlassian.net`
- `JIRA_EMAIL=paulo.pereira@condoconta.com.br`
- `JIRA_API_TOKEN=<token>` (tem caracteres especiais — NUNCA via `echo $TOKEN`)
- Auth: `curl -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}"`

## Busca full-text (endpoint nativo `/wiki/rest/api/search`)
```bash
curl -s -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
  "https://${JIRA_DOMAIN}/wiki/rest/api/search?cql=$(python3 -c "import urllib.parse;print(urllib.parse.quote('text ~ \"termo\"'))")&limit=5"
```
Retorna `results[].content.title` e `results[].content._links.webui`. Cobre TODOS os spaces sem
especificar (não só os 4 DEFAULT_SPACES do script).

## Ler página por ID (body completo)
```bash
curl -s -u "${JIRA_EMAIL}:${JIRA_API_TOKEN}" \
  "https://${JIRA_DOMAIN}/wiki/rest/api/content/{PAGE_ID}?expand=body.storage"
```
Extrair texto: `re.sub(r'<[^>]+>', ' ', body)` → `html.unescape` → colapsar espaços.

## Exemplo real (PDI, 24/08/2026)
- Página "Plano de Desenvolvimento Individual" → space `SL`, page id `556335141`.
- Busca por "PDI" também retornou: `CDAP` "Etapa 5 — Definição do PDI" (2614231041),
  `SL` "One on One (1:1)" (555450413), "Gestão de Pessoas" (553451546).
