-- =============================================================================
-- Pulse mensal — pesquisa de clima, relação com liderança, uso de IA e eNPS
--
-- Origem: formulário Google Forms, uma rodada por mês.
--
-- ⚠️ AS RESPOSTAS SÃO ANÔNIMAS. `pulse_resposta` não tem — e não pode ganhar —
--    qualquer referência a `employees`. Quem respondeu é controlado à parte, em
--    `pulse_participacao`, que registra apenas SE a pessoa respondeu, nunca O
--    QUE respondeu. Não existe caminho de join entre as duas tabelas, e isso é
--    proposital. Leia a seção "Limite do anonimato" antes de montar relatório
--    com recorte fino.
--
-- Depende de base_schema.sql (employees, departments, v_employees):
--       sqlite3 hermes.db < base_schema.sql
--       sqlite3 hermes.db < pulse_schema.sql
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- Controle das rodadas
--
-- Uma linha por mês de referência. É a âncora de tudo: as respostas apontam
-- para cá em vez de repetir ano/mês, e a participação é contada por rodada.
-- -----------------------------------------------------------------------------
CREATE TABLE pulse_pesquisa (
    id           INTEGER PRIMARY KEY,
    ano          INTEGER NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    mes          INTEGER NOT NULL CHECK (mes BETWEEN 1 AND 12),
    -- mês de referência normalizado, ex.: "2026-07"
    competencia  TEXT GENERATED ALWAYS AS (printf('%04d-%02d', ano, mes)) STORED,

    inicio       TEXT NOT NULL,          -- abertura do formulário, ISO
    fim          TEXT NOT NULL,          -- fechamento, ISO
    observacao   TEXT,

    criado_em    TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE (ano, mes),                   -- uma rodada por mês de referência
    CHECK (inicio IS date(inicio)),
    CHECK (fim    IS date(fim)),
    CHECK (fim >= inicio)
);

-- -----------------------------------------------------------------------------
-- Mapa de respostas de escala -> número
--
-- As quatro perguntas de sentimento/IA são categóricas no formulário. Guardar o
-- texto preserva o dado como veio; este mapa é o que permite média e série
-- temporal, sem chutar formato na modelagem.
--
-- ⚠️ SEEDS ABAIXO SÃO PONTO DE PARTIDA. Rode a consulta de cobertura no fim
--    deste arquivo depois da primeira carga e complete com as opções reais do
--    formulário. Resposta não mapeada não quebra a carga — só fica fora das
--    médias, e a consulta de cobertura denuncia.
-- -----------------------------------------------------------------------------
CREATE TABLE escala_resposta (
    resposta TEXT PRIMARY KEY,
    valor    INTEGER NOT NULL CHECK (valor BETWEEN 1 AND 5)
);

INSERT INTO escala_resposta (resposta, valor) VALUES
    -- escala numérica pura, caso o formulário use 1..5
    ('1', 1), ('2', 2), ('3', 3), ('4', 4), ('5', 5),
    -- escalas textuais comuns em pulse
    ('Muito ruim', 1), ('Ruim', 2), ('Neutro', 3), ('Bom', 4), ('Muito bom', 5),
    ('Péssimo', 1), ('Regular', 3), ('Ótimo', 5), ('Excelente', 5),
    ('Discordo totalmente', 1), ('Discordo', 2),
    ('Nem concordo nem discordo', 3),
    ('Concordo', 4), ('Concordo totalmente', 5),
    ('Nada', 1), ('Pouco', 2), ('Moderadamente', 3), ('Bastante', 4), ('Muito', 5),
    ('Não', 1), ('Não usei IA', 1), ('Sim', 5);

