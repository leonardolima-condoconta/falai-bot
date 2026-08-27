# Formulários do Slack

| Arquivo | Formulário | Tabela alvo | Natureza |
|---|---|---|---|
| `pulse_modal.json` | Pulse mensal | `pulse_resposta` | estático |
| `pdi_modal.py` | Nova ação de PDI | `pdi` | dinâmico |
| `um_a_um_modal.py` | Registro de 1x1 | `registro_1x1` | dinâmico |
| `feedback_modal.py` | Feedback (SCI) | `feedback` | dinâmico |
| `avaliacao_modal.py` | Avaliação do ciclo | `avaliacao` | dinâmico |
| `common.py` | peças compartilhadas pelos quatro dinâmicos | — | — |

Os `block_id` de cada input são **iguais aos nomes das colunas** da tabela alvo.
O handler lê `view.state.values[<block_id>].valor` e grava direto, sem de-para.

Para validar um modal no Block Kit Builder, abra a URL correspondente em
`.bkb_<form>_url.txt` — ela já carrega o payload no surface *Modal*. Colar o
JSON no surface *Message* dá erro de `invalid additional property`.

---

## Os quatro formulários dinâmicos

Todos seguem o mesmo padrão, em `common.py`:

1. quem invoca é resolvido por `lower(email)` contra `employees`;
2. o select de colaborador traz **apenas liderados diretos e ativos**
   (`supervisor_id = <quem invocou> AND is_active = 1`);
3. enums (`formato`, `tipo_feedback`, `tipo_acao_pdi`, `status_acao`,
   `recomendacao`) vêm do banco — mudar o enum atualiza o formulário sem tocar
   em código.

```python
from forms.um_a_um_modal import build_1x1_modal, parse_1x1_submission

view = build_1x1_modal(conn, slack_user_email)
client.views_open(trigger_id=trigger_id, view=view)

# no view_submission:
dados = parse_1x1_submission(payload)
conn.execute("""INSERT INTO registro_1x1(colaborador_id, lider_id, data, formato_id,
    energia, motivacao, pauta_liderado, encaminhamentos, feedback_tipo_id,
    resumo_feedback_sci, progresso_pdi_pct, acoes_acordadas, proximo_1x1)
    VALUES(:colaborador_id, :lider_id, :data, :formato_id, :energia, :motivacao,
           :pauta_liderado, :encaminhamentos, :feedback_tipo_id, :resumo_feedback_sci,
           :progresso_pdi_pct, :acoes_acordadas, :proximo_1x1)""", dados)
```

Os outros três são idênticos na forma — só trocam o builder, o parser e o INSERT.

### Quem invocou não é campo do formulário

`registro_1x1.lider_id` e `feedback.autor_id` saem do `private_metadata`, não de
um input. Os parsers já devolvem a chave preenchida. Isso também satisfaz o
`CHECK (lider_id <> colaborador_id)` do schema de graça: o select só oferece
liderados, então nunca dá para registrar 1x1 consigo mesmo.

`pdi` e `avaliacao` não guardam quem registrou — nesses dois o `_meta` é
descartado no parse.

### Normalização

`parse_submission` devolve o dicionário pronto para o INSERT:
`selected_option` → `value`, `datepicker` → data ISO, `number_input` → `int` ou
`float` conforme o campo, e string em branco → `None` (nunca `''`, respeitando o
que o `base_schema.sql` exige).

### Quando não dá para montar o formulário

Os builders devolvem um **modal de aviso** (`callback_id: form_aviso`) em vez de
estourar exceção:

| Situação | Mensagem |
|---|---|
| E-mail do Slack não existe em `employees` | Explica a divergência com o RH |
| Quem invocou não lidera ninguém | Explica que o vínculo vem do cadastro do RH |
| Equipe acima de 100 pessoas | Limite do Block Kit; manda usar a web |
| *(só avaliação)* nenhum ciclo cadastrado | Pede ao People abrir o ciclo em `ciclo` |

### Avaliação: duplicata no mesmo ciclo

`avaliacao` tem `UNIQUE (ciclo_id, colaborador_id)`. O formulário **não** filtra
quem já foi avaliado, porque o ciclo é escolhido dentro do próprio modal. Trate
no handler devolvendo o erro no bloco certo:

