# Template — Ticket de Bug no Jira PAIX para Erros da API

## Quando usar

Sempre que um endpoint da condopower-api retornar erro durante um fluxo People (1x1, feedback, PDI, avaliacao) — conforme tabela em `falai-fluxos-conversacionais`.

## Formato do Ticket

- **Projeto:** PAIX
- **Tipo:** Bug
- **Prioridade:** Medium (padrão)

### Resumo (summary)

```
BUG: <CODIGO_ERRO> — endpoint <METODO> <breve descricao do que aconteceu>
```

### Descricao (description) — usar sempre ADF (Atlassian Document Format)

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "O endpoint "},
        {"type": "text", "text": "<METODO>", "marks": [{"type": "code"}]},
        {"type": "text", "text": " da API condopower-api retornou "},
        {"type": "text", "text": "<CODIGO_ERRO>", "marks": [{"type": "strong"}]},
        {"type": "text", "text": "."}
      ]
    },
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "<MENSAGEM_ERRO>"}]
    },
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Caso concreto"}]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Colaborador: <NOME> (<CARGO> · <DEPTO>)"}
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Fluxo: <1x1|feedback|PDI|avaliacao>"}
      ]
    },
    {
      "type": "paragraph",
      "content": [
        {"type": "text", "text": "Dados preenchidos:"}
      ]
    },
    {
      "type": "bulletList",
      "content": [
        {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "<CAMPO>: <VALOR>"}]}]}
      ]
    },
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Erro retornado"}]
    },
    {
      "type": "codeBlock",
      "attrs": {"language": "json"},
      "content": [
        {"type": "text", "text": "<JSON_DO_ERRO_COMPLETO>"}
      ]
    },
    {
      "type": "heading",
      "attrs": {"level": 2},
      "content": [{"type": "text", "text": "Sugestao"}] 
    },
    {
      "type": "paragraph",
      "content": [{"type": "text", "text": "<sugestao contextual>"}]
    }
  ]
}
```

### Labels

- `api`
- label com o codigo do erro (ex: `NOT_YOUR_REPORT`)
- label descritivo do contexto (ex: `autoavaliacao`)

### Autenticacao

- Domain: `condoconta.atlassian.net`
- Email e token: extrair do `.env` (`JIRA_EMAIL`, `JIRA_API_TOKEN`)
- Autenticacao: Basic Auth (Base64)
- Endpoint: `POST https://condoconta.atlassian.net/rest/api/3/issue`

### Exemplo (este ticket foi criado em 20/08/2026)

PAIX-36 — `BUG: NOT_YOUR_REPORT — endpoint desempenho.register_avaliacao bloqueia autoavaliacao`