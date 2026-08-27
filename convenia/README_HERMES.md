# convenia — extrator isolado (para o agente Hermes)

Núcleo **somente-leitura** da API Convenia, isolado dos fluxos e do frontend.

> ## ⚠️ Leia o [`RELATORIO_API.md`](./RELATORIO_API.md) antes de escrever qualquer extração
>
> Este pacote foi originalmente desenhado supondo **acesso total** à API. **Não é o caso do
> Hermes.** A chave do Hermes opera sob um escopo restrito e **permanente**: dos 40+ schemas
> catalogados aqui, apenas 8 devolvem dados, e mesmo esses vêm com **campos censurados**.
>
> O `RELATORIO_API.md` é a **fonte de verdade** sobre o que existe de fato: schema por schema,
> campo por campo, com taxa de preenchimento medida contra a API real. Este README descreve
> *como usar* a biblioteca; o relatório descreve *o que dá para extrair*. Quando divergirem,
> o relatório vence.

| Módulo | Papel |
|---|---|
| `convenia.ConveniaClient` | Cliente HTTP: rate limit (50 req/min), retry em 429, paginação automática |
| `convenia.ConveniaStorage` | Persistência SQLite: achata o JSON, cria colunas dinamicamente, guarda o JSON bruto |
| `convenia.Settings` / `get_settings` | Config via `.env` (prefixo `CONVENIA_`) |
| `convenia.schemas` | Models Pydantic + `ConveniaSchema` por seção da API |
| `ConveniaError` (+ subclasses) | Hierarquia de erros tipados |

---

## O escopo do token — as duas regras que mudam tudo

**1. Endpoint fora do escopo devolve `403`, não dados.** É permanente para o Hermes; não é
falha transitória, não adianta retry.

**2. Campo fora do escopo devolve `null`, não erro.** Esta é a regra perigosa. A resposta
chega com status 200 e o campo presente — só que vazio. Na listagem de colaboradores,
**19 dos 30 campos vêm sempre nulos**, incluindo `salary`, `cpf`, `status`, `phone`, `pis`
e `rg`. Um pipeline ingênuo grava tudo isso como coluna nula e conclui que "o Convenia não
tem o dado", quando é só permissão faltando.

Consulte o escopo vigente pela própria API antes de assumir qualquer coisa:

```python
tok = client.fetch(schemas.system_data.TokenPermissionsSchema)[0]
print(tok.name)                                    # nome do token
for p in tok.permissions:
    print(p.name, [f.name for f in p.fields or []])  # endpoint + campos liberados
```

### O que o Hermes consegue extrair hoje

| Domínio | Situação |
|---|---|
| **Cadastro de pessoas** | ✅ nome, sobrenome, e-mail, aniversário, endereço, admissão, celular |
| **Estrutura organizacional** | ✅ departamento, cargo, centro de custo, gestor |
| **Núcleo familiar** | ✅ dependentes com relação e descrição legal |
| **Catálogo de benefícios** | ✅ os benefícios *da empresa* (não quem recebe o quê) |
| **Financeiro** | ❌ salário, histórico salarial, benefícios por colaborador |
| **Temporal** | ❌ férias, ausências, desligamentos |
| **Auditoria** | ❌ histórico de alterações |

---

## Instalação

O pacote é uma pasta `convenia/` — copie-a para dentro do projeto do Hermes. Dependências
(as mesmas do `pyproject.toml`):

```bash
pip install "httpx>=0.28.1" "pydantic>=2.13.4" "pydantic-settings>=2.14.2"
# ou: uv add httpx pydantic pydantic-settings
```

Só isso — sem FastAPI/uvicorn/jinja2/pandas/plotly.

## Configuração

```bash
cp convenia/.env.example .env   # e preencha CONVENIA_API_KEY
```

```dotenv
CONVENIA_API_KEY=sua-chave-aqui
# CONVENIA_BASE_URL, CONVENIA_TIMEOUT, CONVENIA_PAGE_SIZE têm default
```

> **O `.env` é resolvido a partir do diretório de execução**, não de onde o pacote está.
> O `.env` precisa estar na raiz de onde você roda o processo — a mesma raiz de onde
> `import convenia` funciona. Se as duas não coincidirem, `get_settings()` levanta
> `ValidationError` reclamando de `api_key`.

Para passar a chave em código (testes):

```python
from convenia import ConveniaClient, Settings
client = ConveniaClient(settings=Settings(api_key="chave-de-teste"))
```

