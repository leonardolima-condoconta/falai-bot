---
name: falai-form-patterns
description: "Padrões dos formulários People: proxy, cookies, validação."
version: 1.0.0
---

# Falai — Padrões de formulários People

## Proxy same-domain

Submit: `https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc`

| Regra | Motivo |
|---|---|
| Mesmo domínio do static-server | Zero CORS/preflight |
| Headers: só `Content-Type: application/json` | Tokens injetados server-side pelo proxy |
| NUNCA expor tokens no JS | Segurança |

## Cookie "já respondido"

```
document.cookie = '<nome>_respondido=1;max-age=864000;path=/'
```

- `max-age=864000` = 10 dias
- Load: verifica cookie → se true, esconde form e mostra agradecimento
- Submit OK: salva cookie + esconde form + mostra agradecimento
- Submit erro: NÃO salva cookie

## Validação de campos obrigatórios

Hidden inputs (escala/emoji) não validam nativamente. Usar JS:
- Coletar todos `[data-pergunta]`
- Verificar `.value` vazio
- Mostrar "⚠️ Preencha: [campo]" e `scrollIntoView` no primeiro vazio

## API routing

| Contexto | Endpoint |
|---|---|
| Container Python | `webhook-proxy.../webhooks/condopower-api` |
| Navegador (submit) | `/proxy/condopower-rpc` (same-domain) |

⚠️ NUNCA usar `/webhooks/condopower-api/rpc` — o proxy monta `/rpc` sozinho. Causa 404.

## access.verify client-side

Quando o container não alcança a API:
1. Embutir o email no HTML
2. No `load` da página, fazer `fetch` → `/proxy/condopower-rpc` → `access.verify`
3. Extrair `employee.id` e guardar em variável JS
4. Submit usa esse id; se ainda não resolvido, mostra "Aguarde..."

## Slug sanitization (OBRIGATÓRIO)

Todo slug de formulário DEVE ser sanitizado ANTES da publicação no static-server. Slugs com acentos, caracteres especiais ou não-ASCII causam `400 invalid_slug`.

```python
import unicodedata, re
slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
slug = re.sub(r'[^a-z0-9-]', '', slug)[:60]
```

- NUNCA publicar HTML sem sanitizar o slug
- Caracteres como `ã`, `ç`, `í`, `ú`, `·` quebram a publicação

## Campos senioridade e nivel_senioridade

Os JSONs `autoavaliacao_perguntas.json` e `avaliacao_lider_perguntas.json` agora incluem:
- `senioridade`: "Pleno", "Sênior", "Junior", "Coordenação"...
- `nivel_senioridade`: "I", "II", "III", "IV", "V"

**Nos geradores Python:**
```python
cnivel = colaborador.get("senioridade","") or colaborador.get("nivel","")
cstep = colaborador.get("nivel_senioridade","") or colaborador.get("step","")
```

**No HTML da `sub`:** `cargo · área · Pleno V · Ciclo 2026.2`

**No dropdown do líder:** incluir senioridade no texto da option e no label "Avaliando":
```javascript
var srLabel = l.senioridade ? ' · ' + l.senioridade + (l.nivel_senioridade ? ' ' + l.nivel_senioridade : '') : '';
// option: l.nome + ' — ' + l.cargo + srLabel
// label:  '<b>' + l.nome + '</b> · ' + l.cargo + srInfo + '</div>'
```

**Mapa de senioridade**: deve ser injetado no HTML como JSON para lookup client-side:
```python
senioridade_map = {}
for col in area["colaboradores"]:
    nome = col["nome"]
    sen = col.get("senioridade","") or col.get("nivel","")
    nv = col.get("nivel_senioridade","") or col.get("step","")
    if sen or nv:
        senioridade_map[nome.lower()] = {"senioridade": sen, "nivel_senioridade": nv}
senioridade_map_json = json.dumps(senioridade_map, ensure_ascii=False)
```

## Layout 1x1 (referência)

O formulário 1x1 (`gerar_form_1x1.py`) segue o layout full-screen:
- `body`: `height:100vh; overflow-y:auto; display:flex; flex-direction:column`
- `header`: `flex-shrink:0` (full-width)
- `.wrapper`: `flex:1; display:grid; grid-template-columns:3fr 2fr` (60/40)
- Coluna esquerda: comparativo + justificativa
- Coluna direita: 9box (60px células, 13px fonte) + PDI
- Scroll único no body (sem overflow independente por coluna)

## Batch generation (geração em lote)

Para regenerar todos os formulários após alterações nos JSONs:

```bash
# Líderes
cd /opt/data/convenia
for email in lider1@... lider2@...; do
  /opt/data/.venv/bin/python3 gerar_form_lider.py "$email"
done

# Autoavaliações — usar script temporário que:
# 1. Extrai nomes do JSON
# 2. Resolve emails via access.verify (nome2email)
# 3. Gera via gerar_form_avaliacao.py <email>
```

⚠️ Nem todos os colaboradores têm email resolvível pelo padrão `primeiro.ultimo@condoconta.com.br`. C-levels e nomes compostos precisam de tratamento especial.