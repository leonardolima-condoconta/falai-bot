# Padrão de Reordenação de Perguntas em Formulários

## Quando usar

Quando o usuário pedir para trocar perguntas de lugar nos formulários de avaliação (ex: "troca Q7 com Q8", "Q5 vai pra Q7, Q6 vai pra Q5, Q7 vai pra Q6").

## Regra absoluta: trocar posição E número

**NÃO basta inverter a ordem visual.** O campo `n` (número da pergunta) PRECISA ser trocado junto, senão:
- O label mostra `8.` na posição 7 (ou vice-versa)
- O submit envia `q8` com a resposta da pergunta 7 (ou vice-versa)
- A API/banco recebe os dados com o mapeamento invertido

## Padrão Python (gerador de HTML)

```python
# Autoavaliação — swap Q7 ↔ Q8 (índices 6 e 7)
perguntas_render = list(colaborador["perguntas"])
if len(perguntas_render) >= 8:
    # Trocar posição
    perguntas_render[6], perguntas_render[7] = perguntas_render[7], perguntas_render[6]
    # Trocar número (n) — CRÍTICO
    perguntas_render[6]["n"], perguntas_render[7]["n"] = perguntas_render[7]["n"], perguntas_render[6]["n"]
```

## Padrão Python (rotação Q5→Q7, Q6→Q5, Q7→Q6)

```python
# Líder — rotacionar Q5, Q6, Q7 (índices 4, 5, 6)
if len(resultado) >= 7:
    resultado[4], resultado[5], resultado[6] = resultado[5], resultado[6], resultado[4]
    resultado[4]["n"], resultado[5]["n"], resultado[6]["n"] = 5, 6, 7
```

## Padrão SQL (corrigir respostas já salvas no banco)

Quando a ordem do formulário muda, as respostas anteriores a 2026-08-31 estão na ordem antiga e precisam ser corrigidas no banco.

**SQLite:**
```sql
UPDATE forms
SET raw = json_set(
  json_set(raw,
    '$.perguntas."Pergunta A"',
    json_extract(raw, '$.perguntas."Pergunta B"')
  ),
  '$.perguntas."Pergunta B"',
  json_extract(raw, '$.perguntas."Pergunta A"')
)
WHERE tipo_formulario = 'form.autoavaliacao'
  AND json_extract(raw, '$.perguntas."Pergunta A"') IS NOT NULL
  AND json_extract(raw, '$.perguntas."Pergunta B"') IS NOT NULL;
```

**PostgreSQL:**
```sql
UPDATE forms
SET raw = jsonb_set(
  jsonb_set(raw,
    '{perguntas,"Pergunta A"}',
    raw #> '{perguntas,"Pergunta B"}'
  ),
  '{perguntas,"Pergunta B"}',
  raw #> '{perguntas,"Pergunta A"}'
)
WHERE tipo_formulario = 'form.autoavaliacao'
  AND raw #> '{perguntas,"Pergunta A"}' IS NOT NULL
  AND raw #> '{perguntas,"Pergunta B"}' IS NOT NULL;
```

## Pitfalls

1. **Trocar só posição sem `n`** → labels errados, submit com chaves invertidas
2. **Usar `p["n"]` original sem reatribuir** → o `n` do objeto foi mutado em uma cópia rasa mas não na original
3. **Esquecer de rodar SQL de correção** → respostas antigas ficam com o mapeamento errado no banco
4. **SQLite ≠ PostgreSQL:** as funções são `json_set`/`json_extract` vs `jsonb_set`/`#>`