-- -----------------------------------------------------------------------------
-- Respostas — anônimas
--
-- Sem employee_id, por definição. `area` e `lideranca_direta` são texto livre do
-- formulário; a ligação com a Convenia é feita por nome, sem constraint, na view
-- v_pulse — e é intencionalmente frouxa.
-- -----------------------------------------------------------------------------
CREATE TABLE pulse_resposta (
    id                  INTEGER PRIMARY KEY,
    pesquisa_id         INTEGER NOT NULL REFERENCES pulse_pesquisa(id)
                            ON UPDATE CASCADE ON DELETE RESTRICT,

    -- "Carimbo de data/hora". O Forms exporta em DD/MM/AAAA HH:MM:SS —
    -- converta para ISO na ingestão.
    carimbo             TEXT NOT NULL,

    -- "Qual sua area?"
    area                TEXT,
    -- "Qual sua Liderança Direta?"
    lideranca_direta    TEXT,

    -- "Como você se sentiu esse mês?"
    sentimento_pessoal  TEXT,
    -- "Como está a relação com a sua liderança esse mês?"
    relacao_lideranca   TEXT,
    -- "Qual seu sentimento desse mês quanto ao time?"
    sentimento_time     TEXT,
    -- "O uso de IA ajudou você a ganhar tempo ou otimizar tarefas no último mês?"
    ia_ganho_tempo      TEXT,
    -- "O uso de IA melhorou a qualidade ou o resultado das suas entregas?"
    ia_qualidade        TEXT,

    -- "De 0 a 10, o quanto você recomendaria CondoConta como um bom lugar para
    --  trabalhar?" — escala eNPS, 0..10 (note: começa em 0, não em 1)
    enps                INTEGER CHECK (enps BETWEEN 0 AND 10),

    -- "👉 Conta pra gente: o que motivou sua nota e o que faria sua experiência
    --  no CondoConta ser ainda melhor?"
    -- Campo único de texto livre: o "Comentários, sempre bem vindo:" do
    -- formulário era duplicata deste e foi descartado na modelagem.
    motivo_nota         TEXT,

    -- Classificação eNPS padrão: 0-6 detrator, 7-8 neutro, 9-10 promotor.
    enps_classe TEXT GENERATED ALWAYS AS
        (CASE WHEN enps IS NULL   THEN NULL
              WHEN enps >= 9      THEN 'Promotor'
              WHEN enps >= 7      THEN 'Neutro'
              ELSE 'Detrator' END) STORED,

    carregado_em        TEXT NOT NULL DEFAULT (datetime('now')),

    CHECK (carimbo IS datetime(carimbo))
);

-- Resposta não pode ser anterior à abertura da rodada — pega CSV carregado na
-- pesquisa errada, que é o erro provável quando se tem uma rodada por mês.
-- Resposta DEPOIS do fechamento é permitida de propósito (respondente atrasado).
CREATE TRIGGER trg_pulse_resposta_janela
BEFORE INSERT ON pulse_resposta
WHEN date(NEW.carimbo) < (SELECT inicio FROM pulse_pesquisa WHERE id = NEW.pesquisa_id)
BEGIN
    SELECT RAISE(ABORT, 'carimbo anterior à abertura da pesquisa');
END;

-- -----------------------------------------------------------------------------
-- Participação — nominal, e SÓ isso
--
-- Responde uma única pergunta: "fulano respondeu esta rodada?". Serve para
-- cobrança de adesão e nada mais.
--
-- ⚠️ NÃO ADICIONE resposta_id AQUI. A ausência de vínculo é a garantia de
--    anonimato; uma coluna apontando para pulse_resposta destruiria isso de uma
--    vez. Se precisar cruzar, cruze agregados, nunca linhas.
-- -----------------------------------------------------------------------------
CREATE TABLE pulse_participacao (
    pesquisa_id   INTEGER NOT NULL REFERENCES pulse_pesquisa(id)
                      ON UPDATE CASCADE ON DELETE RESTRICT,
    employee_id   TEXT NOT NULL REFERENCES employees(id)
                      ON UPDATE CASCADE ON DELETE RESTRICT,
    respondeu     INTEGER NOT NULL DEFAULT 0 CHECK (respondeu IN (0, 1)),
    registrado_em TEXT NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (pesquisa_id, employee_id)
);

