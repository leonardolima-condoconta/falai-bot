# Fluxos

Como o sistema roda de ponta a ponta: quem dispara cada fluxo, em que ordem as
escritas acontecem e o que precisa estar pronto antes.

Os outros documentos descrevem **peças**; este descreve a **operação**:

| Documento | Responde |
|---|---|
| [`RELATORIO_API.md`](./RELATORIO_API.md) | o que a API da Convenia entrega de fato |
| [`README_HERMES.md`](./README_HERMES.md) | como usar a biblioteca de extração |
| [`sql/*.sql`](./sql/) | o modelo de dados, com as decisões nos comentários |
| [`forms/README.md`](./forms/README.md) | campo a campo de cada modal do Slack |
| **este arquivo** | a sequência: o que dispara o quê, em que ordem |

```
        Convenia (API)
              │  4 GET · ~1,8s
              ▼
      ┌───────────────────┐
      │ employees, jobs,  │◄──── fluxo 0: sincronização (job)
      │ departments,      │
      │ cost_centers, cbo │
      └─────────┬─────────┘
                │ é lida por todos os fluxos abaixo; nenhum deles escreve nela
    ┌───────────┴───────────────────────────────┐
    │                                           │
 Slack: gestor                            Slack: colaborador
    │                                           │
    ├─ 1x1        → registro_1x1                └─ pulse → pulse_resposta (anônima)
    ├─ feedback   → feedback                              + pulse_participacao (nominal)
    ├─ PDI        → pdi
    └─ avaliação  → avaliacao  (exige ciclo aberto)
```

## Invariantes

Valem para todos os fluxos. Quebrar qualquer um deles quebra o desenho:

1. **Pessoa nunca entra pelo formulário.** A única origem de gente é a extração
   da Convenia. Todo `colaborador_id` é um UUID de 36 caracteres que já existe em
   `employees`.
2. **Gestor só registra sobre liderado direto e ativo.** O select é montado com
   `supervisor_id = <quem invocou> AND is_active = 1` — não há como registrar
   sobre quem não é da equipe.
3. **Quem registra nunca é campo do formulário.** Sai do `private_metadata`
   (`lider_id`, `autor_id`), resolvido pelo e-mail do Slack.
4. **Enum no banco = opção no formulário.** Alterar `formato`, `tipo_feedback`,
   `tipo_acao_pdi`, `status_acao` ou `recomendacao` atualiza os modais sem tocar
   em código.
5. **A carga nunca apaga linha.** Desligado é marcado (`is_active = 0`), não
   removido — é isso que sustenta o `ON DELETE RESTRICT` do histórico.
6. **Resposta de pulse nunca toca `employees`.** Não existe caminho de join entre
   `pulse_resposta` e quem respondeu.

---

## Fluxo 0 — Sincronização Convenia → base

**Dispara:** job agendado (cadência ainda não definida; a 1,8s por rodada, diária
é folgado). **Escreve:** `departments`, `cost_centers`, `cbo_occupations`,
`jobs`, `employees`.

Ordem obrigatória — os FKs dependem dela:

| # | Chamada | Grava | Volume |
|---|---|---|---|
| 1 | `GET /api/v3/companies/departments` | `departments` | 20 |
| 2 | `GET /api/v3/companies/cost-centers` | `cost_centers` | 21 |
| 3 | `GET /api/v3/companies/jobs` | `cbo_occupations`, depois `jobs` | 54 / 227 |
| 4 | `GET /api/v3/employees` | `employees` | 119 |

`cbo_occupations` não tem endpoint: é derivada de `jobs.cbo` (`cbo_code` → nome é
1:1 estrito, verificado nos 227). Extraia antes de inserir os cargos.

**Três regras que a ingestão precisa aplicar:**

- **`nullif(valor, '')` em toda coluna de texto.** A API mistura `''` e `null`
  para o mesmo "sem valor". Os `CHECK` rejeitam `''` de propósito, para o dado
  sujo aparecer na carga em vez de virar linha silenciosamente inútil.
- **Os `*_id` declarados vêm `null`; o vínculo está nos objetos aninhados**
  (`department`, `cost_center`, `job`, `supervisor`). Leia de lá. Atenção ao
  cargo: o objeto é `job`, e a coluna é `job_id` — não `job_description_id`.