---

## Padrão de uso: `fetch` → `save`

Extração é sempre a mesma dupla: o client busca a lista tipada, o storage grava numa tabela.
O exemplo abaixo é a **extração completa do que o Hermes tem acesso** — roda de ponta a ponta:

```python
from convenia import ConveniaClient, ConveniaStorage, schemas

with ConveniaClient() as client, ConveniaStorage("convenia.db") as db:
    # 1. Tabelas de apoio (listagens simples, sem parâmetro de caminho)
    db.save("departments",  client.fetch(schemas.departments.DepartmentsSchema))
    db.save("jobs",         client.fetch(schemas.jobs.JobsSchema))
    db.save("cost_centers", client.fetch(schemas.cost_centers.CostCentersSchema))
    db.save("benefits",     client.fetch(schemas.company.CompanyBenefitsSchema))

    # 2. Colaboradores
    employees = client.fetch(schemas.employees.EmployeesSchema)
    db.save("employees", employees)

    # 3. Endpoints com {employee_id} no caminho → passe como keyword.
    #    Custa 1 requisição por colaborador: 119 colaboradores ≈ 2 min no rate limit.
    for emp in employees:
        db.save("dependents",
                client.fetch(schemas.employees.DependentsSchema, employee_id=str(emp.id)))
```

- `client.fetch(Schema, **path_params)` devolve `list[BaseModel]` já **paginado** e validado.
- Endpoints com `{...}` no caminho exigem o parâmetro como keyword (`employee_id=`,
  `benefit_id=` …).
- `db.save(tabela, rows)` grava uma lista; `db.save_one(tabela, chave, obj)` grava um item
  (útil quando você precisa injetar campos antes de gravar).
- Em `dependents` **não** é preciso injetar `employee_id`: a API já devolve esse campo.

### Filtros

Endpoints de listagem aceitam um `filters_model` com `match` / `like` / `different`:

```python
f = schemas.employees.EmployeeFilters(like={"name": "Ana"})
resultado = client.fetch(schemas.employees.EmployeesSchema, filters=f)   # 2 registros

f = schemas.employees.EmployeeFilters(match={"name": "Alex"})            # igualdade exata
```

Filtros por período (`EmployeeDismissedFilters`, com `from_date`/`to_date`) existem, mas o
único endpoint que os usa — `DismissedEmployeesSchema` — está bloqueado.

---

## O modelo de dados que sai disso

Rodando o exemplo acima (extração completa em ~127s), o SQLite fica assim:

| Tabela | Linhas | Chave para join |
|---|---|---|
| `employees` | 119 | `id` |
| `jobs` | 227 | `id` |
| `cost_centers` | 21 | `id` |
| `departments` | 20 | `id` |
| `dependents` | 54 (de 40 colaboradores) | `employee_id` → `employees.id` |
| `benefits` | 4 | `id` |

### ⚠️ Os FKs não estão onde os schemas dizem

Os models declaram `department_id`, `job_description_id`, `cost_center_id` — e **todos vêm
`null`**. O vínculo real chega como **objeto aninhado** (`department`, `job`, `cost_center`,
`supervisor`, `address`), que o storage achata em colunas. O nome da coluna resultante nem
sempre bate com o campo declarado:

| Objeto na API | Vira coluna | Join |
|---|---|---|
| `department: {id, name}` | `department_id`, `department_name` | → `departments.id` ✅ 119/119 |
| `cost_center: {id, name}` | `cost_center_id`, `cost_center_name` | → `cost_centers.id` ✅ 119/119 |
| `job: {id, name}` | **`job_id`**, `job_name` | → `jobs.id` ✅ 119/119 |
| `supervisor: {id, name, last_name}` | `supervisor_id`, `supervisor_name`, … | → `employees.id` ✅ 117/119 |
| `address: {id, address, number, …}` | `address_id`, `address_address`, … | — |

Repare no `job`: o campo declarado é `job_description_id`, mas a coluna que existe de fato é
**`job_id`**. Já `department_id` e `cost_center_id` coincidem por acidente — o achatamento do
objeto sobrescreve o campo declarado nulo, e o UUID sobrevive. Funciona, mas depende da ordem
de iteração do dict, não de design. **Sempre confira o `PRAGMA table_info` antes de escrever
um join.**

Colunas efetivas de `employees` (25):

