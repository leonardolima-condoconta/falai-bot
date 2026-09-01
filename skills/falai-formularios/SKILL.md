---
name: falai-formularios
description: "Formularios HTML da Falai. Proxy, submit, tokens e cookies."
version: 1.0.0
---

# Falai Formulários — arquitetura e regras

## Geradores Python

| Método | Script | Status |
|---|---|---|
| `form.pulse` | `form-pulse.html` (estático) | ✅ |
| `form.autoavaliacao` | `/opt/data/convenia/gerar_form_avaliacao.py <email>` | ✅ |
| `form.avaliacao_lider` | `/opt/data/convenia/gerar_form_lider.py <email_lider>` | ✅ |
| `form.1x1` | `/opt/data/convenia/gerar_form_1x1.py <lider_email> <colab_email>` | ✅ |
| `form.pdi` | — | ❌ |
| `form.9box` | — | ❌ |

### 🔴 Pitfall: fuzzy name matching gera formulário da pessoa errada

`gerar_form_avaliacao.py` quebra o e-mail em partes e procura nos nomes do
`autoavaliacao_perguntas.json`. Quando duas pessoas compartilham as mesmas partes (ex: "Daniele
**Vanessa** Severo **Silva**" e "**Vanessa** da **Silva**" batem em `vanessa.silva@`), a
**primeira no JSON ganha** — e o formulário é publicado com nome e perguntas da pessoa errada.

Sintoma: o colaborador recebe um link com o nome de outra pessoa no título do HTML.

**Casos reais (31/08/2026 — ciclo 2026.2):** 7 de 108 formulários afetados:
| Email | Recebeu formulário de |
|---|---|
| `vanessa.silva@` | Daniele Vanessa Severo Silva |
| `caua.lima@` | Rafael Pacífico Segundo Lima |
| `leticia.santos@` | Magda Mayara dos Santos Monteiro |
| `juliana.simoes@` | Julia Eulalia Baldoino Marques |
| `danielly.costa@` | Paulo Fernando da Costa Pereira |
| `solange.pereira@` | Paulo Fernando da Costa Pereira |
| `vitoria.sousa@` | Vitor Pacheco |
| `joao.carvalho@` | Raphael de Carvalho Cortes |

**Caso adicional (31/08/2026):** `joao.carvalho@` → "João Guilherme Teixeira Brag" (31 chars truncado).
O fuzzy matching deu score 2 para `guilherme.giacometti@` e score 0 para o email correto —
batendo em "Guilherme Arquer Giacometti". Só o override map resolve.

**Causa raiz:** nomes no JSON são truncados a ~31 caracteres; o fuzzy matching quebra
o e-mail em partes e pontua contra os nomes. Quando duas pessoas compartilham partes do nome,
o primeiro no JSON vence.

### 🛠️ Fix: `email_override_map.json` + prioridade no script

**Arquivo de overrides** (`/opt/data/convenia/email_override_map.json`):
```json
{
  "vanessa.silva@condoconta.com.br": "Vanessa da Silva",
  "vitoria.sousa@condoconta.com.br": "Vitória Kimberllan Carvalho Lemos de Sousa",
  "caua.lima@condoconta.com.br": "Cauã Daniel Lima da Silva",
  "leticia.santos@condoconta.com.br": "Letícia Francisco dos Santos",
  "juliana.simoes@condoconta.com.br": "Juliana Xavier Simões",
  "danielly.costa@condoconta.com.br": "Danielly Maire Oliveira da Costa",
  "solange.pereira@condoconta.com.br": "Solange Gonçalves da Costa Pereira"
}
```

**Script corrigido** — adicionar Priority 1 ANTES do fuzzy matching:
```python
# Priority 1: exact override by email (corrige colisões de fuzzy matching)
override_name = _email_overrides.get(EMAIL.lower())
if override_name:
    override_lower = override_name.lower()
    for t, src, col in all_cols:
        nome_lower = col["nome"].lower()
        # Match by prefix (nomes no JSON são truncados a ~31 chars)
        if nome_lower == override_lower \
           or override_lower.startswith(nome_lower) \
           or nome_lower.startswith(override_lower[:len(nome_lower)]):
            tipo_form, source_data, colaborador = t, src, col
            break

# Priority 2: fuzzy matching (original)
if not colaborador:
    # ... fuzzy matching logic unchanged ...
```

O matching por prefixo é necessário porque os nomes no JSON são truncados a ~31 caracteres.

### Fluxo de correção pós-envio

Quando links errados já foram enviados via DM:
1. Adicionar entradas no `email_override_map.json`
2. Aplicar o patch acima no `gerar_form_avaliacao.py`
3. Regenerar: `python3 gerar_form_avaliacao.py <email>`
4. Editar a DM com `chat.update` trocando a URL

⛔ **Pitfall: atualizar DMs sem corrigir o JSON fonte.** Quando o prazo muda (ex: 1→4 dias)
e todas as DMs são regravadas via `chat.update` usando o JSON antigo de mensagens,
**todas as correções de URL anteriores são perdidas**. O JSON antigo continha os links
errados e a regravação em massa os restaura silenciosamente. Fluxo correto:
1. Atualizar o JSON fonte (`mensagens_autoavaliacao_2026.2.json`) com as URLs corretas
2. Só então regravar as DMs via `chat.update`
3. Auditar lendo as DMs reais do Slack para confirmar

### Templates de mensagem

Modelos prontos das mensagens de avaliação em `references/mensagens-avaliacao-templates.md`.

### Ordem unificada de perguntas

Para que o dash de 1:1 tenha comparativo assertivo, autoavaliação e avaliação de liderança
DEVEM seguir a mesma ordem: 1-Resultados, 2-Métrica, 3-Competências, 4-Autonomia,
5-Potencial, 6-V+, 7-V-, 8-PDI/Recomendação. Especificação completa em
`references/ordem-unificada-perguntas.md`.

## URL de submit — REGRA ABSOLUTA

**Sempre** proxy mesmo-domínio:
```
https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc
```

Por que: zero CORS — o navegador está no mesmo domínio do static-server, sem preflight OPTIONS.

NUNCA usar cross-origin no fetch do navegador:
- ❌ `condopower-api.aiexpert-condoconta.info/rpc`
- ❌ `webhook-proxy.condoconta.com.br/webhooks/condopower-api/rpc`

## Tokens no submit

Tokens SÃO obrigatórios mesmo via proxy. O proxy repassa `X-Service-Account-Token` e `auth`.

Padrão de referência (copiar da Pulses):
```javascript
fetch('/proxy/condopower-rpc', {
  method:'POST',
  headers:{
    'Content-Type':'application/json',
    'X-Service-Account-Token':'<token>',
    'auth':'<token>'
  },
  body:JSON.stringify({method:'form.xxx',params:{...}})
})
```

Injeção: placeholders `__SA_TOKEN__` / `__AUTH_TOKEN__` substituídos no Python, ou variáveis JS `SA`/`AUTH`.

## Cookies

- `max-age=864000` (10 dias) em TODOS os formulários
- Ao carregar → verifica cookie → se existe, esconde form, mostra agradecimento
- Submit OK → salva cookie → esconde form → agradecimento
- Erro → mensagem de erro, sem cookie

### Líder (caso especial)
Cookie é array JSON: `avaliacao_lider_feitos=["uuid1","uuid2"]`
Agradecimento só quando todos os liderados foram avaliados.

## Nomenclatura

- **"Pulses"** (plural) sempre: URLs, títulos, comunicados, CSVs
- Link canônico: `pesquisa-pulses`
- Link legado `pulse-satisfacao` foi removido

## Comunicação Slack

- NUNCA colocar links entre asteriscos. `*` = negrito, links dentro quebram.
- Correto: `*Link:* https://...`
- Errado: `*Link: https://...*`

## Formulário 1x1

Layout: comparativo autoavaliação (🟡) vs líder (🔵) à esquerda, 9box à direita superior, PDI abaixo do 9box. Busca dados via `form.autoavaliacao.get` e `form.avaliacao_lider.get`.