- **`employees` num único `INSERT` transacional.** Em 73 dos 119 o gestor aparece
  depois do liderado na ordem da API; o `DEFERRABLE INITIALLY DEFERRED` do
  `supervisor_id` é o que permite não ordenar por hierarquia.

**Desligamento é inferido, não lido.** `status` está fora do escopo do token
(sempre `null`) e `/employees/dismissed` é 403. `/employees` devolve só ativos,
então quem sai da listagem foi desligado:

```sql
BEGIN;
UPDATE employees SET is_active = 0 WHERE id NOT IN (<ids da extração>);
-- em seguida, upsert dos extraídos com is_active = 1
COMMIT;
```

Reaparecer volta `is_active` para 1. **Nunca `DELETE`** — o `ON DELETE RESTRICT`
de `registro_1x1`, `feedback`, `pdi`, `avaliacao` e `pulse_participacao` existe
para barrar exatamente isso, e o histórico de quem saiu continua íntegro.

**Re-extraia tudo, sempre.** A API não expõe `updated_at` em nenhum endpoint, e
a 1,8s por rodada qualquer lógica de delta custa mais do que economiza.

> ⚠️ **Este fluxo é o único ainda sem código no repositório.** `ConveniaStorage`
> grava num schema que ele mesmo infere dos dados — **não** nas tabelas de
> `sql/base_schema.sql`. Todas as cargas validadas até aqui foram feitas por
> scripts de teste descartáveis. O carregador que aplica as regras acima é o
> primeiro item para produção.

---

## Fluxo 1 — 1x1

**Dispara:** gestor, no Slack. **Escreve:** `registro_1x1` (1 linha).
**Pré-requisito:** fluxo 0 rodado ao menos uma vez.

1. `build_1x1_modal(conn, slack_user_email)` resolve quem invocou por
   `lower(email)` contra `employees` e monta o select com a equipe direta.
2. `views_open` com a view devolvida.
3. No `view_submission`: `parse_1x1_submission(payload)` devolve o dicionário com
   as chaves de `registro_1x1`, já com `lider_id` preenchido.
4. `INSERT INTO registro_1x1(...)` — INSERT nomeado, sem de-para (os `block_id`
   são os nomes das colunas).

`CHECK (lider_id <> colaborador_id)` é satisfeito de graça: o select só oferece
liderados.

**O campo que não fecha o ciclo:** `progresso_pdi_pct` é registrado no 1x1 mas
não atualiza nada em `pdi`. Hoje é um número solto na linha do 1x1 — se a
intenção era mover o PDI, falta a escrita (ver fluxo 3).

---

## Fluxo 2 — Feedback (SCI)

**Dispara:** gestor, via **`/colaborador feedback`**. **Escreve:** `feedback`
(1 linha).

> ⚠️ **Não registre o comando como `/feedback`.** É palavra reservada do Slack —
> a plataforma trata o comando ela mesma e nunca o entrega ao app. Por isso este
> é o único fluxo sem comando próprio: entra como **subcomando de
> `/colaborador`**, e o handler roteia pelo campo `text` do payload, não pelo
> `command`.
>
> Duas consequências para o handler:
>
> - `/colaborador` sem argumento, ou com subcomando desconhecido, precisa de
>   resposta própria (efêmera, listando os subcomandos válidos) — senão o usuário
>   recebe silêncio e conclui que o app está quebrado.
> - O `text` chega como veio: normalize (`strip().lower()`) antes de comparar.
>
> Os outros três fluxos de gestor não caem nessa restrição e podem ter comando
> direto. Só confira o nome no momento do registro: o Slack tem regras de
> formação para nome de comando, e `1x1` começando com dígito é justamente o tipo
> de nome que vale testar antes de contar com ele.

Fora a invocação, é a mesma mecânica do fluxo 1, com `build_feedback_modal` /
`parse_feedback_submission`; quem invocou vira `autor_id`.

Situação · Comportamento · Impacto são três colunas separadas, e os três são
`optional` no modal — o formulário incentiva o modelo com um bloco de contexto,
mas não o obriga. Feedback com só o campo "acordado" preenchido é aceito pelo
banco.

---

## Fluxo 3 — PDI (70-20-10)

**Dispara:** gestor, no Slack. **Escreve:** `pdi` (1 linha, uma ação).

