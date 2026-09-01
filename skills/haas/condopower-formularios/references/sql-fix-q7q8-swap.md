# SQL Migration: Fix Q7/Q8 swap in autoavaliacao responses

## SQLite

```sql
UPDATE forms
SET raw = json_set(
  json_set(
    raw,
    '$.perguntas."Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"',
    json_extract(raw, '$.perguntas."O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"')
  ),
  '$.perguntas."O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"',
  json_extract(raw, '$.perguntas."Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"')
)
WHERE tipo_formulario = 'form.autoavaliacao'
  AND json_extract(raw, '$.perguntas."Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"') IS NOT NULL
  AND json_extract(raw, '$.perguntas."O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"') IS NOT NULL;
```

Funções: `json_set`, `json_extract` — específicas do SQLite.

## PostgreSQL

```sql
UPDATE forms
SET raw = jsonb_set(
  jsonb_set(
    raw,
    '{perguntas,"Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"}',
    raw #> '{perguntas,"O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"}'
  ),
  '{perguntas,"O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"}',
  raw #> '{perguntas,"Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"}'
)
WHERE tipo_formulario = 'form.autoavaliacao'
  AND raw #> '{perguntas,"Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?"}' IS NOT NULL
  AND raw #> '{perguntas,"O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)"}' IS NOT NULL;
```

Funções: `jsonb_set`, `#>` — específicas do PostgreSQL.

## Segurança

- Idempotente: rodar duas vezes desfaz e refaz a troca
- Só afeta respostas onde AMBAS as chaves existem (evita corromper respostas parciais)
- Filtro por `tipo_formulario = 'form.autoavaliacao'` — não afeta outros tipos
- As chaves são os enunciados LONGOs das perguntas (o JSON salva assim, não `q7`/`q8`)

## Origem

Criado em 31/08/2026 após a troca de Q7/Q8 no `gerar_form_avaliacao.py`. Novas respostas já chegam na ordem correta; este script corrige as respostas antigas.