-- -----------------------------------------------------------------------------
-- Índices
-- -----------------------------------------------------------------------------
CREATE INDEX idx_pulse_resposta_pesquisa ON pulse_resposta(pesquisa_id);
CREATE INDEX idx_pulse_resposta_area     ON pulse_resposta(area);
CREATE INDEX idx_pulse_resposta_lider    ON pulse_resposta(lideranca_direta);
CREATE INDEX idx_pulse_particip_employee ON pulse_participacao(employee_id);

-- -----------------------------------------------------------------------------
-- v_pulse — respostas com escalas resolvidas e a rodada anexada
--
-- `area_departamento_id` e `lideranca_id` tentam casar o texto do formulário com
-- os dados da Convenia, por nome e sem constraint. Vêm NULL quando não casa
-- (grafia diferente, liderança que saiu, resposta em branco). Use para recorte,
-- nunca como fonte de verdade.
-- -----------------------------------------------------------------------------
CREATE VIEW v_pulse AS
SELECT
    p.id,
    q.id                                  AS pesquisa_id,
    q.competencia,
    q.ano,
    q.mes,
    p.carimbo,
    p.area,
    d.id                                  AS area_departamento_id,
    p.lideranca_direta,
    l.id                                  AS lideranca_id,
    p.sentimento_pessoal,  e1.valor       AS sentimento_pessoal_n,
    p.relacao_lideranca,   e2.valor       AS relacao_lideranca_n,
    p.sentimento_time,     e3.valor       AS sentimento_time_n,
    p.ia_ganho_tempo,      e4.valor       AS ia_ganho_tempo_n,
    p.ia_qualidade,        e5.valor       AS ia_qualidade_n,
    p.enps,
    p.enps_classe,
    p.motivo_nota
FROM pulse_resposta p
JOIN pulse_pesquisa q ON q.id = p.pesquisa_id
LEFT JOIN escala_resposta e1 ON e1.resposta = p.sentimento_pessoal
LEFT JOIN escala_resposta e2 ON e2.resposta = p.relacao_lideranca
LEFT JOIN escala_resposta e3 ON e3.resposta = p.sentimento_time
LEFT JOIN escala_resposta e4 ON e4.resposta = p.ia_ganho_tempo
LEFT JOIN escala_resposta e5 ON e5.resposta = p.ia_qualidade
LEFT JOIN departments d ON d.name      = p.area
LEFT JOIN v_employees l ON l.full_name = p.lideranca_direta;

-- -----------------------------------------------------------------------------
-- v_pulse_adesao — quem foi convidado x quem respondeu, por rodada
-- -----------------------------------------------------------------------------
CREATE VIEW v_pulse_adesao AS
SELECT
    q.id                                     AS pesquisa_id,
    q.competencia,
    q.inicio,
    q.fim,
    count(pp.employee_id)                    AS convidados,
    sum(pp.respondeu)                        AS responderam,
    ROUND(100.0 * sum(pp.respondeu)
          / nullif(count(pp.employee_id), 0), 1) AS adesao_pct,
    (SELECT count(*) FROM pulse_resposta r WHERE r.pesquisa_id = q.id)
                                             AS respostas_recebidas
FROM pulse_pesquisa q
LEFT JOIN pulse_participacao pp ON pp.pesquisa_id = q.id
GROUP BY q.id;

-- -----------------------------------------------------------------------------
-- v_pulse_mensal — a série temporal que interessa
-- -----------------------------------------------------------------------------
CREATE VIEW v_pulse_mensal AS
SELECT
    competencia,
    count(*)                                            AS respostas,
    ROUND(avg(sentimento_pessoal_n), 2)                 AS sentimento_pessoal,
    ROUND(avg(relacao_lideranca_n),  2)                 AS relacao_lideranca,
    ROUND(avg(sentimento_time_n),    2)                 AS sentimento_time,
    ROUND(avg(ia_ganho_tempo_n),     2)                 AS ia_ganho_tempo,
    ROUND(avg(ia_qualidade_n),       2)                 AS ia_qualidade,
    sum(enps_classe = 'Promotor')                       AS promotores,
    sum(enps_classe = 'Neutro')                         AS neutros,
    sum(enps_classe = 'Detrator')                       AS detratores,
    -- eNPS = %promotores - %detratores, em pontos (-100..100)
    ROUND(100.0 * (sum(enps_classe = 'Promotor') - sum(enps_classe = 'Detrator'))
          / nullif(count(enps), 0), 1)                  AS enps