`build_pdi_modal` / `parse_pdi_submission`. `pdi` não guarda quem registrou — o
`_meta` é descartado no parse.

Uma ação por submit. Um PDI com três ações são três aberturas do formulário.

> ⚠️ **Só existe criação.** `status_id`, `evidencia_conclusao`,
> `ultimo_checkin_gestor` e `ultimo_checkin_bp` só podem ser gravados no momento
> em que a ação nasce. Nada no repositório atualiza uma ação depois disso, e é
> justamente aí que vive o acompanhamento: `v_colaborador_desempenho` conta
> `acoes_pdi_abertas` por `status_id IN (1,2,4)`, então sem fluxo de atualização
> toda ação criada como "Não iniciado" permanece aberta para sempre.
> Falta um modal de check-in — o mais barato é um select da ação existente + novo
> status + data, fazendo `UPDATE` em vez de `INSERT`.

---

## Fluxo 4 — Avaliação de ciclo

**Dispara:** gestor, no Slack, dentro da janela do ciclo. **Escreve:**
`avaliacao` (1 linha por colaborador por ciclo).
**Pré-requisito:** o People abriu o ciclo.

1. **People abre o ciclo** — sem isso o modal devolve aviso, não formulário:
   ```sql
   INSERT INTO ciclo (ano, semestre, nome, aberto_em)
   VALUES (2026, 2, '2026.2', date('now'));
   ```
2. Gestor invoca; `build_avaliacao_modal` oferece os 24 ciclos mais recentes, com
   o último pré-selecionado e os fechados marcados `(fechado)`.
3. Três notas de 1 a 5 (decimais). **`nota_final`, `desempenho` e `potencial` não
   são campos** — são colunas geradas: resultados 50% · competências 30% ·
   potencial 20%, com corte em 4,0 (Alto) e 2,5 (Médio).
4. `INSERT INTO avaliacao(...)`.
5. **Trate a duplicata no handler.** `UNIQUE (ciclo_id, colaborador_id)`, e o
   formulário não consegue filtrar quem já foi avaliado porque o ciclo é escolhido
   dentro do próprio modal:
   ```python
   except sqlite3.IntegrityError:
       return {"response_action": "errors",
               "errors": {"colaborador_id": "Essa pessoa já foi avaliada neste ciclo."}}
   ```
6. **People fecha o ciclo:** `UPDATE ciclo SET fechado_em = date('now') WHERE id = ?`.
   Fechar é rótulo, não trava — o banco continua aceitando avaliação em ciclo
   fechado. Se a janela precisar ser dura, é `CHECK`/trigger novo.

Leitura: `v_avaliacao` entrega o nine box com cargo, departamento, gestor e tempo
de casa resolvidos.

---

## Fluxo 5 — Pulse mensal

**Dispara:** People (abertura) e todo colaborador ativo (resposta).
**Escreve:** `pulse_pesquisa`, `pulse_participacao`, `pulse_resposta`.

Uma rodada por mês de referência (`UNIQUE (ano, mes)`).

### 1. Abrir a rodada

```sql
INSERT INTO pulse_pesquisa (ano, mes, inicio, fim)
VALUES (2026, 7, '2026-07-25', '2026-07-31');
```

`ano`/`mes` são o **mês de referência**, não o do envio: quem responde em 03/08
sobre julho gera `(2026, 7)` com carimbo em agosto.

### 2. Convidar

```sql
INSERT INTO pulse_participacao (pesquisa_id, employee_id)
SELECT :pesquisa_id, id FROM employees WHERE is_active = 1;
```

Isso define o denominador da adesão. Convidar só depois do fluxo 0 do mês, ou
quem entrou recentemente fica fora da conta.

### 3. Responder

`pulse_modal.json` é estático — injete a rodada antes de abrir:

```python
view = json.load(open("forms/pulse_modal.json"))
view["private_metadata"] = json.dumps({"pesquisa_id": pesquisa_id})
client.views_open(trigger_id=trigger_id, view=view)
```

### 4. Gravar — duas escritas que não se conhecem

```python
# a resposta: sem user_id, sem e-mail, sem área, sem liderança
conn.execute("INSERT INTO pulse_resposta(pesquisa_id, carimbo, ...) VALUES (...)")
```