```
id, name, last_name, email, birth_date, hiring_date,
department_id, department_name, cost_center_id, cost_center_name,
job_id, job_name, supervisor_id, supervisor_name, supervisor_last_name,
address_id, address_address, address_number, address_complement,
address_zip_code, address_city, address_state, address_district,
raw, saved_at
```

Os 19 campos censurados (`salary`, `status`, `cpf`, `pis`, `rg`, `phone`, `corporate_email`,
`team_id`, e os `*_id` de gender/marital/nationality/education/relationship/admission/
payment/salary_type) **não viram coluna nenhuma** — chegam nulos na 1ª linha e o storage os
pula na criação da tabela. Não os procure no banco.

---

## Como o banco é usado (`ConveniaStorage`)

SQLite em modo WAL, com esquema **inferido dos próprios dados** — não há migrations:

- **Tabela criada a partir da 1ª linha.** Colunas nascem dos campos vistos; tipo inferido
  do valor (`INTEGER`/`REAL`/`TEXT`). Campos `None` são pulados na criação para não travar o
  tipo como `TEXT`.
- **Dicts aninhados são achatados** em colunas `pai_filho` (ex.: `address.city` → `address_city`).
- **Listas viram JSON** (texto).
- Toda tabela ganha `raw TEXT` (JSON original completo) e `saved_at TEXT`.
- Campos novos que aparecem depois entram via `ALTER TABLE ADD COLUMN` automaticamente.
- Chave primária `id` com `INSERT OR REPLACE` → re-extrair **atualiza** o registro, não duplica.

Consequências práticas para o Hermes:
- Rode a extração quantas vezes quiser: é idempotente por `id`.
- Precisa de um campo que não virou coluna (veio `None` na 1ª vez, ou é lista)? Leia de `raw`
  (`json.loads(row["raw"])`).
- Uma tabela = o nome que você passar em `save()`. Você escolhe os nomes; não há acoplamento
  fixo com os schemas.

> **A idempotência exige um campo `id`.** `EmployeeBenefitsResponse` e `TokenPermissionItem`
> são envelopes sem `id`: `save()` cai em `flat.get("id", "")` e usa chave `''` para **todas**
> as linhas, colapsando a tabela num único registro. Para esses, use `save_one()` com uma
> chave própria.

---

## Tratamento de erros

Todos herdam de `ConveniaError` (capture um só para pegar tudo):

| Erro | Situação |
|---|---|
| `ConveniaAuthError` (401) | Chave inválida/ausente |
| `ConveniaForbiddenError` (403) | **Fora do escopo do token — permanente, não tente de novo** |
| `ConveniaNotFoundError` (404) | Recurso inexistente |
| `ConveniaValidationError` (422) | Parâmetros inválidos |
| `ConveniaRateLimitError` (429) | Limite atingido (client já faz retry 3×/60s antes de estourar) |
| `ConveniaServerError` (5xx) | Erro no Convenia |
| `ConveniaConnectionError` | Falha de conexão/timeout |

Como 403 é estado permanente, **não** vale varrer os 119 colaboradores para descobrir isso —
o primeiro já responde pelos demais:

```python
from convenia import ConveniaError, ConveniaForbiddenError

def fetch_safe(client, schema, **path_params):
    try:
        return client.fetch(schema, **path_params)
    except ConveniaForbiddenError:
        return []          # fora do escopo: pule o schema inteiro, não só este registro
    except ConveniaError as e:
        print(f"[aviso] {schema.__name__}: {e}")
        return []
```

---

## Inventário de schemas

`{...}` no endpoint = precisa desse parâmetro como keyword no `fetch`.
Legenda: ✅ acessível · ❌ 403 permanente · ⚪ 200 mas vazio · ⛔ endpoint inexistente · ❔ não testado

