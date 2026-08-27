---
name: convenia-api-contract
description: "Contrato real da API Convenia: endpoints, CBO e senioridade."
version: 1.1.0
---

# Convenia API — Contrato real (People)

Fonte de dados cadastrais do agente Falai. Este skill registra o contrato REAL da API
(supersede `convenia-rh`, que está desatualizado em pontos-chave).

## Endpoints

| Recurso | Endpoint |
|---|---|
| Departamentos | `GET /api/v3/companies/departments` |
| Centros de custo | `GET /api/v3/companies/cost-centers` |
| Cargos | `GET /api/v3/companies/jobs` |
| Colaboradores (lista) | `GET /api/v3/employees` |
| Colaborador (detalhe) | `GET /api/v3/employees/{id}` |
| Permissões do token | `GET /api/v3/tokens/permissions` |

## ⚠️ Correção: jobs trazem CBO (convenia-rh está errado)

`convenia-rh` afirma que cargos vêm "apenas id e name, sem descrição nem CBO". FALSO.
A resposta real de `/api/v3/companies/jobs` é:

```json
{"id": "66fca192-...", "name": "AI Expert Analyst", "description": null,
 "cbo_code": "351905", "cbo": {"name": "Agente de inteligência"}}
```

`cbo_code` e `cbo.name` vêm preenchidos; apenas `description` é `null`. Logo, a coluna
`jobs.cbo_code NOT NULL REFERENCES cbo_occupations` do SQLite NÃO é bloqueador de carga.

## Senioridade e nível — endpoint individual, NÃO a lista

A lista `/api/v3/employees` não expõe `custom_fields`. Eles só vêm em
`GET /api/v3/employees/{id}`:

```json
{"custom_fields": [
  {"name": "Senioridade", "value": "Pleno"},
  {"name": "Nivel de Senioridade", "value": "V"},
  {"name": "Dias Presenciais na Semana", "value": "3"}
]}
```

Extrair filtrando `cf.name == "Senioridade"` e `cf.name == "Nivel de Senioridade"`.
O detalhe também traz `cellphone` e `social_name`, ausentes da lista.

## Como consultar um colaborador individual (fetch_one não existe)

O `ConveniaClient` **não** expõe `fetch_one()`. Para buscar um colaborador pelo ID,
use o cliente interno `httpx`:

```python
from convenia import ConveniaClient
with ConveniaClient() as client:
    resp = client._client.get(f"/api/v3/employees/{employee_id}")
    data = resp.json()
    emp = data["data"]  # contém name + last_name + cellphone + birth_date + custom_fields
```

Isso é necessário porque `EmployeesSchema` só mapeia o endpoint de lista (`/api/v3/employees`),
que retorna campos truncados (ex: `name` = só primeiro nome, sem `cellphone`, sem `custom_fields`).

⚠️ **NUNCA use `curl` ou `requests` direto para `api.convenia.com.br`** — a resolução DNS
falha dentro do container (`NameResolutionError`). O `ConveniaClient` (httpx) resolve
corretamente e é o único caminho funcional.

## Campos disponíveis na lista vs detalhe

| Campo | Lista (`/api/v3/employees`) | Detalhe (`/api/v3/employees/{id}`) |
|---|---|---|
| `name` | só primeiro nome | só primeiro nome |
| `last_name` | ✅ (só sobrenome) | ✅ (só sobrenome) |
| `full_name` (composto) | `{name} {last_name}` | `{name} {last_name}` |
| `email` | ✅ | ✅ |
| `cellphone` | ❌ | ✅ |
| `birth_date` | ✅ | ✅ |
| `hiring_date` | ✅ | ✅ |
| `cpf` | `null` (token Falai-Bot) | ❌ (não incluso) |
| `custom_fields` | ❌ | ✅ |
| `department` / `job` / `cost_center` / `supervisor` | ✅ (dict) | ✅ (dict) |
| `social_name` | ❌ | ✅ |
| `relationship` / `relationship_id` | ❌ | ✅ |

**CPF é inacessível** com o token `Falai-Bot` — retorna `null` na lista e está ausente
no detalhe. É restrição de permissão do token, não de endpoint. Se necessário, acessar
o painel do Convenia (`app.convenia.com.br`) ou solicitar token com escopo ampliado.

## Ambiente / isolamento de .env (CRÍTICO)

- `Settings` usa `env_prefix="CONVENIA_"` e lê `.env` do diretório de execução.
- Rodar de `/opt/data/` puxa o `.env` global do Hermes e explode com dezenas de
  `extra_forbidden`.
- SEMPRE rodar de `/opt/data/convenia/` (tem `.env` isolado com apenas `CONVENIA_API_KEY`).
- `PYTHONPATH` aponta para o diretório PAI (`/opt/data`), nunca para `/opt/data/convenia`.
- Usar o venv do projeto: `/opt/data/.venv/bin/python3`.

## Notas

- `salary` é sempre `null` no token `Falai-Bot`; férias/ausências/desligamentos são 403.
- Rate limit 50 req/min; extração completa (~127s) é segura.
- Campos aninhados (`job`, `department`, `cost_center`, `supervisor`) são dicts, não objetos.
- Schema completo da resposta de detalhe: `references/employee-detail-response.json`.

## Vínculo empregatício (`relationship`)

Disponível **apenas no detalhe** (`/api/v3/employees/{id}`), NÃO na lista. Formato:
```json
{"relationship_id": 6, "relationship": {"id": 6, "name": "Trabalhador Autônomo"}}
```

Valores observados na base CondoConta:
- `Trabalhador Autônomo` (id 6) — maioria dos ativos (~42 de 49 ativos em ago/2026)
- `CLT` — minoria (~7)

### Colaboradores inativos (pitfall)

Colaboradores desligados podem retornar resposta **sem chave `"data"`** no detalhe:
```python
detail = resp.json()
if "data" not in detail:
    # colaborador inativo/desligado — pular ou tratar como sem vínculo
```
Nesses casos, não há `relationship`, `custom_fields`, nem demais campos de detalhe.
Para varrer toda a base filtrando ativos, tratar `"data" not in detail` como skip.