---
name: condopower-formularios
description: Formulários People via proxy da condopower-api.
version: 1.2.0
---

# condopower-formularios — formulários HTML de People

## Changelog
- **v1.3.0 (01/09/2026):** 1x1 refatorado com `div.stars` (padrão autoavaliação/líder) + mapeamento semântico por palavra-chave. Skill `falai-form-1x1` criada com referências. Duplicatas removidas: `gerar_form_avaliacao_v2.py`, `gerar_form_autoavaliacao.py`, `gerar_form_lider_v2.py` (usar apenas `gerar_form_avaliacao.py`, `gerar_form_lider.py`, `gerar_form_1x1.py`). Hermes tem suporte nativo a webhooks (`platforms.webhook`) para receber POST de serviços externos.
- **v1.1.0 (27/08/2026):** Endpoint do webhook-proxy corrigido (sem `/rpc`). `gerar_form_lider.py` reescrito 100% client-side. Pergunta de Recomendação removida. Validação JS de obrigatoriedade adicionada em todos os forms.

## Arquivos por formulário

| Formulário | Gerador |
|---|---|
| Pulses (pesquisa de clima) | HTML estático `/opt/data/formularios/form-pulse.html` — sem .py |
| Autoavaliação | `/opt/data/convenia/gerar_form_avaliacao.py <email>` |
| Avaliação do Líder | `/opt/data/convenia/gerar_form_lider.py <email_lider>` |
| 1x1 (consolidado) | `/opt/data/convenia/gerar_form_1x1.py <email_lider> <email_colab>` |
| PDI / 9box | ainda sem gerador próprio — o fluxo vive dentro do 1x1 |

Publicação (todos): POST multipart no webhook do static-server
`https://webhook-proxy.condoconta.com.br/webhooks/static-server` com
`X-Service-Account-Token` do `.env` (var `STATIC_SERVER_SA_TOKEN`) e `-F slug=... -F file=@...;type=text/html`.

## REGRA DE OURO DO SUBMIT — proxy same-domain (evita CORS)

O navegador NÃO consegue fazer `fetch` cross-origin para a condopower-api:
o preflight OPTIONS cai em redirect de login e o browser aborta
(`Redirect is not allowed for a preflight request`).

**Solução que funciona:** o submit DEVE ir para o proxy no MESMO domínio do static-server:

```javascript
fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc', {
  method:'POST',
  headers:{'Content-Type':'application/json'},   // SÓ isto — sem tokens
  body:JSON.stringify({method:'form.<tipo>', params: dados})
})
```

- **Zero tokens no navegador.** O proxy injeta `X-Service-Account-Token` e `auth` server-side.
  Nunca exponha os tokens no JS do form (o usuário pediu explicitamente para remover).
NUNCA apontar o fetch para `condopower-api.aiexpert-condoconta.info/rpc` direto,
nem para `webhook-proxy...` — cross-origin quebra no preflight.

## Resolução de identidade CLIENT-SIDE

O container Python NÃO alcança a condopower-api (404/timeout), mas o navegador alcança
via proxy. Então `colaborador_id` (UUID do Convenia) DEVE ser resolvido no JS, no load da página,
não no Python:

```javascript
var COLABORADOR_ID = '';
(function(){
  var email = document.getElementById('colaborador_email').value;
  fetch('/proxy/condopower-rpc', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({method:'access.verify', params:{identifier:email}})
  }).then(r=>r.json()).then(r=>{
    if(r.ok && r.result && r.result.employee) COLABORADOR_ID = r.result.employee.id;
  });
})();
```

No submit, guarda-se: se `!COLABORADOR_ID`, mostra "Aguarde... identificando" e `return`.
O JSON de origem (`autoavaliacao_perguntas.json`) NÃO tem `id`/`uuid`/`email` — só
`nome, aba, cargo, area, nivel, step, gestor, qtd_perguntas, perguntas`. O UUID só vem de
`access.verify`.

## Pitfalls de geração de HTML (já morderam)

1. **`{{`/`}}` escapando pro JS.** Em strings Python que montam HTML, `{{`/`}}` vazam
   literais e QUEBRAM todo o bloco `<script>` (sintoma: botões de escala não ficam amarelos
   ao clicar, pois `selStar`/`selReco` nunca executam). Confirme no HTML gerado com
   `grep -c "{{" arquivo.html` == 0. Use a forma de string correta para o contexto
   (f-string vs string normal vs raw string) — não misture escapes.
