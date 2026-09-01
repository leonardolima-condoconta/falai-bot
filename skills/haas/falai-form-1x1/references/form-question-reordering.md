# Reordenação de Perguntas nos Formulários

## Autoavaliação: Q7 ↔ Q8 (swap)

Motivo: Q7 (PDI/carreira) e Q8 (energia) trocaram de posição no formulário.

O script `gerar_form_avaliacao.py` faz o swap ANTES de renderizar:

```python
perguntas_render = list(colaborador["perguntas"])
if len(perguntas_render) >= 8:
    perguntas_render[6], perguntas_render[7] = perguntas_render[7], perguntas_render[6]
    perguntas_render[6]["n"], perguntas_render[7]["n"] = perguntas_render[7]["n"], perguntas_render[6]["n"]
```

**Importante:** trocar também o `n` (contador) para que os labels mostrem "7." e "8." na ordem correta e o submit envie os campos `q7` e `q8` corretos.

## Avaliação do Líder: Q5 → Q7, Q6 → Q5, Q7 → Q6 (rotação)

Motivo: Potencial vai pro final, SCI e Evoulir sobem uma posição.

O script `gerar_form_lider.py` faz a rotação no `filtrar_perguntas()`:

```python
if len(resultado) >= 7:
    resultado[4], resultado[5], resultado[6] = resultado[5], resultado[6], resultado[4]
    resultado[4]["n"], resultado[5]["n"], resultado[6]["n"] = 5, 6, 7
```

## Por que fazer no script e não no JSON?

O JSON é a fonte de verdade gerada a partir das planilhas. Alterar o JSON criaria divergência entre a planilha original e os dados. O script aplica a transformação na camada de apresentação.

## SQL para corrigir respostas já salvas

Se o banco tem respostas na ordem antiga, este SQL (PostgreSQL) troca Q7/Q8 no `raw`:

```sql
UPDATE forms
SET raw = jsonb_set(
  jsonb_set(raw,
    '{perguntas,"Enunciado Q7..."}',
    raw #> '{perguntas,"Enunciado Q8..."}'
  ),
  '{perguntas,"Enunciado Q8..."}',
  raw #> '{perguntas,"Enunciado Q7..."}'
)
WHERE tipo_formulario = 'form.autoavaliacao';
```