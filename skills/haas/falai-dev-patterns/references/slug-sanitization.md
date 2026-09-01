# Slug sanitization — remover acentos e caracteres não-ASCII

## Problema
Nomes com acentos (André, José, João) quebram slugs do static-server. O servidor rejeita com `invalid_slug` se o slug contiver caracteres não-ASCII.

Exemplo de erro:
```
ERRO: 400 - {"error":"invalid_slug","message":"slug ausente ou inválido (use letras minúsculas, números e hífen)."}
```

## Solução
Aplicar sanitização após gerar o slug:

```python
import unicodedata, re

slug = "avaliacao-" + nome.lower().replace(" ","-")[:40]

# Strip accents
slug = ''.join(c for c in unicodedata.normalize('NFD', slug) if unicodedata.category(c) != 'Mn')
# Remove non-ASCII, keep only a-z, 0-9, hyphen
slug = re.sub(r'[^a-z0-9-]', '', slug)[:60]
```

Isso transforma:
- `André Romão de Oliveira` → `andre-romao-de-oliveira`
- `Lucas José de Souza` → `lucas-jose-de-souza`
- `João Guilherme` → `joao-guilherme`

## Onde aplicar
Em TODOS os scripts geradores de HTML que publicam no static-server:
- `gerar_form_avaliacao.py` ✅ (aplicado 28/08/2026)
- `gerar_form_lider.py` ❌ pendente
- `gerar_form_1x1.py` ❌ pendente
- Qualquer script futuro que publique HTML com slug derivado de nome de pessoa

## Reordenação de perguntas — manter `n` junto com a posição

### Autoavaliação: Q7 ↔ Q8 (swap)

Q7 (motivação) e Q8 (PDI) trocaram de lugar. O `n` do JSON DEVE acompanhar:

```python
perguntas_render = list(colaborador["perguntas"])
if len(perguntas_render) >= 8:
    # Swap posições (índices 6 e 7)
    perguntas_render[6], perguntas_render[7] = perguntas_render[7], perguntas_render[6]
    # Swap n também — senão o label mostra "8. Motivação" na posição 7
    perguntas_render[6]["n"], perguntas_render[7]["n"] = perguntas_render[7]["n"], perguntas_render[6]["n"]
```

### Avaliação do Líder: Q5→Q7, Q6→Q5, Q7→Q6 (rotação)

```python
if len(resultado) >= 7:
    resultado[4], resultado[5], resultado[6] = resultado[5], resultado[6], resultado[4]
    resultado[4]["n"], resultado[5]["n"], resultado[6]["n"] = 5, 6, 7
```

**Regra de ouro:** SEMPRE ajustar `p.n` quando trocar posições. Sem isso, o label HTML mostra a
numeração errada e o submit envia `q7` com a pergunta que deveria ser `q8`.