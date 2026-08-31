---
name: falai-dev-patterns
description: HTML form JS pitfalls, cookies, localStorage, Slack links.
version: 1.0.0
---

# Falai Development Patterns

## JS objects inside Python raw strings

`{{}}` in `r"""..."""` gets mangled. Use string concatenation + `json.dumps()`.

```python
# ✅ Right
html = 'function foo(){var x = {}, v = ' + json.dumps(cid) + ';}'
```

## Hidden input values

Always use `json.dumps()` — never backslash-escaping (`value=\\\"...\"`).

```python
html += '<input type="hidden" id="area" value=' + json.dumps(carea) + '>'
```

## Token injection in fetch()

Use placeholders + post-generation replace:
```python
html = html.replace("__SA_TOKEN__", SA).replace("__AUTH_TOKEN__", AUTH)
```

## Submit endpoint — proxy same-domain (resolve CORS)

**SEMPRE** usar o proxy do static-server, nunca o domínio da API diretamente:
```
https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc
```
Fetch direto para `condopower-api.aiexpert-condoconta.info/rpc` dispara preflight OPTIONS
cross-origin → o proxy/Traefik devolve `302` pra login → navegador aborta
`Redirect is not allowed for a preflight request` → `ERR_FAILED`.

O proxy INJETA `X-Service-Account-Token` e `auth` server-side. O fetch do navegador NÃO deve
levar tokens — só `Content-Type: application/json` (o usuário pediu explicitamente para
remover auth/x-service-account-token do headers). Formulário com token exposto no JS = leak.

## Form state

**Cookie** (10 dias): `document.cookie='k=1;max-age=864000;path=/';`
Check: `document.cookie.indexOf('k=1')>=0`
Use `max-age=864000` = 10 dias (padrão da Falai).

**localStorage NÃO expira** — sem max-age. Quando o usuário pedir ciclo de vida limitado
(ex. 10 dias), usar cookie, NÃO localStorage. Para lista multi-item com prazo, guardar array
JSON no cookie: `document.cookie='k='+encodeURIComponent(JSON.stringify([id1,id2]))+';max-age=864000;path=/'`
e ler com `document.cookie.split('; ').find(r=>r.startsWith('k='))`.

## colaborador_id vem de access.verify

`form.autoavaliacao`, `form.avaliacao_lider`, `form.1x1`, `form.pdi`, `form.9box` EXIGEM
`colaborador_id` (UUID do Convenia). Esse id vem de `access.verify` — se a API estiver fora
do ar no container, o `value=""` sai vazio e a API devolve `400 MISSING_PARAMS`
("Parâmetros inválidos ou ausentes"). **`form.pulse` é a exceção**: anônimo, não exige id —
por isso Pulses funciona mesmo quando a API de identidade está fora do ar.

## Resolver colaborador_id CLIENT-SIDE (quando o container não alcança a API)

**Diagnóstico:** o container Python NÃO alcança `condopower-api` (timeout/404), mas o
NAVEGADOR alcança via `/proxy/condopower-rpc` (mesmo domínio do static-server). Então o
`access.verify` deve ir pro JS do formulário, não pro gerador Python.

**Padrão (autoavaliação):** injeta o email como hidden input no HTML e resolve o UUID no
`load` da página:

```python
# Python: injeta só o email (sem access.verify server-side)
html += '<input type="hidden" id="colaborador_email" value=' + json.dumps(cemail) + '>'
```

```javascript
var COLABORADOR_ID = '';
(function(){
  var email = document.getElementById('colaborador_email').value;
  fetch('https://static-server.aiexpert-condoconta.info/proxy/condopower-rpc',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({method:'access.verify',params:{identifier:email}})
  }).then(function(r){return r.json()}).then(function(r){
    if(r.ok && r.result && r.result.employee) COLABORADOR_ID = r.result.employee.id;
  });
})();
// No submit: se !COLABORADOR_ID → "Aguarde... identificando", não enviar ainda.
```

**Por que não basta o JSON de origem:** `autoavaliacao_perguntas.json` e
`avaliacao_lider_perguntas.json` NÃO trazem `id`/`uuid`/`email` — só
`nome, aba, cargo, area, nivel, step, gestor, qtd_perguntas, perguntas`. O UUID só existe
via `access.verify`.

## Nomes e links

- **"Pesquisa Pulses"** (PLURAL). Nunca "Pulse" singular em título/link/comunicado.
- Link oficial: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
- Legado `pulse-satisfacao` foi DESCONTINUADO.

## Slack formatting

Links nunca entre asteriscos.
✅ `*Link:* https://url`  |  ❌ `*Link: https://url*`

## Regra absoluta — nunca ser proativa com side effects

A Falai **NUNCA** executa ações com efeitos colaterais permanentes sem pedido explícito do usuário.

Exemplos de ações PROIBIDAS sem pedido explícito:
- `git commit`
- `skill_manage` (create/edit/patch/delete) sem o usuário pedir
- Enviar mensagens no Slack sem o usuário pedir
- Alterar `.env`, `config.yaml` ou SOUL.md sem o usuário pedir
- Deletar arquivos ou skills sem o usuário pedir
- Publicar formulários sem o usuário pedir

**Status queries são OK** (listar, verificar, diagnosticar, buscar). **Side effects NÃO.**

Quando o usuário pede pra VERIFICAR se tem commits pendentes, a resposta correta é listar o `git status`, NÃO commitar. Commitar é uma ação separada que requer pedido explícito.

**Origem da regra:** a Falai commitou alterações sem ser solicitada em 28/08/2026 — o usuário corrigiu: "não seja proativo".