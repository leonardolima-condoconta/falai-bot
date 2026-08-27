-- =============================================================================
-- Base interna do Hermes — dados extraídos da API Convenia
--
-- Modelado a partir do escopo PERMANENTE do token (5 endpoints acessíveis).
-- Todos os tipos, formatos e constraints abaixo foram derivados dos dados reais
-- e validados contra a extração completa. Ver RELATORIO_API.md.
--
-- Volumes medidos: 119 colaboradores · 227 cargos · 54 CBOs · 21 centros de
-- custo · 20 departamentos.
--
-- CARGA COMPLETA = 4 REQUISIÇÕES, ~1,5s:
--    GET /employees · /companies/departments · /companies/jobs · /companies/cost-centers
--
--    O endpoint /employees/{id} NÃO é usado. Verificado nos 119 colaboradores: ele
--    devolve os mesmos campos da listagem (concordância de 100%, zero divergência)
--    e acrescenta apenas `cellphone` e `social_name` — ambos fora do escopo do
--    Hermes. Chamá-lo custaria +119 requisições e 145s (96× mais lento) para
--    trazer zero informação nova.
--
-- ⚠️ NORMALIZE STRING VAZIA PARA NULL NA INGESTÃO.
--    A API mistura '' e null para o mesmo "sem valor". Aplique nullif(valor, '')
--    em toda coluna de texto; os CHECKs abaixo rejeitam '' de propósito, para que
--    o dado sujo apareça na carga em vez de virar linha silenciosamente inútil.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Tabelas de apoio
-- -----------------------------------------------------------------------------

-- 20 registros. `name` é único nos dados reais.
CREATE TABLE departments (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    synced_at  TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (length(id) = 36)
);

-- 21 registros. `name` é único nos dados reais.
CREATE TABLE cost_centers (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    synced_at  TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (length(id) = 36)
);

-- 54 registros. Extraído de jobs.cbo — a API devolve o CBO embutido em cada
-- cargo, mas a relação cbo_code -> nome é estritamente 1:1 (verificado nos 227
-- cargos), então vira lookup próprio. Código CBO é a chave natural.
CREATE TABLE cbo_occupations (
    code       TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    synced_at  TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (code GLOB '[0-9][0-9][0-9][0-9][0-9][0-9]')
);

-- 227 registros. `name` NÃO é único: "Analista de Suporte" existe duas vezes,
-- com CBOs distintos (411010 e 212420). `description` vem preenchida em só 2%.
CREATE TABLE jobs (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT,
    cbo_code     TEXT NOT NULL REFERENCES cbo_occupations(code) ON UPDATE CASCADE,
    synced_at    TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (length(id) = 36)
);

-- -----------------------------------------------------------------------------
-- Colaboradores
--
-- Origem: GET /api/v3/employees — uma única chamada paginada traz os 119.
--
-- Nomes de departamento/cargo/centro de custo/gestor NÃO são replicados aqui:
-- vêm por join (ver a view v_employees no fim). Guardar cópia significaria
-- ficar desatualizado se a entidade de origem for renomeada.
--
-- O endereço é retornado pela API (objeto `address`, 100% preenchido) mas NÃO é
-- persistido: não faz parte do escopo de uso do Hermes. Se um dia precisar, os
-- campos são address.{address, number, complement, district, city, state, zip_code}.
-- -----------------------------------------------------------------------------
CREATE TABLE employees (
    id                  TEXT PRIMARY KEY,

    -- identificação (nenhum documento é acessível: cpf/pis/rg estão fora do escopo)
    name                TEXT NOT NULL,           -- primeiro nome
    last_name           TEXT NOT NULL,           -- sobrenome completo
    email               TEXT UNIQUE,             -- 15% nulo; corporativo
    birth_date          TEXT NOT NULL,           -- ISO YYYY-MM-DD
    hiring_date         TEXT NOT NULL,           -- ISO YYYY-MM-DD

    -- vínculos organizacionais (100% preenchidos e íntegros nos dados reais)
    department_id       TEXT NOT NULL REFERENCES departments(id),
    cost_center_id      TEXT NOT NULL REFERENCES cost_centers(id),
    job_id              TEXT NOT NULL REFERENCES jobs(id),
    -- 117/119 preenchidos; os 2 nulos são o topo da hierarquia.
    -- DEFERRABLE: permite inserir o lote inteiro numa transação sem ordenar por hierarquia.
    supervisor_id       TEXT REFERENCES employees(id) DEFERRABLE INITIALLY DEFERRED,

    -- Situação: 1 = ativo, 0 = desligado. NÃO vem da API — o campo `status` do
    -- endpoint está fora do escopo e chega sempre null, e /employees/dismissed
    -- é 403. É derivado da presença na extração: /employees devolve apenas
    -- ativos, então quem some da listagem foi desligado.
    --
    -- Regra de carga (nunca apagar linha, só marcar):
    --   UPDATE employees SET is_active = 0 WHERE id NOT IN (<ids da extração>);
    --   INSERT OR REPLACE ... com is_active = 1 para os que vieram.
    --
    -- Preservar a linha é o que sustenta o ON DELETE RESTRICT das tabelas de
    -- desempenho: o histórico de um desligado continua íntegro.
    is_active           INTEGER NOT NULL DEFAULT 1,

    synced_at           TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (length(id) = 36),
    CHECK (length(name) > 0 AND length(last_name) > 0),
    CHECK (birth_date IS date(birth_date)),
    CHECK (hiring_date IS date(hiring_date)),
    CHECK (email IS NULL OR email LIKE '%_@_%.__%'),
    CHECK (is_active IN (0, 1)),
    CHECK (supervisor_id IS NULL OR supervisor_id <> id)
);

-- -----------------------------------------------------------------------------
-- Índices — os FKs não ganham índice automático no SQLite
-- -----------------------------------------------------------------------------
CREATE INDEX idx_employees_department   ON employees(department_id);
CREATE INDEX idx_employees_cost_center  ON employees(cost_center_id);
CREATE INDEX idx_employees_job          ON employees(job_id);
CREATE INDEX idx_employees_supervisor   ON employees(supervisor_id);
CREATE INDEX idx_employees_hiring_date  ON employees(hiring_date);
CREATE INDEX idx_jobs_cbo               ON jobs(cbo_code);

-- -----------------------------------------------------------------------------
-- View de leitura: o colaborador com todos os nomes resolvidos.
--
-- NÃO filtra por is_active de propósito — esconder desligado silenciosamente
-- distorceria qualquer histórico. Filtre no consumo: WHERE is_active = 1.
-- -----------------------------------------------------------------------------
CREATE VIEW v_employees AS
SELECT
    e.id,
    e.name || ' ' || e.last_name          AS full_name,
    e.email,
    e.birth_date,
    (strftime('%Y', 'now') - strftime('%Y', e.birth_date))
        - (strftime('%m-%d', 'now') < strftime('%m-%d', e.birth_date))   AS age,
    e.hiring_date,
    (julianday('now') - julianday(e.hiring_date)) / 365.25               AS tenure_years,
    d.name                                AS department,
    c.name                                AS cost_center,
    j.name                                AS job,
    j.cbo_code,
    cbo.name                              AS cbo_occupation,
    s.name || ' ' || s.last_name          AS supervisor,
    e.is_active
FROM employees e
JOIN departments     d   ON d.id   = e.department_id
JOIN cost_centers    c   ON c.id   = e.cost_center_id
JOIN jobs            j   ON j.id   = e.job_id
JOIN cbo_occupations cbo ON cbo.code = j.cbo_code
LEFT JOIN employees  s   ON s.id   = e.supervisor_id;