```python
try:
    conn.execute("INSERT INTO avaliacao(...) VALUES(...)", dados)
except sqlite3.IntegrityError:
    return {"response_action": "errors",
            "errors": {"colaborador_id": "Essa pessoa já foi avaliada neste ciclo."}}
```

O select de ciclo já vem com o mais recente pré-selecionado, e os fechados
aparecem marcados como `(fechado)`.

### Notas e escalas numéricas

`energia`, `motivacao` (1–5), `progresso_pdi_pct` (0–100) e as três notas da
avaliação (1–5, decimais) usam o elemento `number_input`, com `min_value` e
`max_value` — a validação de faixa acontece no Slack antes do submit, e os
`CHECK` do schema são a segunda barreira.

`nota_final`, `desempenho` e `potencial` **não** são campos: são colunas
geradas, calculadas pelo banco (resultados 50% · competências 30% ·
potencial 20%).

---

## Pulse

Sem campos de área e liderança, como combinado — quem responde é identificado
pelo `user_id` do Slack só para o controle de adesão, e isso **não** entra na
resposta.

Abrir o modal injetando a rodada corrente:

```python
view = json.load(open("forms/pulse_modal.json"))
view["private_metadata"] = json.dumps({"pesquisa_id": pesquisa_id})
client.views_open(trigger_id=trigger_id, view=view)
```

### A regra que sustenta o anonimato

O submit chega com o `user_id` do Slack. O handler faz **duas escritas
independentes**, e nenhuma delas as conecta:

```python
pesquisa_id = json.loads(payload["view"]["private_metadata"])["pesquisa_id"]
v = payload["view"]["state"]["values"]
get = lambda b: (v[b]["valor"].get("selected_option") or {}).get("value")

# 1. a resposta — sem qualquer traço de quem enviou
conn.execute("""INSERT INTO pulse_resposta(pesquisa_id, carimbo, sentimento_pessoal,
    relacao_lideranca, sentimento_time, ia_ganho_tempo, ia_qualidade, enps, motivo_nota)
    VALUES(?, datetime('now'), ?, ?, ?, ?, ?, ?, ?)""",
    (pesquisa_id, get("sentimento_pessoal"), get("relacao_lideranca"),
     get("sentimento_time"), get("ia_ganho_tempo"), get("ia_qualidade"),
     int(get("enps")), (v["motivo_nota"]["valor"].get("value") or "").strip() or None))

# 2. a participação — nominal, mas sem dizer o que foi respondido
conn.execute("""UPDATE pulse_participacao SET respondeu = 1
    WHERE pesquisa_id = ? AND employee_id =
        (SELECT id FROM employees WHERE lower(email) = lower(?))""",
    (pesquisa_id, slack_user_email))
```

**Nunca** passe `user_id`, e-mail, área ou liderança para o primeiro INSERT.

### ⚠️ Vazamento por correlação de horário

O anonimato acima é estrutural, mas os **carimbos de tempo o desfazem** se as
duas escritas forem simultâneas: `pulse_resposta.carregado_em` e
`pulse_participacao.registrado_em` ficam a segundos um do outro, e com as
respostas chegando ao longo de dias o pareamento é quase perfeito para quem tem
acesso ao banco.

Escolha uma mitigação antes de ir para produção:

- **Marcar a participação em lote**, desacoplada do submit — um job de hora em
  hora que atualiza `respondeu` para todos os que enviaram no intervalo. Simples
  e resolve por completo.
- **Gravar só a data** em `registrado_em` e `carregado_em` (`date('now')`), o que
  achata a correlação para o dia.
- Restringir acesso direto às duas tabelas e expor só as views agregadas.

A primeira é a mais robusta e não exige mexer no schema.

### Escalas

Os `value` dos selects são exatamente as chaves de `escala_resposta` no
`sql/pulse_schema.sql`. Isso é o que garante que 100% das respostas entrem nas
médias. **Ao editar uma opção aqui, edite lá também** — o teste de cobertura no
rodapé daquele arquivo detecta a divergência depois do fato, mas o barato é não
criá-la.

O eNPS vai como string `"0"`..`"10"`; converta para `int` antes de gravar.

---

## Limites do Block Kit respeitados

Título ≤ 24 caracteres, ≤ 100 blocos por modal, ≤ 100 opções por select, texto
de opção ≤ 75 caracteres. O maior modal é o de 1x1, com 16 blocos; a maior
equipe hoje tem 10 pessoas e o nome mais longo da base tem 42 caracteres.