### employees
| Schema | Endpoint | Acesso |
|---|---|---|
| `EmployeesSchema` | `/api/v3/employees` | ✅ 119 |
| `EmployeeDetailSchema` | `/api/v3/employees/{employee_id}` | ✅ |
| `DependentsSchema` | `/api/v3/employees/{employee_id}/dependents` | ✅ |
| `DismissedEmployeesSchema` | `/api/v3/employees/dismissed` | ❌ |
| `SalariesHistoricSchema` | `/api/v3/employees/{employee_id}/salaries-historic` | ❌ |
| `EmployeeBenefitsSchema` | `/api/v3/employees/{employee_id}/benefits` | ❌ |
| `AbsencesSchema` / `AbsenceReasonsSchema` / `AbsenceTypesSchema` / `AbsenceDetailSchema` | `/api/v3/employees/{employee_id}/absences[...]` | ❌ |
| `ChangeHistoriesSchema` / `ChangeHistoryDetailSchema` | `/api/v3/employees/{employee_id}/change-histories[...]` | ❌ |
| `VacationPeriodsSchema` / `VacationPeriodDetailSchema` | `/api/v3/employees/{employee_id}/vacations/periods[...]` | ❌ |
| `VacationSolicitationsSchema` / `VacationSolicitationDetailSchema` | `/api/v3/employees/{employee_id}/vacations/solicitations[...]` | ❌ |

### estrutura organizacional
| Schema | Endpoint | Acesso |
|---|---|---|
| `departments.DepartmentsSchema` | `/api/v3/companies/departments` | ✅ 20 |
| `cost_centers.CostCentersSchema` | `/api/v3/companies/cost-centers` | ✅ 21 |
| `jobs.JobsSchema` | `/api/v3/companies/jobs` | ✅ 227 |
| `teams.TeamsSchema` | `/api/v3/companies/teams` | ⚪ sem times cadastrados |

### company
| Schema | Endpoint | Acesso |
|---|---|---|
| `CompanyBenefitsSchema` | `/api/v3/companies/benefits` | ✅ 4 |
| `CompanyBenefitDetailSchema` | `/api/v3/companies/benefits/{benefit_id}` | ✅ |
| `BenefitEmployeesSchema` | `/api/v3/companies/benefits/{benefit_id}/employees` | ❌ |
| `CustomFieldsSchema` | `/api/v3/companies/custom-fields` | ❌ |
| `CollectiveVacationsSchema` | `/api/v3/companies/vacations/collective` | ⛔ 404 |

### payroll
| Schema | Endpoint | Acesso |
|---|---|---|
| `PayrollsSchema` | `/api/v3/payrolls` | ❌ |
| `PayrollDetailSchema` | `/api/v3/payrolls/{payroll_id}` | ❔ |

### system_data — tabelas de domínio
**Não seguem a lista de permissões do token**: algumas respondem sem constar no escopo,
outras dão 403. Teste antes de usar.

| Schema | Acesso |
|---|---|
| `BanksSchema` | ✅ 162 |
| `EducationsSchema` | ✅ 20 |
| `DependentRelationsSchema` | ✅ 11 |
| `GendersSchema` | ✅ 2 |
| `StatesSchema` | ❌ |
| `TokenPermissionsSchema` | ✅ — **não é listagem**: devolve 1 envelope `{name, permissions[]}` |
| `AddressDescriptionSchema`, `AdmissionTypesSchema`, `BankAccountTypesSchema`, `CitiesSchema`, `CountriesSchema`, `DisabilitiesSchema`, `DismissalTypesSchema`, `EmergencyContactRelationsSchema`, `EntryConditionsSchema`, `EthnicitiesSchema`, `GenderIdentitiesSchema`, `MaritalStatusSchema`, `NationalitiesSchema`, `PaymentMethodsSchema`, `RelationshipsSchema`, `ResidenceTimeSchema`, `SalaryTypesSchema`, `StabilityTypesSchema`, `TerminationTypesSchema`, `VisaTypesSchema`, `WorkerCategoriesSchema` | ❔ |

---

## Notas de manutenção

- **`extra: allow` não é universal.** Os models de `employees`, `company`, `jobs`,
  `departments`, `cost_centers`, `teams` e `payroll` têm — e é por isso que campos não
  declarados como `address`, `supervisor` e `cbo` chegam preservados. Os **26 models do
  `system_data` e o `DismissalInfo` não têm**: campos extras são silenciosamente descartados
  pelo Pydantic e, como o `raw` é gerado a partir do `model_dump()`, também não chegam ao
  banco. Nos endpoints testados a API só devolve `{id, name}`, então nada é perdido hoje —
  mas é risco latente.
- **Se o escopo do token for ampliado**, refaça a medição (`RELATORIO_API.md` documenta o
  procedimento) em vez de confiar nas tabelas acima.
- **`salaries-historic` devolve salário em centavos** (inteiro) e, às vezes, string no formato
  BR (`"8.500,00"`). Não foi possível confirmar — o endpoint é 403. Se algum dia abrir,
  normalize antes de gravar.
