---
name: condopower-api
description: Dados de People da CondoConta por POST /rpc — quem é a pessoa que está falando, seu nível de acesso e seus liderados diretos, aniversários e tempo de casa, registro e leitura dos formulários respondidos (clima, autoavaliação, avaliação de liderança, 1x1, PDI, nine box) e administração das rodadas de pesquisa de clima. Use SEMPRE que a conversa envolver uma pessoa da CondoConta — quem ela é, o que pode ver, quem lidera, quando entrou, aniversário, tempo de casa — quando alguém responder qualquer um desses formulários ou pedir para ver os que já foram respondidos, de uma pessoa ou de uma área, quando pedir adesão ou resultado de clima, ou quando você precisar saber se pode mostrar um dado a quem pediu. Vale mesmo que a API não seja citada pelo nome.
version: 2.1.0
---

# condopower-api — dados de People por POST /rpc

## Pra que serve

Este serviço é a **fonte de identidade e de registro** do agente para assuntos de People:

1. **Saber com quem você está falando** — um Slack ID vira nome, e-mail, cargo, departamento,
   nível de acesso e a lista de liderados diretos. É a primeira chamada de todo atendimento,
   porque tudo o que vem depois depende de saber quem pediu e o que essa pessoa alcança.
2. **Guardar o que a pessoa respondeu** — 1x1, PDI, autoavaliação, avaliação de liderança,
   nine box e clima. Você coleta na conversa e grava; o serviço não interpreta as respostas.
3. **Administrar a pesquisa de clima** — abrir a rodada do mês, encerrar, reabrir, acompanhar a
   adesão e ler as respostas. Só o time de People faz isso.
4. **Lembrar de comemorar** — aniversário e tempo de casa dos dias que a execução cobre.

O que ele **não** faz: salário, férias, ausências, desligamento (fora do escopo do token do
Convenia) e login. Também não existe formulário web — as páginas HTML foram removidas em
2026-08-21. Não mande link de `/forms`, ele não responde.

Endereço: `https://condopower-api.aiexpert-condoconta.info`

---

## Como usar

### Uma rota só, sempre POST

```json
{"method": "access.verify", "params": {"identifier": "<@U0ANA>"}}
```

O proxy à frente das aplicações só encaminha POST com cabeçalho e corpo, então não existem
rotas REST por recurso — o nome da função viaja no corpo, em `method`, e os argumentos em
`params`. `Content-Type: application/json`.

Sucesso e falha têm formas fixas, e a falha traz **status HTTP semântico**, não 200:

```json
{"ok": true,  "method": "access.verify", "result": { ... }}
{"ok": false, "method": "access.verify", "error": {"code": "...", "message": "...", "fields": []}}
```

O `message` é escrito para ser lido por uma pessoa — em caso de erro, prefira repassá-lo a
inventar explicação.

### Regras que valem para tudo

**`access.verify` é a primeira chamada de todo atendimento.** É onde o Slack ID vira e-mail e
id do Convenia, que é o que os outros métodos pedem. Nenhum outro método aceita Slack ID.

**Nunca assuma nível de acesso.** Se a verificação falhar, o atendimento para. Não existe nível
padrão; tratar falha como "nível 1" abriria dado de quem não deveria ver.

**Você é quem aplica o recorte por nível.** O serviço devolve o nível e recusa escrita
administrativa de quem não é People, mas não filtra leitura por hierarquia. Um nível 2 que
pedir dado de outra área recebe resposta — cabe a você não mostrar.

**Recusa é resposta correta.** 403 e 409 são regras de negócio funcionando, não obstáculos a
contornar tentando outros parâmetros.

**O catálogo é autoritativo, esta skill não.** `system.describe` devolve o schema de entrada e
saída gerado dos mesmos modelos que validam a chamada. Se divergirem, o catálogo está certo.

### 1. Quem é a pessoa — `access.verify`

