-- =============================================================================
-- Gestão de desempenho — 1x1, feedback, PDI e avaliação
--
-- ⚠️ DEPENDE DE schema.sql. Aplique nesta ordem, no MESMO banco:
--       sqlite3 hermes.db < schema.sql
--       sqlite3 hermes.db < pdi.sql
--
-- Os colaboradores NÃO são cadastrados aqui: vêm da extração da Convenia, na
-- tabela `employees`. Por isso toda referência a pessoa é TEXT (UUID de 36
-- caracteres vindo da API), e não INTEGER.
--
-- Este arquivo não altera nada de schema.sql — só referencia.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ===================== TABELAS DE ENUM (aba Listas) =====================

CREATE TABLE formato       (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE);
CREATE TABLE tipo_feedback (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE);
CREATE TABLE tipo_acao_pdi (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE);
CREATE TABLE status_acao   (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE);
CREATE TABLE recomendacao  (id INTEGER PRIMARY KEY, nome TEXT NOT NULL UNIQUE);

INSERT INTO formato (id, nome) VALUES (1,'Presencial'), (2,'Remoto');

INSERT INTO tipo_feedback (id, nome) VALUES (1,'Positivo'), (2,'Construtivo'), (3,'Ambos');

INSERT INTO tipo_acao_pdi (id, nome) VALUES   -- modelo 70-20-10
    (1,'70% Prática'), (2,'20% Social'), (3,'10% Formal');

INSERT INTO status_acao (id, nome) VALUES
    (1,'Não iniciado'), (2,'Em andamento'), (3,'Concluído'), (4,'Atrasado');

INSERT INTO recomendacao (id, nome) VALUES
    (1,'Promoção'), (2,'Mérito'), (3,'Bônus'), (4,'Manter'),
    (5,'PDI intensivo'), (6,'PIP'), (7,'Desligamento');

-- Ciclo avaliativo. Era referenciado por `avaliacao` sem nunca ser criado.
-- Semestre + ano reproduz a granularidade que o UNIQUE original pretendia.
CREATE TABLE ciclo (
    id        INTEGER PRIMARY KEY,
    ano       INTEGER NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    semestre  INTEGER NOT NULL CHECK (semestre IN (1, 2)),
    nome      TEXT,                    -- ex.: "2026.1"
    aberto_em TEXT CHECK (aberto_em IS NULL OR aberto_em IS date(aberto_em)),
    fechado_em TEXT CHECK (fechado_em IS NULL OR fechado_em IS date(fechado_em)),

    UNIQUE (ano, semestre)
);

-- ===================== TABELAS TRANSACIONAIS =====================
--
-- Padrão das FKs para pessoas:
--   REFERENCES employees(id) ON UPDATE CASCADE ON DELETE RESTRICT
--
-- RESTRICT é proposital: o histórico de desempenho não pode sumir junto com o
-- colaborador. A carga da Convenia usa INSERT OR REPLACE e nunca apaga linhas,
-- então quem sai da empresa apenas para de ser atualizado e continua
-- referenciável. Se algum dia a carga passar a fazer DELETE, o RESTRICT vai
-- barrar — e é exatamente o que se quer.

CREATE TABLE registro_1x1 (
    id                  INTEGER PRIMARY KEY,
    data                TEXT NOT NULL,
    colaborador_id      TEXT NOT NULL REFERENCES employees(id)
                            ON UPDATE CASCADE ON DELETE RESTRICT,
    lider_id            TEXT REFERENCES employees(id)
                            ON UPDATE CASCADE ON DELETE RESTRICT,
    formato_id          INTEGER REFERENCES formato(id),
    energia             INTEGER CHECK (energia   BETWEEN 1 AND 5),
    motivacao           INTEGER CHECK (motivacao BETWEEN 1 AND 5),
    pauta_liderado      TEXT,
    encaminhamentos     TEXT,
    feedback_tipo_id    INTEGER REFERENCES tipo_feedback(id),
    resumo_feedback_sci TEXT,
    progresso_pdi_pct   INTEGER CHECK (progresso_pdi_pct BETWEEN 0 AND 100),
    acoes_acordadas     TEXT,
    proximo_1x1         TEXT,

    CHECK (data IS date(data)),
    CHECK (proximo_1x1 IS NULL OR proximo_1x1 IS date(proximo_1x1)),
    CHECK (lider_id IS NULL OR lider_id <> colaborador_id)
);

CREATE TABLE feedback (
    id             INTEGER PRIMARY KEY,
    data           TEXT NOT NULL,
    colaborador_id TEXT NOT NULL REFERENCES employees(id)
                       ON UPDATE CASCADE ON DELETE RESTRICT,
    autor_id       TEXT REFERENCES employees(id)          -- quem deu o feedback
                       ON UPDATE CASCADE ON DELETE RESTRICT,
    tipo_id        INTEGER REFERENCES tipo_feedback(id),
    situacao       TEXT,   -- modelo SCI
    comportamento  TEXT,
    impacto        TEXT,
    acordado       TEXT,

    CHECK (data IS date(data))
);