FROM v_pulse
GROUP BY competencia;

-- -----------------------------------------------------------------------------
-- v_pulse_por_area — mesmo recorte, por área
--
-- ⚠️ `respostas` está exposta de propósito: filtre células com poucos
--    respondentes antes de publicar (ver "Limite do anonimato").
-- -----------------------------------------------------------------------------
CREATE VIEW v_pulse_por_area AS
SELECT
    area,
    competencia,
    count(*)                            AS respostas,
    ROUND(avg(sentimento_pessoal_n), 2) AS sentimento_pessoal,
    ROUND(avg(relacao_lideranca_n),  2) AS relacao_lideranca,
    ROUND(avg(sentimento_time_n),    2) AS sentimento_time,
    ROUND(100.0 * (sum(enps_classe = 'Promotor') - sum(enps_classe = 'Detrator'))
          / nullif(count(enps), 0), 1)  AS enps
FROM v_pulse
GROUP BY area, competencia;

-- =============================================================================
-- LIMITE DO ANONIMATO
--
-- O anonimato aqui é estrutural mas não absoluto. `pulse_participacao` diz QUEM
-- respondeu; `pulse_resposta` diz O QUE foi respondido e de qual área. Numa área
-- com poucos respondentes, cruzar os dois reidentifica: se só uma pessoa de
-- "Partner" consta como respondeu = 1, a resposta de "Partner" é dela.
--
-- O schema não tem como impedir isso — é disciplina de relatório:
--   • suprima células com menos de 5 respostas em qualquer recorte por área
--     ou liderança;
--   • não publique motivo_nota junto de recorte de área;
--   • trate v_pulse_adesao como dado de RH, não de gestor de área.
--
-- CONSULTAS DE MANUTENÇÃO
--
-- Opções do formulário fora do mapa de escalas (ficam fora das médias):
--   SELECT resposta, count(*) AS ocorrencias FROM (
--       SELECT sentimento_pessoal AS resposta FROM pulse_resposta
--       UNION ALL SELECT relacao_lideranca FROM pulse_resposta
--       UNION ALL SELECT sentimento_time   FROM pulse_resposta
--       UNION ALL SELECT ia_ganho_tempo    FROM pulse_resposta
--       UNION ALL SELECT ia_qualidade      FROM pulse_resposta)
--   WHERE resposta IS NOT NULL
--     AND resposta NOT IN (SELECT resposta FROM escala_resposta)
--   GROUP BY resposta ORDER BY ocorrencias DESC;
--
-- Áreas e lideranças que não casaram com a Convenia:
--   SELECT DISTINCT area FROM v_pulse
--    WHERE area IS NOT NULL AND area_departamento_id IS NULL;
--   SELECT DISTINCT lideranca_direta FROM v_pulse
--    WHERE lideranca_direta IS NOT NULL AND lideranca_id IS NULL;
--
-- Divergência entre adesão declarada e respostas recebidas (indica participação
-- registrada errado, ou resposta carregada na rodada errada):
--   SELECT competencia, responderam, respostas_recebidas
--   FROM v_pulse_adesao WHERE responderam <> respostas_recebidas;
--
-- Abrir a rodada do mês para todos os colaboradores ativos:
--   INSERT INTO pulse_participacao (pesquisa_id, employee_id)
--   SELECT :pesquisa_id, id FROM employees WHERE is_active = 1;
-- =============================================================================