| Param | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `identifier` | string | sim | Slack ID (`U123`, `@U123`, `<@U123>`) ou e-mail |

Um identificador só, de propósito: dois permitiriam pedir o Slack ID de uma pessoa junto do
e-mail de outra. O que distingue e-mail não é o `@` — é o `@` **no meio** do valor, com algo de
cada lado.

**Volta** `employee` (`id`, `full_name`, `email`, `slack_user_id`, `job`, `department`),
`level`, `role`, `is_active` e `reports[]` — cada liderado com `id`, `full_name`, `email`,
`slack_user_id` e `job`.

| `level` | `role` | Alcança |
|---|---|---|
| 5 | `superadmin` | tudo |
| 4 | `admin` | tudo |
| 3 | `team_people` | tudo — é quem administra a pesquisa de clima |
| 2 | `condo_leader` | a si e aos liderados diretos |
| 1 | `condopower` | apenas a si |

**Cuidado com nulos.** `email` e `slack_user_id` podem vir nulos: 20 dos 121 colaboradores não
têm Slack ID casado — 18 sem e-mail no Convenia e 2 com endereço que o workspace não conhece.
Essas pessoas existem no cadastro e são encontradas por e-mail.

O `id` de `employee` e de `reports[]` é o UUID do Convenia. **Nunca monte esse id na mão** — ele
é o que os formulários pedem.

### 2. Comemorações — `celebrations.birthdays` e `celebrations.work_anniversaries`

| Param | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `reference_date` | date | não | Dia da execução; ausente = hoje no fuso de São Paulo |

**Volta** `reference_date`, `covered_dates[]` e `celebrants[]`. Cada pessoa traz
`celebrated_on`, o dia em que a data cai — em `work_anniversaries`, também `hiring_date` e
`years`.

**Na segunda-feira, `covered_dates` inclui o sábado e o domingo anteriores**, porque os jobs só
rodam em dia útil e quem comemora no fim de semana passaria em branco. Agrupe a mensagem por
dia ("no sábado...", "ontem...") em vez de tratar tudo como hoje.

Tempo de casa conta a partir de **um ano completo** — quem está completando o primeiro dia não
aparece. `celebrants` vazio é resposta normal, não erro.

### 3. Guardar um formulário respondido — os seis `form.*`

**O que você manda em `params` é gravado como veio**, e o nome do método usado fica registrado
como o tipo do formulário.

| Método | Id obrigatório | Para que serve |
|---|---|---|
| `form.pulse` | nenhum | Resposta de clima — **exige rodada aberta** |
| `form.autoavaliacao` | `colaborador_id` | A pessoa se avalia |
| `form.avaliacao_lider` | `lider_id` | A liderança avalia um liderado |
| `form.1x1` | `lider_id` | Registro de um 1x1 |
| `form.pdi` | `lider_id` | Plano de desenvolvimento individual |
| `form.9box` | `lider_id` | Posicionamento no nine box |

**Não existe lista fechada de campos.** Mande cada resposta com o nome de campo do formulário —
número, texto, data, lista ou objeto aninhado, tudo é aceito e nada é descartado. Nos quatro que
pedem `lider_id`, `colaborador_id` é opcional e vale mandar quando o formulário é sobre alguém.

**`area` é o único campo de resposta que o serviço lê.** Mande-o sempre que souber de que área o
formulário fala: ele fica no `raw` como os outros e vira a coluna pela qual a leitura filtra.
Formulário gravado sem `area` não aparece para quem pedir por área.

**Volta** `id`, `tipo_formulario` e `created_at`. O `id` é o comprovante de que ficou
registrado — repasse-o quando a pessoa perguntar se salvou.

**A coleta é sua.** Não há formulário web para onde mandar quem tem muito a preencher. Peça os
campos em bloco em vez de um por mensagem, confirme o que entendeu e chame o método **uma única
vez**, com tudo pronto. Isto é coleta, não conversa: o processamento vem depois, a partir do que
ficou gravado, e campo que você achou irrelevante e não mandou não volta.

