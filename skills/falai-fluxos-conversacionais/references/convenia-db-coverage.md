# Cobertura do Banco Local (Convenia → SQLite)

## O que ESTÁ sincronizado

| Tabela | Colunas |
|--------|---------|
| employees | id, name, last_name, email, birth_date, hiring_date, department_id, cost_center_id, job_id, supervisor_id, is_active, synced_at, senioridade, nivel_senioridade, cellphone |
| departments | id, name |
| jobs | id, name |
| cost_centers | id, name |

Total: 120 colaboradores ativos em 23 departamentos.

## ⚠️ Onde o banco está (e como consultá-lo)

O arquivo principal `/opt/data/convenia_data/convenia.db` costuma estar **vazio (0 bytes)** — o mesmo vale para `/opt/data/people.db` e `/opt/data/condoconta.db`. Os dados reais vivem em **backups diários**: `/opt/data/convenia_data/backups/convenia_YYYY-MM-DD.db` (use o mais recente).

- O CLI `sqlite3` **não está instalado** no container — consulte via Python (`import sqlite3`).
- A tabela `employees` **não tem coluna `slack_user_id`** — o casamento com o Slack é por `email`.
- Para "quem é meu líder?", use `employees.supervisor_id` (UUID do Convenia) e faça join com `departments`/`jobs` para cargo e área. A API `condopower-api` não responde isso: `access.verify` devolve `reports[]` (liderados), não o supervisor.

## O que NÃO está sincronizado (exige API Convenia)

| Dado | Onde vive | Token Falai-Bot |
|------|-----------|-----------------|
| **custom_fields** (frequência, modalidade, tipo vínculo, etc.) | `GET /api/v3/employees/{id}` → `data.custom_fields` | ✅ Acessível |
| Salário | `GET /api/v3/employees/{id}` → `data.salary` | ❌ 403 (sempre null) |
| Férias | `/api/v3/employees/{id}/vacations` | ❌ 403 |
| Ausências | `/api/v3/employees/{id}/absences` | ❌ 403 |
| Desligamentos | `/api/v3/terminations` | ❌ 403 |
| Dependentes | `/api/v3/employees/{id}/dependents` | ✅ Acessível (não syncado) |

## Perguntas comuns que NÃO podem ser respondidas só com o banco local

- "Quantos prestadores?" → exige API (custom_fields.tipo_vinculo)
- "Quem vem 5x na semana?" → exige API (custom_fields.frequencia)
- "Quem é remoto?" → exige API (custom_fields.modalidade)
- "Quem está de férias?" → exige API + token com escopo ampliado

## API Convenia — requisitos

- URL: `https://api.convenia.com.br/api/v3/`
- Token: em `/opt/data/convenia_data/.env` (`CONVENIA_API_KEY`)
- Rate limit: 50 req/min
- DNS: o container pode não resolver `api.convenia.com.br` — verificar antes de tentar