CREATE TABLE pdi (
    id                    INTEGER PRIMARY KEY,
    colaborador_id        TEXT NOT NULL REFERENCES employees(id)
                              ON UPDATE CASCADE ON DELETE RESTRICT,
    competencia_foco      TEXT,
    gap_evidencia         TEXT,
    tipo_acao_id          INTEGER REFERENCES tipo_acao_pdi(id),  -- 70-20-10
    descricao_acao        TEXT,
    prazo                 TEXT,
    evidencia_conclusao   TEXT,
    status_id             INTEGER REFERENCES status_acao(id),
    ultimo_checkin_gestor TEXT,
    ultimo_checkin_bp     TEXT,

    CHECK (prazo IS NULL OR prazo IS date(prazo)),
    CHECK (ultimo_checkin_gestor IS NULL OR ultimo_checkin_gestor IS date(ultimo_checkin_gestor)),
    CHECK (ultimo_checkin_bp     IS NULL OR ultimo_checkin_bp     IS date(ultimo_checkin_bp))
);

CREATE TABLE avaliacao (
    id                INTEGER PRIMARY KEY,
    ciclo_id          INTEGER NOT NULL REFERENCES ciclo(id),
    colaborador_id    TEXT NOT NULL REFERENCES employees(id)
                          ON UPDATE CASCADE ON DELETE RESTRICT,
    nota_resultados   REAL CHECK (nota_resultados   BETWEEN 1 AND 5),
    nota_competencias REAL CHECK (nota_competencias BETWEEN 1 AND 5),
    nota_potencial    REAL CHECK (nota_potencial    BETWEEN 1 AND 5),
    -- colunas calculadas espelhando as fórmulas da aba Avaliacoes:
    nota_final REAL GENERATED ALWAYS AS
        (ROUND(nota_resultados*0.5 + nota_competencias*0.3 + nota_potencial*0.2, 2)) STORED,
    desempenho TEXT GENERATED ALWAYS AS
        (CASE WHEN nota_resultados*0.5+nota_competencias*0.3+nota_potencial*0.2 >= 4   THEN 'Alto'
              WHEN nota_resultados*0.5+nota_competencias*0.3+nota_potencial*0.2 >= 2.5 THEN 'Médio'
              ELSE 'Baixo' END) STORED,
    potencial  TEXT GENERATED ALWAYS AS
        (CASE WHEN nota_potencial >= 4   THEN 'Alto'
              WHEN nota_potencial >= 2.5 THEN 'Médio'
              ELSE 'Baixo' END) STORED,
    recomendacao_id INTEGER REFERENCES recomendacao(id),
    comentarios     TEXT,

    -- O UNIQUE original citava (semestre_ano, ano, colaborador_id), colunas que
    -- não existem na tabela. A granularidade pretendida vive em `ciclo`.
    UNIQUE (ciclo_id, colaborador_id)
);

-- ===================== ÍNDICES =====================
-- SQLite não indexa FK automaticamente.

CREATE INDEX idx_1x1_colaborador       ON registro_1x1(colaborador_id);
CREATE INDEX idx_1x1_lider             ON registro_1x1(lider_id);
CREATE INDEX idx_1x1_data              ON registro_1x1(data);
CREATE INDEX idx_feedback_colaborador  ON feedback(colaborador_id);
CREATE INDEX idx_feedback_autor        ON feedback(autor_id);
CREATE INDEX idx_feedback_data         ON feedback(data);
CREATE INDEX idx_pdi_colaborador       ON pdi(colaborador_id);
CREATE INDEX idx_pdi_status            ON pdi(status_id);
CREATE INDEX idx_avaliacao_colaborador ON avaliacao(colaborador_id);
CREATE INDEX idx_avaliacao_ciclo       ON avaliacao(ciclo_id);

-- ===================== VIEWS =====================
-- Cruzam o desempenho com os dados de cadastro vindos da Convenia.

-- Nine box do ciclo, já com cargo, departamento e gestor resolvidos.
CREATE VIEW v_avaliacao AS
SELECT
    a.id,
    ci.ano,
    ci.semestre,
    e.full_name           AS colaborador,
    e.department,
    e.cost_center,
    e.job,
    e.supervisor          AS gestor,
    ROUND(e.tenure_years, 1) AS tempo_casa_anos,
    a.nota_resultados,
    a.nota_competencias,
    a.nota_potencial,
    a.nota_final,
    a.desempenho,
    a.potencial,
    a.desempenho || ' / ' || a.potencial AS nine_box,
    r.nome                AS recomendacao,
    a.comentarios
FROM avaliacao a
JOIN ciclo         ci ON ci.id = a.ciclo_id
JOIN v_employees   e  ON e.id  = a.colaborador_id
LEFT JOIN recomendacao r ON r.id = a.recomendacao_id;

-- Um retrato por colaborador: cadastro + atividade de desempenho.
CREATE VIEW v_colaborador_desempenho AS
SELECT
    e.id,
    e.full_name,
    e.department,
    e.job,
    e.supervisor          AS gestor,
    (SELECT count(*) FROM registro_1x1 x WHERE x.colaborador_id = e.id)      AS qtd_1x1,
    (SELECT max(data)  FROM registro_1x1 x WHERE x.colaborador_id = e.id)    AS ultimo_1x1,
    (SELECT count(*) FROM feedback f WHERE f.colaborador_id = e.id)          AS qtd_feedbacks,
    (SELECT count(*) FROM pdi p WHERE p.colaborador_id = e.id
                                  AND p.status_id IN (1, 2, 4))              AS acoes_pdi_abertas,
    (SELECT a.nota_final FROM avaliacao a
       JOIN ciclo c ON c.id = a.ciclo_id
      WHERE a.colaborador_id = e.id
      ORDER BY c.ano DESC, c.semestre DESC LIMIT 1)                          AS ultima_nota
FROM v_employees e;