**Exemplo**

```json
{
  "method": "form.1x1",
  "params": {
    "lider_id": "3f1c...",
    "colaborador_id": "9ab2...",
    "data": "2026-08-21",
    "energia": 4,
    "pauta_liderado": "Quer assumir a squad de cobrança",
    "acoes_acordadas": ["Mentoria com a Ana", "Curso de liderança"]
  }
}
```

```json
{"ok": true, "method": "form.1x1",
 "result": {"id": 42, "tipo_formulario": "form.1x1",
            "created_at": "2026-08-21T14:03:11.204Z"}}
```

### 4. Ler os formulários guardados — os seis `form.*.get`

Cada nome de formulário responde também a `{nome}.get`: `form.1x1.get`, `form.pdi.get`,
`form.9box.get`, `form.autoavaliacao.get`, `form.avaliacao_lider.get` e `form.pulse.get`. Volta
`respostas`, da mais recente para a mais antiga, cada item com `id`, `tipo_formulario`,
`area`, `lider_id`, `colaborador_id`, `created_at` e o `raw` inteiro.

| Param | Obrigatório | Efeito |
|---|---|---|
| `requester_email` | sim | Quem está perguntando; é o que define o alcance |
| `area` | não | Só aquela área, ignorando caixa e espaço em volta |
| `lider_id` | não | Só o que aquela pessoa preencheu |
| `colaborador_id` | não | Só o que é sobre aquela pessoa |
| `quantidade` | não | De 1 a 50 itens; sem ela, 50 |

Os filtros se somam (E, não OU). Fora da faixa de `quantidade` é erro de validação, não corte
silencioso.

**O alcance é o do nível, e ele filtra em vez de recusar.** Nível 3+ (`team_people`) lê tudo.
Abaixo disso, a lista traz só o que a pessoa preencheu, o que é sobre ela e o que é sobre um
liderado direto — inclusive liderado já desligado, porque o histórico é de quem acompanhou.
**Lista vazia não prova que o formulário não existe**: pode existir fora do alcance de quem
perguntou. Diga que não encontrou *para aquela pessoa*, não que não existe.

**Quem pergunta precisa existir no cadastro.** `requester_email` que o cadastro não conhece
responde `404 EMPLOYEE_NOT_FOUND` — é a única recusa desta leitura, e não se confunde com lista
vazia. Mande o e-mail que veio de `access.verify`, não o que a pessoa digitou.

`form.pulse.get` é o caso especial: clima não grava id de ninguém, então para quem não é People
o recorte não alcança nada e a lista volta vazia — o anonimato continua de pé. Para People, o
conteúdo é o mesmo de `pulse.answers`; a diferença é o corte, aqui por área e quantidade, lá
pela janela da rodada.

```json
{"method": "form.1x1.get",
 "params": {"requester_email": "ana@condoconta.com.br", "area": "Banking Operations",
            "quantidade": 5}}
```

### 5. Pesquisa de clima — os cinco `pulse.*`

Todos são administração e **exigem nível 3 (`team_people`) ou acima**, respondendo
`403 NOT_PEOPLE` a quem estiver abaixo. Quem responde o clima usa `form.pulse`, não estes.

| Método | Params obrigatórios | O que faz |
|---|---|---|
| `pulse.open_round` | `requester_email`, `ano`, `mes`, `inicio`, `fim` | Abre a rodada do mês (`observacao` é opcional) |
| `pulse.close_round` | `requester_email` | Encerra; sem `ano`/`mes`, a que está aberta hoje |
| `pulse.reopen` | `requester_email`, `ano`, `mes`, `fim` | Reabre uma encerrada, com prazo novo |
| `pulse.round_status` | `requester_email` | Convidados, responderam, faltam, adesão |
| `pulse.answers` | `requester_email` | As respostas que caíram na janela |

