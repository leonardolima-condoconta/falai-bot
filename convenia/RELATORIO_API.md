# Relatório de Teste — API Convenia

Extração de **1 registro por schema**, com foco em colaboradores, medida contra a API real. Três execuções acompanhando as mudanças de permissão da chave.

> **A Execução 3 é o estado final e permanente.** É ela que vale para o Hermes; as duas primeiras ficam registradas só para mostrar o efeito de cada mudança de escopo. O modelo de dados derivado daqui está em [`schema.sql`](./schema.sql).

| | Exec. 1 | Exec. 2 | Exec. 3 |
|---|---|---|---|
| Permissões do token | 3 | 9 | **5** |
| Schemas testados | 16 | 19 | 17 |
| Schemas com dados | 3 | 8 | **5** |
| Bloqueados (403) | 13 | 10 | 12 |

Base: `https://public-api.convenia.com.br` · 119 colaboradores ativos · autenticação OK nas três execuções (nenhum 401).

## 1. Comparação por schema

| Schema | Endpoint | Exec. 1 | Exec. 2 | Exec. 3 | Situação final |
|---|---|---|---|---|---|
| `employees.EmployeesSchema` | `/api/v3/employees` | ✅ 119 | ✅ 119 | ✅ 119 | ✅ **disponível** |
| `employees.EmployeeDetailSchema` | `/api/v3/employees/{employee_id}` | ✅ 1 | ✅ 1 | ✅ 1 | ✅ **disponível** |
| `employees.DismissedEmployeesSchema` | `/api/v3/employees/dismissed` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.SalariesHistoricSchema` | `/api/v3/employees/{employee_id}/salaries-historic` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.DependentsSchema` | `/api/v3/employees/{employee_id}/dependents` | ✅ 1 | ✅ 1 | ❌ 403 | 🔒 **perdeu acesso** |
| `employees.EmployeeBenefitsSchema` | `/api/v3/employees/{employee_id}/benefits` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.AbsencesSchema` | `/api/v3/employees/{employee_id}/absences` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.AbsenceReasonsSchema` | `/api/v3/employees/{employee_id}/absences/reasons` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.AbsenceTypesSchema` | `/api/v3/employees/{employee_id}/absences/types` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.ChangeHistoriesSchema` | `/api/v3/employees/{employee_id}/change-histories` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.VacationPeriodsSchema` | `/api/v3/employees/{employee_id}/vacations/periods` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `employees.VacationSolicitationsSchema` | `/api/v3/employees/{employee_id}/vacations/solicitations` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ bloqueado |
| `departments.DepartmentsSchema` | `/api/v3/companies/departments` | ❌ 403 | ✅ 20 | ✅ 20 | ✅ **disponível** |
| `jobs.JobsSchema` | `/api/v3/companies/jobs` | ❌ 403 | ✅ 227 | ✅ 227 | ✅ **disponível** |
| `cost_centers.CostCentersSchema` | `/api/v3/companies/cost-centers` | ❌ 403 | ✅ 21 | ✅ 21 | ✅ **disponível** |
| `teams.TeamsSchema` | `/api/v3/companies/teams` | ❌ 403 | ⚪ vazio | ❌ 403 | 🔒 **perdeu acesso** |
| `company.CompanyBenefitsSchema` | `/api/v3/companies/benefits` | — não testado | ✅ 4 | ❌ 403 | 🔒 **perdeu acesso** |
| `company.CompanyBenefitDetailSchema` | `/api/v3/companies/benefits/{benefit_id}` | — não testado | ✅ 1 | — não testado | — não testado |
| `company.BenefitEmployeesSchema` | `/api/v3/companies/benefits/{benefit_id}/employees` | — não testado | ❌ 403 | — não testado | — não testado |

*Números nas colunas de execução = registros retornados. 🔒 marca o que já esteve acessível e foi revogado.*

## 2. Escopo do token

A API aplica escopo **por endpoint e por campo**: campo fora do escopo volta como `null`, não como erro.

| Permissão | Descrição | Exec. 1 | Exec. 2 | Exec. 3 |
|---|---|---|---|---|
| `employees.get.employees` | Listagem de colaboradores | 9 campos | 10 campos | **10 campos** |
| `employees.show.employee` | Detalhe de colaborador | 9 campos | 12 campos | **11 campos** |
| `employees.get.dependents` | Dependentes do colaborador | 9 campos | 9 campos | 🔒 revogada |
| `companies.get.company.cost.centers` | Listagem de centros de custo | — | 1 campo | **1 campo** |
| `companies.get.company.departments` | Listagem de departamentos | — | 1 campo | **1 campo** |
| `companies.get.company.jobs` | Listagem de cargos | — | 4 campos | **4 campos** |
| `companies.get.teams` | Listagem de times | — | 2 campos | 🔒 revogada |
| `companies.get.benefits` | Listagem de benefícios de uma empresa | — | 16 campos | 🔒 revogada |
| `companies.show.benefit` | Detalhe de um benefício de uma empresa | — | 16 campos | 🔒 revogada |

Escopo final: **5 permissões**, cobrindo colaboradores (listagem e detalhe), departamentos, cargos e centros de custo.

## 3. Campos retornados por schema (execução 3 — estado final)

`decl.` = campo declarado no schema Pydantic · `extra` = veio da API sem estar declarado (preservado via `extra: allow`). Preenchimento = % de registros com valor não-vazio.

### `employees.EmployeesSchema` — 119 registro(s)

| Campo | Origem | Preench. | Exemplo |
|---|---|---|---|
| `address` | extra | 100% | `{"id": "b94ac857-2126-4c8e-a021-df05add8…` |
| `admission_type_id` | decl. | 0% | `null` |
| `birth_date` | decl. | 100% | `199***09` |
| `corporate_email` | decl. | 0% | `null` |
| `cost_center` | extra | 100% | `{"name": "Product", "id": "bd052922-8e2f…` |
| `cost_center_id` | decl. | 0% | `null` |
| `cpf` | decl. | 0% | `null` |
| `department` | extra | 100% | `{"name": "Product", "id": "2f483c19-4d1e…` |
| `department_id` | decl. | 0% | `null` |
| `education_id` | decl. | 0% | `null` |
| `email` | decl. | 85% | `al***@condoconta.com.br` |
| `gender_id` | decl. | 0% | `null` |
| `hiring_date` | decl. | 100% | `2025-03-25` |
| `id` | decl. | 100% | `8fa03131-9c8c-4265-9f47-c02df739c1d4` |
| `job` | extra | 100% | `{"name": "Product Owner", "id": "5a1c1a2…` |
| `job_description_id` | decl. | 0% | `null` |
| `last_name` | extra | 100% | `Ricobom` |
| `marital_status_id` | decl. | 0% | `null` |
| `name` | decl. | 100% | `Alex` |
| `nationality_id` | decl. | 0% | `null` |
| `payment_method_id` | decl. | 0% | `null` |
| `phone` | decl. | 0% | `null` |
| `pis` | decl. | 0% | `null` |
| `relationship_id` | decl. | 0% | `null` |
| `rg` | decl. | 0% | `null` |
| `salary` | decl. | 0% | `null` |
| `salary_type_id` | decl. | 0% | `null` |
| `status` | decl. | 0% | `null` |
| `supervisor` | extra | 100% | `{"id": "3f929dc8-1e42-46aa-80b0-450a9a76…` |
| `team_id` | decl. | 0% | `null` |

### `employees.EmployeeDetailSchema` — 1 registro(s)

| Campo | Origem | Preench. | Exemplo |
|---|---|---|---|
| `admission_type_id` | decl. | 0% | `null` |
| `birth_date` | decl. | 100% | `199***09` |
| `cellphone` | extra | 100% | `419***95` |
| `corporate_email` | decl. | 0% | `null` |
| `cost_center` | extra | 100% | `{"id": "bd052922-8e2f-401c-ba89-688383cd…` |
| `cost_center_id` | decl. | 0% | `null` |
| `cpf` | decl. | 0% | `null` |
| `department` | extra | 100% | `{"id": "2f483c19-4d1e-4fc1-8bf2-6d1c96f7…` |
| `department_id` | decl. | 0% | `null` |
| `education_id` | decl. | 0% | `null` |
| `email` | decl. | 100% | `al***@condoconta.com.br` |
| `gender_id` | decl. | 0% | `null` |
| `hiring_date` | decl. | 100% | `2025-03-25` |
| `id` | decl. | 100% | `8fa03131-9c8c-4265-9f47-c02df739c1d4` |
| `job` | extra | 100% | `{"id": "5a1c1a28-6794-4ddc-a6d2-61fcd23e…` |
| `job_description_id` | decl. | 0% | `null` |
| `last_name` | extra | 100% | `Ricobom` |
| `marital_status_id` | decl. | 0% | `null` |
| `name` | decl. | 100% | `Alex` |
| `nationality_id` | decl. | 0% | `null` |
| `payment_method_id` | decl. | 0% | `null` |
| `phone` | decl. | 0% | `null` |
| `pis` | decl. | 0% | `null` |
| `relationship_id` | decl. | 0% | `null` |
| `rg` | decl. | 0% | `null` |
| `salary` | decl. | 0% | `null` |
| `salary_type_id` | decl. | 0% | `null` |
| `social_name` | extra | 0% | `null` |
| `status` | decl. | 0% | `null` |
| `supervisor` | extra | 100% | `{"id": "3f929dc8-1e42-46aa-80b0-450a9a76…` |
| `team_id` | decl. | 0% | `null` |

### `departments.DepartmentsSchema` — 20 registro(s)

| Campo | Origem | Preench. | Exemplo |
|---|---|---|---|
| `id` | decl. | 100% | `091dfb96-ad18-4d4b-8c8b-5affaac46032` |
| `name` | decl. | 100% | `Collection` |

### `jobs.JobsSchema` — 227 registro(s)

| Campo | Origem | Preench. | Exemplo |
|---|---|---|---|
| `cbo` | extra | 100% | `{"name": "Agente de inteligência"}` |
| `cbo_code` | extra | 100% | `351905` |
| `description` | extra | 2% | `null` |
| `id` | decl. | 100% | `66fca192-17a6-443c-8345-5163fc4bfcb9` |
| `name` | decl. | 100% | `AI Expert Analyst` |

### `cost_centers.CostCentersSchema` — 21 registro(s)

| Campo | Origem | Preench. | Exemplo |
|---|---|---|---|
| `id` | decl. | 100% | `06906ef3-0a6d-4079-aa96-2b99b577f90f` |
| `name` | decl. | 100% | `Sales` |

## 4. Bloqueados em definitivo (403 Forbidden)

| Schema | Endpoint |
|---|---|
| `employees.DismissedEmployeesSchema` | `/api/v3/employees/dismissed` |
| `employees.SalariesHistoricSchema` | `/api/v3/employees/{employee_id}/salaries-historic` |
| `employees.DependentsSchema` | `/api/v3/employees/{employee_id}/dependents` |
| `employees.EmployeeBenefitsSchema` | `/api/v3/employees/{employee_id}/benefits` |
| `employees.AbsencesSchema` | `/api/v3/employees/{employee_id}/absences` |
| `employees.AbsenceReasonsSchema` | `/api/v3/employees/{employee_id}/absences/reasons` |
| `employees.AbsenceTypesSchema` | `/api/v3/employees/{employee_id}/absences/types` |
| `employees.ChangeHistoriesSchema` | `/api/v3/employees/{employee_id}/change-histories` |
| `employees.VacationPeriodsSchema` | `/api/v3/employees/{employee_id}/vacations/periods` |
| `employees.VacationSolicitationsSchema` | `/api/v3/employees/{employee_id}/vacations/solicitations` |
| `teams.TeamsSchema` | `/api/v3/companies/teams` |
| `company.CompanyBenefitsSchema` | `/api/v3/companies/benefits` |

Não testáveis, pois dependem de um ID vindo das listagens bloqueadas: `AbsenceDetailSchema`, `ChangeHistoryDetailSchema`, `VacationPeriodDetailSchema`, `VacationSolicitationDetailSchema`. Também fora de alcance: `teams`, `company.CompanyBenefits*`, `employees.Dependents` (revogados na Exec. 3), `company.CustomFields`, `payroll.*` e `system_data.States`. `company.CollectiveVacations` responde **404** — endpoint inexistente, não é permissão.

Domínios permanentemente inacessíveis: **financeiro** (salário, histórico salarial, benefícios), **temporal** (férias, ausências, desligamentos), **auditoria** (histórico de alterações) e **núcleo familiar** (dependentes).

## 5. Observações técnicas

**`TokenPermissionsSchema` — corrigido.** Declarava `permissions: list[str]` e misturava envelope com item, estourando `ValidationError`. A resposta é um envelope `{name, permissions[]}` (o `name` é o nome do token, aqui `Falai-Bot`), com cada permissão no formato `{id, name, translated_name, fields[]}`. Agora são três models: `TokenPermissionItem` (envelope) → `TokenPermission` (permissão) → `TokenPermissionField` (campo liberado). O escopo do token passa a ser consultável pelo próprio client:

```python
tok = client.fetch(schemas.system_data.TokenPermissionsSchema)[0]
for p in tok.permissions:
    print(p.name, [f.name for f in p.fields or []])
```

**A API devolve objetos aninhados, não os FK ids.** Os schemas esperam `department_id`/`job_description_id`/`cost_center_id`, mas chegam `department`, `job`, `cost_center`, `supervisor` e `address` como objetos (campos `extra`) — enquanto as colunas `*_id` declaradas vêm 100% `null`. O vínculo com departamentos/cargos/centros de custo existe, só está dentro do objeto do colaborador.

**Colisão no `_flatten` do storage.** `department: {id, name}` achata para `department_id`, que colide com o campo declarado `department_id` (null). Verificado: o UUID aninhado sobrescreve o null e sobrevive — funciona, mas por ordem de iteração do dict, não por design. Vale o mesmo para `cost_center_id`.

**`teams` é inalcançável por dois motivos independentes.** Na Exec. 2, com a permissão concedida, o endpoint respondia 200 com **lista vazia** — não há times cadastrados na empresa. Na Exec. 3 a permissão foi revogada e virou 403. De todo modo `team_id` fica sempre `null` nos colaboradores.

**`jobs.description` vem preenchido em apenas 2% dos 227 cargos** (4 de 227) — não serve como campo confiável.

**A API mistura `''` e `null`.** `cellphone` chega como string vazia em 2 colaboradores e como `null` em 1 — mesmo significado, representações diferentes. É o único campo com essa inconsistência; todos os outros usam `null`. Como `cellphone` acabou fora do modelo, hoje não afeta a carga — mas mantenha `nullif(valor, '')` na ingestão, porque nada garante que a API não faça o mesmo em outro campo.

**O endpoint de detalhe é redundante.** Comparados os 119 colaboradores campo a campo entre `/employees` e `/employees/{id}`: os 15 campos comuns têm **concordância de 100%, zero divergência**. A listagem é superconjunto — traz `address` (8 campos) que o detalhe não tem; o detalhe acrescenta apenas `cellphone` (97% preenchido) e `social_name` (35%), ambos fora do escopo de uso do Hermes. Chamá-lo custa +119 requisições e 145s para trazer zero informação nova.

**Os catálogos, ao contrário, não são deriváveis dos colaboradores.** O objeto aninhado em `employees` traz só `{id, name}` e só do que está em uso: derivar `jobs` dali perderia 159 dos 227 cargos e o CBO inteiro (`cbo`, `cbo_code`, `description` só existem em `/companies/jobs`). Idem `departments` (13 de 20 em uso) e `cost_centers` (16 de 21). As 3 chamadas custam ~0,3s — mantenha-as.

**Um cargo duplicado.** `jobs.name` tem 226 valores distintos em 227 registros: "Analista de Suporte" existe duas vezes, com CBOs diferentes (411010 e 212420). Não use o nome do cargo como chave.

**CBO é um lookup 1:1.** Os 227 cargos referenciam 54 códigos CBO distintos, e a relação `cbo_code` → nome é estrita (verificada nos 227). Por isso vira tabela própria no `schema.sql`.

## 6. Modelo de dados

O [`schema.sql`](./schema.sql) traduz esta medição em DDL SQLite. Validado carregando a extração real completa: as 5 tabelas populadas, todas as constraints satisfeitas, `foreign_key_check` e `integrity_check` limpos.

**Carga completa: 4 requisições, ~1,8s.**

| Tabela | Linhas | Origem |
|---|---|---|
| `employees` | 119 | `GET /api/v3/employees` |
| `jobs` | 227 | `GET /api/v3/companies/jobs` |
| `cbo_occupations` | 54 | derivada de `jobs.cbo` (lookup 1:1) |
| `cost_centers` | 21 | `GET /api/v3/companies/cost-centers` |
| `departments` | 20 | `GET /api/v3/companies/departments` |

`GET /api/v3/employees/{id}` **não é usado** — ver a observação sobre redundância na seção 5. Não o reintroduza achando que falta dado.

Integridade referencial medida nos dados reais — **100% dos FKs resolvem**: `department_id` 119/119, `job_id` 119/119, `cost_center_id` 119/119, `supervisor_id` 117/117 preenchidos (2 nulos são o topo da hierarquia).

Dois pontos que o DDL precisa tratar e não são óbvios:

- **A auto-referência de gestor exige `DEFERRABLE INITIALLY DEFERRED`.** Em 73 dos 119 colaboradores o gestor aparece *depois* deles na ordem da API; sem o adiamento, a carga em transação única falha com `FOREIGN KEY constraint failed` (verificado).
- **Tudo é `TEXT`, nenhuma coluna numérica.** `address_number`, `address_zip_code` e `cbo_code` têm zeros à esquerda (`02`, `01141070`); como `INTEGER` viram dado corrompido.

### Estratégia de atualização

A 1,8s por rodada, **re-extraia tudo** — sai mais barato que qualquer lógica de delta, e o `INSERT OR REPLACE` por `id` mantém a carga idempotente. Ressalva: a API não expõe `updated_at` em nenhum endpoint, então não há como saber *o que* mudou sem comparar contra o banco. No volume atual isso não é problema.

---

Gerado por `test_colaboradores.py`. Dados brutos das três execuções em `/tmp/claude-1000/-home-condoconta-convenia/647edd12-e740-4892-9272-8621be67805c/scratchpad/` (`resultado.json`, `resultado_v2.json`, `resultado_v3.json`, `permissions_raw*.json`); o perfil de tipos e cardinalidade que embasou o DDL está em `perfil.json`. Valores de CPF, e-mail, telefone e data de nascimento aparecem mascarados.