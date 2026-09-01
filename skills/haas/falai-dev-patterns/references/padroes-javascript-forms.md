- **"Pesquisa Pulses"** (PLURAL). Nunca "Pulse" singular em título/link/comunicado.
- Link oficial: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`
- Legado `pulse-satisfacao` foi DESCONTINUADO.

## Slack formatting

Links nunca entre asteriscos.
✅ `*Link:* https://url`  |  ❌ `*Link: https://url*`

## Líder — dropdown com múltiplos liderados (client-side)

O `gerar_form_lider.py` não faz `access.verify` no Python — injeta o email e as perguntas
embutidas como `PERGUNTAS_MAP` (JSON string). O navegador resolve tudo no load:

```javascript
// A página carrega → access.verify (client-side) → reports[] → dropdown
fetch('/proxy/condopower-rpc',{...access.verify...}).then(function(r){
  LIDERADOS = r.result.reports.map(function(rep){ return {
    id: rep.id, nome: rep.full_name, cargo: rep.job,
    departamento: rep.department,
    perguntas: matchPerguntas(rep.full_name) // busca no PERGUNTAS_MAP embutido
  };});
  rebuildDropdown();
});
```

Cookie `avaliacao_lider_feitos=[u1,u2]` rastreia liderados já avaliados (10 dias).
Dropdown remove cada um após submit bem-sucedido. Só mostra agradecimento quando zerar.

## Perguntas — ordem garantida

Autoavaliação e líder têm perguntas DIFERENTES (instrumentos distintos), mas cada um
é internamente consistente:
- Python itera `col["perguntas"]` na ordem do JSON
- JS renderiza na mesma ordem
- Submit envia `{enunciado: resposta}` na ordem do DOM
- **Não trocar `Object` por `Array`** — o contrato da API é `{"pergunta": "resposta"}`

## 1x1 consolidado — submit múltiplo

Botão único dispara 3 chamadas em paralelo:
```javascript
async function submitAll(){
  await post('form.1x1', {justificativa, lider_id, colaborador_id, area});
  await post('form.9box', {nota_resultados, nota_potencial, lider_id, colaborador_id});
  await post('form.pdi', {competencia_foco, gap_evidencia, ...});
}
```
Erro em uma não bloqueia as outras.

## Validação de obrigatoriedade antes do submit

**Escalas/textarea** (autoavaliação/líder): checar todos `[data-pergunta]` antes de enviar.
Scroll até primeira pendente. Mensagem: "⚠️ Preencha todas as perguntas (N pendentes)".

**Dropdowns/hidden** (pulses): validar por seletor CSS, array `{sel, msg}`.