**O recorte de `round_status` e `answers` é o mesmo:** sem `ano`/`mes`, a rodada **mais
recente**; com `ano` só, **todas as daquele ano**; com `ano` e `mes`, aquela. Os dois respondem
uma **lista** em `rodadas`, mesmo com um item só.

`round_status` devolve, por rodada: `pesquisa_id`, `competencia` (`AAAA-MM`), `inicio`, `fim`,
`aberta`, `convidados`, `responderam`, `faltam`, `adesao_pct`.

`answers` devolve, por rodada: `pesquisa_id`, `competencia`, `inicio`, `fim`, `qtd_respostas` e
`respostas[]` — cada uma com `id`, `created_at` e `raw`, o preenchimento como a pessoa mandou.

**Como as respostas são encontradas.** A resposta gravada **não referencia a rodada**: o que a
seleciona é a janela `inicio`..`fim`. Uma rodada reaberta com `fim` mais longo passa a incluir o
que chegou na extensão, sem nada ser reetiquetado. `qtd_respostas` é o contador da rodada e deve
bater com o tamanho de `respostas[]`.

**A adesão.** `responderam` é o contador da rodada; `convidados` é a contagem de colaboradores
ativos **hoje**, não uma lista de convites. Uma rodada antiga lida depois de admissões e
desligamentos tem denominador diferente do que tinha na época — não é erro, é o desenho.

**Reabrir exige prazo.** `ano`, `mes` e `fim` são todos obrigatórios: a rodada reaberta é, por
definição, uma que já terminou, e sem prazo novo ela voltaria com a janela no passado e
`round_status` continuaria dizendo que está fechada. Não existe "reabrir a atual".

**Anonimato.** `round_status` devolve **contagem, nunca nomes**, e `form.pulse` não pede id de
ninguém — não há como saber quem respondeu, e não prometa que há. Ao comentar resultado por
área, lembre que em time pequeno o texto livre pode identificar a pessoa pelo conteúdo; em
recorte pequeno, não repasse texto livre.

**Exemplo**

```json
{"method": "pulse.round_status", "params": {"requester_email": "people@condoconta.com.br"}}
```

```json
{"ok": true, "method": "pulse.round_status",
 "result": {"rodadas": [{"pesquisa_id": 2, "competencia": "2026-08",
                         "inicio": "2026-08-01", "fim": "2026-08-31", "aberta": true,
                         "convidados": 121, "responderam": 37, "faltam": 84,
                         "adesao_pct": "30.6"}]}}
```

### 6. Recarregar o cadastro — `roster.sync`

Sem parâmetros. **Volta** as contagens: `employees`, `departments`, `jobs`, `cost_centers`,
`slack_ids_matched`, `deactivated`.

É o que faz `access.verify` conhecer alguém: depois de admissão, desligamento ou mudança de
gestor, o cadastro só reflete a realidade depois de um sync. Quem sai da listagem do Convenia é
**marcado como inativo, nunca apagado**.

**Quando não chamar.** É a chamada mais cara do serviço e a única que depende de credencial
externa. Não use como tentativa às cegas quando alguém "não foi encontrado": nenhum sync
resolve os 18 colaboradores sem e-mail no Convenia. Antes de sincronizar, confirme o e-mail.

### 7. O catálogo — `system.describe`

| Param | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `method_name` | string | não | Restringe a um método |

Use sempre que houver dúvida sobre um contrato, e sempre que um método parecer não existir.
Esta skill pode envelhecer; o catálogo não.

---

## As exceções — onde o comportamento foge do esperado

Estas são as coisas que quebram a intuição. Ler antes é mais barato que descobrir errando.

**`form.pulse` é a única exceção ao "só armazenar".** Resposta de clima só existe dentro de uma
rodada: sem rodada aberta, `409 NO_OPEN_ROUND` e **nada é gravado**. Avise People em vez de
tentar de novo. Cada resposta aceita incrementa o contador da rodada.