2. **Aspas em `value=` de hidden input.** Interpole valores com `json.dumps(valor)`, não
   concatenação crua — senão o valor vai pro banco com barra invertida
   (`"area": "\"Finance\""` em vez de `"Finance"`).
3. **`required` nativo não valida `type=hidden`.** Escalas de 1-5 e eNPS usam hidden input
   preenchido via JS. A validação de obrigatório tem que ser em JS, não `required` no HTML.
   Padrão: array de `{sel, msg}` e loop antes do submit, com `scrollIntoView` no campo faltante.
4. **`form.*` aceita campo livre, mas o resto não.** `form.pulse`/`form.autoavaliacao` etc.
   gravam qualquer campo de `params`. Métodos como `access.verify` rejeitam campo extra com 400.

## Ciclo de vida do cookie (10 dias — preferência do usuário)

- `max-age=864000` (10 dias). O usuário NÃO quer localStorage (não expira) — usar cookie.
- Chaves por formulário: `pulses_respondido=1`, `autoavaliacao_respondida=1`,
  `avaliacao_lider_feitos=<json array de UUIDs>`.
- Fluxo padrão: no load, checar cookie → se presente, esconder form e mostrar `.thank-you`.
  No submit OK: `document.cookie = '<chave>=...;max-age=864000;path=/'` → esconder form →
  mostrar `.thank-you`.

## Avaliação do Líder — múltiplos liderados (padrão especial)

O líder avalia vários liderados. O cookie guarda um JSON array de UUIDs já avaliados:
- `getFeitos()` lê e parseia o cookie; `setFeitos(list)` grava com `encodeURIComponent(JSON.stringify(list))`.
- `rebuildDropdown()` remove do `<select>` os liderados já avaliados.
- A mensagem de agradecimento só aparece quando o dropdown ficar vazio (todos avaliados).
- No submit: `feitos.push(colaborador_id)` → `setFeitos` → reset do form (dropdown de volta).

**Identidade também client-side.** O `gerar_form_lider.py` embute as perguntas do ciclo
(`avaliacao_lider_perguntas.json`, via mapa nome→perguntas) e o `access.verify` do líder +
`reports[]` é feito no JS no load, igual à autoavaliação. O Python não chama a API.

**A pergunta de "Recomendação" é REMOVIDA do formulário.** O JSON traz 8 perguntas por
liderado, mas a última ("Recomendação para este colaborador neste ciclo — Promoção / Mérito /
Bônus / ...") é filtrada no gerador (`filtrar_perguntas()` dropa texto contendo
"recomendação"/"recomendacao"). Fica 7 perguntas no form — a recomendação é tratada fora do
formulário.

## Comunicados no Slack — regra de link

NUNCA colocar link entre asteriscos (`*link*`). O Slack renderiza `*` como negrito e o link
quebra. Link sempre SOLTO, com o rótulo em negrito antes:
`📝 *Link do formulário:* https://...` (correto) vs `*Link: https://...*` (errado).

## Referências
- `references/sql-fix-q7q8-swap.md` — SQL (SQLite e PostgreSQL) para corrigir respostas já salvas com Q7/Q8 invertidas
- `references/confluence-step-atual.md` — extrair trilhas do Confluence e injetar step_atual no JSON
- `references/perguntas-reorder-pattern.md` — padrão de reordenação de perguntas no render (Q7↔Q8 autoavaliação, Q5→Q7→Q6→Q5 líder)
- `references/step-atual-display.md` — mostrar step_atual no form do líder (card azul abaixo do nome)
- `references/extract-confluence-steps.md` — script de extração em lote de 38 cargos × 15 steps
- `references/layout-fullscreen-1x1.md` — layout full-screen do 1x1 (60/40, header full-width, scroll único, 9box grande)
- `references/1x1-semantic-mapping.md` — mapeamento semântico das 8 linhas comparativas auto×líder (keywords por conceito)
- `references/1x1-stars-pattern.md` — padrão div.stars com gradiente dual-color (sel-auto/sel-lider/mixed)
- `references/git-secrets-cleanup.md` — remover tokens do histórico git com `filter-branch` + push force
