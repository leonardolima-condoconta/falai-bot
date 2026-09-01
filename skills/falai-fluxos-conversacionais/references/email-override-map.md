# Template: email_override_map.json

Cópia de referência do arquivo `/opt/data/convenia/email_override_map.json`.
Mapeia e-mails do Convenia para nomes exatos no JSON de autoavaliação
(nomes truncados a ~31 caracteres). Usado pelo `gerar_form_avaliacao.py`
como Prioridade 1 de matching — antes do fuzzy matching.

## Como usar

1. Identificar colisões: rodar auditoria de fuzzy matching simulando o algoritmo
   original contra todos os colaboradores do Convenia
2. Para cada colisão, adicionar entrada: `"email@condoconta.com.br": "Nome exato no JSON"`
3. O script lê este arquivo a cada execução — não precisa reiniciar nada

## Template

```json
{
  "email1@condoconta.com.br": "Nome Exato como aparece no JSON",
  "email2@condoconta.com.br": "Outro Nome Truncado no JSON"
}
```

## Entradas atuais (31/08/2026)

```json
{
  "vanessa.silva@condoconta.com.br": "Vanessa da Silva",
  "vitoria.sousa@condoconta.com.br": "Vitória Kimberllan Carvalho Lemos de Sousa",
  "caua.lima@condoconta.com.br": "Cauã Daniel Lima da Silva",
  "leticia.santos@condoconta.com.br": "Letícia Francisco dos Santos",
  "juliana.simoes@condoconta.com.br": "Juliana Xavier Simões",
  "danielly.costa@condoconta.com.br": "Danielly Maire Oliveira da Costa",
  "solange.pereira@condoconta.com.br": "Solange Gonçalves da Costa Pereira",
  "joao.carvalho@condoconta.com.br": "João Guilherme Teixeira Brag",
  "caju@condoconta.com.br": "Paulo Fernando da Costa Pere"
}
```

## Como o matching funciona no script patchado

```python
# Prioridade 1: override por email → match por prefixo (nomes truncados)
override_name = _email_overrides.get(EMAIL.lower())
if override_name:
    for col in all_cols:
        if col["nome"].lower() == override_name.lower() or \
           override_name.lower().startswith(col["nome"].lower()) or \
           col["nome"].lower().startswith(override_name[:len(col["nome"].lower())]):
            # encontrado!

# Prioridade 2: fuzzy matching original
if not colaborador:
    parts = EMAIL.lower().replace("@condoconta.com.br","").split(".")
    # ... algoritmo de score por partes do nome
```