**Só os `form.*` aceitam campo livre.** Neles, campo desconhecido passa e é guardado. Em todos
os outros métodos os parâmetros são fechados: campo a mais é `400 MISSING_PARAMS`.

**Ninguém pede a rodada.** O serviço resolve a que está aberta. Aceitar a rodada de quem chama
permitiria gravar resposta em período fechado.

**Segunda-feira não cobre só a segunda** nas comemorações — inclui o fim de semana anterior.

**Nível de acesso é filtro de leitura nos `form.*.get`, e só neles.** Ali o serviço já recorta
pelo nível de `requester_email`. Em todo o resto ele informa o nível e aplicar o recorte é seu.

**Slack ID pode ser nulo, e-mail também.** Não trate ausência como pessoa inexistente.

**`roster.sync` desativa quem não veio na listagem — mas nunca a partir de lista vazia.** Uma
leitura falha que retornasse zero rebaixaria todo líder para nível 1, e o serviço se protege
disso. Ainda assim, não repita o sync esperando resultado diferente.

**Um `id` que não existe no cadastro entra sem reclamar.** `lider_id` e `colaborador_id` dos
formulários não são validados contra o cadastro — mande o que veio de `access.verify`, porque
digitar errado grava errado em silêncio.

## Erros: o que cada um quer dizer

| `code` | HTTP | O que fazer |
|---|---|---|
| `MISSING_PARAMS` | 400 | O campo faltante vem em `fields`. Pergunte só o que falta |
| `EMPTY_IDENTIFIER` | 400 | O identificador ficou vazio após a limpeza; peça de novo |
| `NOT_PEOPLE` | 403 | Só nível 3+ administra a pesquisa de clima |
| `EMPLOYEE_NOT_FOUND` | 404 | Cadastro não conhece o identificador — ou o `requester_email` de um `form.*.get` |
| `ROUND_NOT_FOUND` | 404 | Não existe rodada de clima para aquele recorte |
| `UNKNOWN_METHOD` | 404 | Nome de método errado; consulte `system.describe` |
| `NO_OPEN_ROUND` | 409 | Nenhuma rodada aberta para receber resposta ou ser encerrada |
| `ROUND_ALREADY_EXISTS` | 409 | Já existe rodada para aquele mês |
| `ROUND_ALREADY_CLOSED` | 409 | Aquela rodada já foi encerrada |
| `ROUND_NOT_CLOSED` | 409 | A rodada que você quer reabrir não está encerrada |
| `INVALID_WINDOW` | 409 | O `fim` pedido é anterior ao início da rodada |
| `CONSTRAINT_VIOLATION` | 409 | O dado colide com um registro existente |
| `UPSTREAM_UNAVAILABLE` | 502 | Convenia ou Slack não respondeu. Tente mais tarde |
| `MISSING_CREDENTIALS` | 503 | Falta credencial no serviço. É infraestrutura, não do usuário |

Um corpo que não é JSON válido, ou sem `method`, responde **422** no formato do framework
(`{"detail": [...]}`), não neste envelope. Nome de método errado é resolvido **antes** dos
parâmetros: método inexistente com params inválidos devolve 404, nunca 400.

## O que nunca fazer

- Assumir nível de acesso depois de uma verificação que falhou.
- Montar `lider_id` ou `colaborador_id` por conta própria em vez de tirá-los de `access.verify`.
- Mandar link de `/forms` — as páginas HTML não existem mais.
- Resumir ou filtrar as respostas de um formulário antes de gravá-las.
- Enviar a rodada de clima; o serviço resolve a que está aberta.
- Recalcular adesão; ela vem pronta de `round_status`.
- Prometer descobrir quem respondeu o clima, ou tentar deduzir pelo texto livre.
- Repetir `roster.sync` para achar alguém que não tem e-mail no Convenia.
- Repassar dado de uma pessoa a quem o nível de quem pediu não alcança.