O `value` de cada select é exatamente a chave de `escala_resposta` — é isso que
garante que 100% das respostas entrem nas médias. O eNPS chega como string
`"0"`..`"10"`; converta para `int`.

**A participação é a segunda escrita, e não deve sair do mesmo submit:**

```sql
UPDATE pulse_participacao SET respondeu = 1
 WHERE pesquisa_id = ? AND employee_id = (SELECT id FROM employees WHERE lower(email) = lower(?));
```

> ⚠️ **Vazamento por correlação de horário.** O anonimato é estrutural — não há
> coluna ligando as duas tabelas — mas `pulse_resposta.carregado_em` e
> `pulse_participacao.registrado_em` gravados no mesmo instante permitem parear
> as duas por horário com precisão quase total.
>
> **Mitigação recomendada:** marcar a participação **em lote**, num job de hora
> em hora que atualiza `respondeu` para quem enviou no intervalo. Resolve por
> completo e não exige mexer no schema. Alternativas (gravar só a data;
> restringir acesso às tabelas e expor só as views) estão em
> [`forms/README.md`](./forms/README.md). **Nenhuma está implementada.**

O trigger `trg_pulse_resposta_janela` barra carimbo anterior à abertura — pega o
erro provável de carregar na rodada errada. Depois do fechamento é permitido de
propósito: respondente atrasado conta.

### 5. Fechar e reportar

| View | Entrega |
|---|---|
| `v_pulse_mensal` | série temporal: médias das 5 escalas + eNPS em pontos (-100..100) |
| `v_pulse_adesao` | convidados × responderam × respostas recebidas, por rodada |
| `v_pulse_por_area` | mesmo recorte, por área |

**Disciplina de publicação, que o schema não consegue impor:** suprima células
com menos de 5 respostas em qualquer recorte por área ou liderança; não publique
`motivo_nota` junto de recorte de área; trate `v_pulse_adesao` como dado de RH,
não de gestor de área. Numa área com poucos respondentes, cruzar adesão com
resposta reidentifica.

Depois de cada carga, rode a consulta de cobertura de escalas no rodapé de
`sql/pulse_schema.sql`: resposta fora do mapa não quebra nada, só fica fora das
médias — e é assim que se descobre.

> ⚠️ **`v_pulse_por_area` não funciona com o formulário atual.** As colunas
> `area` e `lideranca_direta` continuam em `pulse_resposta` (herança do Google
> Forms), mas o modal do Slack não as coleta — por decisão, para não reidentificar.
> Consequência: `area`, `area_departamento_id` e `lideranca_id` chegam sempre
> `null`, e `v_pulse_por_area` agrupa tudo numa única linha vazia.
>
> São duas saídas, e a escolha é de política, não técnica: **(a)** aceitar que o
> pulse só tem visão global e dropar a view e as duas colunas; ou **(b)** gravar o
> `department_id` de quem responde no submit — recupera o recorte, mas em
> departamento pequeno reidentifica quase igual a gravar o nome. Enquanto não se
> decidir, use apenas `v_pulse_mensal` e `v_pulse_adesao`.

---

## O que falta para rodar em produção

Os fluxos 1 a 5 estão modelados e testados peça por peça contra dados reais. O
que não existe no repositório:

| Pendência | Fluxo | Por que importa |
|---|---|---|
| **Carregador API → `base_schema.sql`** | 0 | `ConveniaStorage` grava em schema inferido, não nas tabelas do DDL. Sem isso, nenhum outro fluxo tem base. |
| **App do Slack** | 1–5 | Os modais e parsers são biblioteca. Falta registrar os comandos (com o roteamento por subcomando do fluxo 2), tratar o `view_submission` e configurar o token. |
| **Job de participação em lote** | 5 | Enquanto o `UPDATE` sair do submit, o anonimato do pulse é aparência. |
| **Fluxo de atualização de PDI** | 3 | Sem ele, ação de PDI nunca sai de "aberta". |
| **Decisão sobre recorte por área no pulse** | 5 | `v_pulse_por_area` está morta até isso ser resolvido. |
| **Agendamento** | 0, 5 | Cadência da sincronização e da abertura mensal da rodada. |

Ordem sugerida: carregador → app do Slack (fluxos 1, 2, 4 saem de graça juntos) →
job de participação antes de abrir o primeiro pulse real → atualização de PDI.
