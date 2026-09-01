---
name: falai-jira
description: "Jira CondoConta: tipos pt-BR e pitfalls."
version: 1.0.0
---

# Jira CondoConta — Específicos para Agentes People

Domínio: `condoconta.atlassian.net`

## Projetos People

| Key | Nome | Uso |
|---|---|---|
| PADD | People Planning | Tarefas de RH: comunicados, onboardings, campanhas |
| PAIX | People AIX | AIX/experiência do colaborador |
| CDAP | Central de Ajuda People | Dúvidas e suporte de People |

## ⚠️ PITFALL #1 — Issue types são em PORTUGUÊS

O Jira CC usa nomes localizados. Usar nome em inglês retorna `400: "Especifique algum tipo de item válido"`.

| Inglês (ERRADO) | Português (CERTO) | ID (PADD) |
|---|---|---|
| `Task` | `Tarefa` | `10365` |
| `Employee` | `Funcionário` | `10366` |

**Regra de ouro:** antes de criar qualquer issue em projeto desconhecido, consulte:
```
GET /rest/api/3/issue/createmeta?projectKeys=<KEY>&expand=projects.issuetypes
```
Isso retorna nomes localizados e IDs exatos. NUNCA assuma que o nome em inglês funciona.

## ⚠️ PITFALL #2 — Autenticação

Credenciais no `.env`:
- `JIRA_DOMAIN=condoconta.atlassian.net`
- `JIRA_EMAIL=paulo.pereira@condoconta.com.br`
- `JIRA_API_TOKEN=ATATT3...` (192 chars, contém `{`, `}`, `!`)

O token tem caracteres especiais. NUNCA passe por interpolação de string no shell (echo, f-string) — será truncado. Use leitura binária (`od -An -tx1` + reconstrução de bytes).

## Exemplo: Criar issue no PADD

```python
auth = base64.b64encode(f"{email}:{token}".encode()).decode()
url = f"https://condoconta.atlassian.net/rest/api/3/issue"

data = {
    "fields": {
        "project": {"key": "PADD"},
        "summary": "Título da tarefa",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Descrição"}]}]
        },
        "issuetype": {"name": "Tarefa"},  # ⚠️ Português!
        "labels": ["comunicado", "people"]
    }
}
```

## RBAC (delega para atlassian-prd)

O controle de acesso completo está em `atlassian-prd` → `assets/rbac.json`. Esta skill cobre apenas as especificidades do Jira CondoConta que NÃO estão na skill genérica.