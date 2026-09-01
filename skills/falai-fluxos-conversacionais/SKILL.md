---
name: falai-fluxos-conversacionais
description: Fluxos People. 1x1 com feedback, PDI e avaliacao.
version: 3.0.0
---

# Fluxos People — Conversacionais

## Permissões

| Role | Acesso |
|---|---|
| superadmin (5) | ✅ |
| admin (4) | ✅ |
| team_people (3) | ❌ |
| condo_leader (2) | ❌ |
| condopower (1) | ❌ |

SOMENTE levels 4 e 5 podem usar esta skill.

## Regra de Entrada (OBRIGATORIA)
1. Identificar quem esta falando via `access.verify` da API `condopower-api` (Slack ID → level/role/reports)
2. Resolver role/level — a API ja retorna tudo em uma chamada so
3. Se 0 liderados e for fluxo de lideranca = encerrar: "Voce nao possui liderados ativos."
4. Se 1+ = listar numerado e perguntar qual

⚠️ Preferencia do usuario: fazer SOMENTE o solicitado, de forma objetiva. Sem suposicoes, sem proatividade extra.

## Fluxo 1x1 com Feedback (12 etapas)

Registro via API `condopower-api` → `form.1x1` (campos livres, sem schema fixo)

| # | Pergunta | Campo |
|---|---|---|
| 1 | "Quem e o colaborador? (nome ou email)" | colaborador_id |
| 2 | "Data do 1x1? (DD/MM/AAAA)" | data |
| 3 | "Formato? 1=Presencial, 2=Remoto" | formato_id |
| 4 | "Energia (1-5) e Motivacao (1-5)? Ex: 4 3" | energia, motivacao |
| 5 | "Pauta do liderado? (- para pular)" | pauta_liderado |
| 6 | "Encaminhamentos? (- para pular)" | encaminhamentos |
| 7 | "Feedback — Tipo? 1=Positivo, 2=Construtivo, 3=Ambos (- para pular)" | tipo_id |
| 8 | "Feedback — Situacao? (- para pular)" | situacao |
| 9 | "Feedback — Comportamento? (- para pular)" | comportamento |
| 10 | "Feedback — Impacto? (- para pular)" | impacto |
| 11 | "Feedback — Acordado? (- para pular)" | acordado |
| 12 | "Proximo 1x1? (DD/MM/AAAA) (- para pular)" | proximo_1x1 |

Chamadas API: `POST /rpc` com `{"method":"form.1x1","params":{...}}` via `condopower-api`.
Campos livres — mande tudo que foi coletado. O que não for preenchido, omita.

---

## Fluxo PDI (8 etapas)

Registro via API `condopower-api` → `form.pdi` (campos livres)

| # | Pergunta | Campo |
|---|---|---|
| 1 | "Para quem e o PDI? (nome ou email)" | colaborador_id |
| 2 | "Qual competencia sera o foco?" | competencia_foco |
| 3 | "Qual a evidencia do gap atual?" | gap_evidencia |
| 4 | "Tipo? 1=70% Pratica, 2=20% Social, 3=10% Formal" | tipo_acao_id |
| 5 | "Descreva a acao" | descricao_acao |
| 6 | "Prazo? (DD/MM/AAAA)" | prazo |
| 7 | "Como sera evidenciada a conclusao?" | evidencia_conclusao |
| 8 | "Status? 1=Nao iniciado, 2=Em andamento, 3=Concluido, 4=Atrasado" | status_id |

---

## Fluxo Avaliação — Formulários HTML (Ciclo 2026.2)

⚠️ NÃO usar fluxo textual. Usar sistema de formulários HTML + RBAC:

**RBAC:** `condopower-rbac` (níveis 1-5, cada nível com fluxos específicos por método)
**API:** `condopower-api` v2.0.0 — métodos renomeados:
- `desempenho.register_avaliacao` → `form.autoavaliacao` (autoavaliação)
- `desempenho.register_avaliacao` → `form.avaliacao_lider` (avaliação pelo líder)
- `pulse.submit` → `form.pulse`

**Arquivos:**
- `gerar_form_avaliacao.py <email>` — HTML de autoavaliação (SOMENTE autoavaliação desde 21/08)
- `gerar_form_lider.py <email>` — HTML unificado líder: dropdown com `reports[]` + perguntas dinâmicas
- `pesquisa-pulses` — HTML estático em `/opt/data/formularios/form-pulse.html`

⚠️ **URL slug = prefixo do e-mail, NÃO nome.** `gerar_form_lider.py` usa `EMAIL.split("@")[0].replace(".", "-")`. Ex: `rodrigo.catarcione@` → `avaliacao-lider-rodrigo-catarcione`. Usar nome completo gera link quebrado. Template de DM e fluxo completo em `references/lancamento-ciclo-dm-lideres.md`.

### ⛔ Lançamento de Ciclo — Pitfalls Críticos (NUNCA ignorar)

**Leia `references/pitfalls-lancamento-ciclo.md` ANTES de qualquer lançamento.** Contém:

1. **Fuzzy matching troca links** — `gerar_form_avaliacao.py` usa matching por partes de nome; nomes truncados (31 chars) no JSON causam colisões. Solução: `email_override_map.json` + script patchado com prioridade de override.
2. **DMs sobrescritas** — Editar DMs sem atualizar JSON fonte primeiro corrompe todas as correções. SEMPRE: atualizar JSON → regravar → `chat.update`.
3. **Auditoria pós-envio obrigatória** — Ler cada DM do Slack e verificar se o slug contém partes do nome da pessoa.
4. **Menção no Slack** — usar `<@U0AS4CSDUUU>`, NUNCA `@U0AS4CSDUUU`.

### 📨 Templates de DM

**Templates completos em `references/dm-templates-avaliacao.md`.**
- Template liderança: CHA, deadline, lista de liderados, link do formulário unificado
- Template autoavaliação: CHA, deadline, link individual
- Menção padrão: `<@U0AS4CSDUUU>` (Luana)

### 🔗 Executivos C-Level — Fora do JSON Padrão

Líderes que reportam ao CEO podem não estar no JSON de autoavaliação. Fluxo:
1. Cruzar `relatorio_lideres.json` × `resultado_envio_autoavaliacao.json` para identificar faltantes
2. Solicitar planilhas `.xlsx` individuais
3. Extrair perguntas do XML do Excel (colunas B e D)
4. Gerar HTML com template CondoConta e publicar via static-server
5. Para o CEO (Rodrigo Della Rocca): formulário de avaliação de liderança unificado com dropdown de 6 C-levels, cada um com Q2 específico da área
6. **Reordenar perguntas** conforme `references/avaliacao-ordem-unificada.md` — autoavaliação e liderança DEVEM seguir a mesma ordem (1=Resultados, 2=Área, 3=Competências, 4=Autonomia, 5=Potencial, 6=V+, 7=V-, 8=PDI/Recomendação)

**Submit (todos os formulários):** padrão unificado desde 21/08:
```javascript
fetch('https://condopower-api.aiexpert-condoconta.info/rpc', {
  method:'POST',
  headers:{'Content-Type':'application/json','X-Service-Account-Token':SA,'auth':AUTH},
  body:JSON.stringify({method:'form.<tipo>',params:{...}})
})
```
Auth headers (`X-Service-Account-Token` + `auth`) injetados no HTML gerado. URL direta (sem webhook-proxy) para que o navegador do usuário alcance a API diretamente.

---

---

## Fluxo Pulse — Engajamento de Líderes via DM

⚠️ **Fluxo com alto índice de retrabalho se feito errado.** Leia `references/pulse-lideres-dm-v2.md` ANTES de começar.

### Checklist obrigatória

Antes de enviar QUALQUER DM sobre Pulse:
- [ ] Contagens extraídas de `pulse.answers` por `raw.lideranca_direta`
- [ ] Slack IDs resolvidos via `access.verify`
- [ ] **NENHUMA menção a áreas/departamentos** na mensagem
- [ ] Tom: "X pessoas do seu time já responderam" (NÃO "recebemos X respostas do seu time")
- [ ] Resumo mostrado ao solicitante com aprovação explícita ANTES de disparar
- [ ] Líderes sem Slack ID reportados separadamente

### Template

Ver `references/pulse-lideres-dm-v2.md` para template completo e pitfalls.

---

## Fluxo Contestação de Avaliação — "Essa pessoa não é meu liderado"

Quando um líder contesta que precisa avaliar alguém, a pessoa pode ser liderado indireto (2 níveis abaixo) ou pode haver erro de atribuição no JSON do Convenia.

### Etapas

| # | Ação | Detalhe |
|---|---|---|
| 1 | Verificar `reports[]` do líder | Chamada `access.verify` já feita na identificação |
| 2 | Se a pessoa **não está** nos diretos → traçar cadeia | Para cada `report`, chamar `access.verify` com o email dele e inspecionar `reports[]` |
| 3 | Se encontrou em nível 2 → confirmar | Mostrar a cadeia completa com tree diagram (líder → gestor direto → colaborador) |
| 4 | Se **não encontrou** em nenhum nível → erro de atribuição | Notificar People (passo 7) |
| 5 | Se encontrou como indireto → explicar | "X é liderado da [Gestora Direta], que reporta a você. A avaliação de liderança é da líder direta, não sua." |
| 6 | Se líder diz "te vira" / "resolve" / "se vira" → ação autônoma | NÃO pedir permissão. Ir direto pro passo 7. |
| 7 | Notificar time de People | DM para Catarcione (U0AFGRGC80P) + post no #people-hr (C0BJLA3H16F) |
| 8 | Fechar com o líder | Confirmar que People foi notificado e vai ajustar a atribuição |

### "Te vira" = ação autônoma imediata

Quando um líder sênior (C-level, VP, diretor) responde com "te vira", "resolve aí", "se vira" ou similar, ele está **delegando propriedade total da tarefa**. NÃO pergunte "quer que eu avise o People?" — isso demonstra insegurança. Aja:

1. Postar no **#people-hr** (C0BJLA3H16F): nome do líder, pessoa contestada, cadeia hierárquica, ação necessária
2. DM para **Catarcione** (U0AFGRGC80P) com os mesmos detalhes
3. Responder ao líder confirmando: "✅ Feito! Já notifiquei o Catarcione e o time de People no #people-hr."

### Canais e UIDs críticos

| Recurso | ID |
|---|---|
| #people-hr (canal) | C0BJLA3H16F |
| Catarcione (DM) | U0AFGRGC80P |

### Exemplo real (28/08/2026)

Luciano Bernardi (CFO) contestou Vitor Pacheco na lista de avaliação:
- Vitor é liderado da **Renata Paim** (Treasury Manager), que reporta ao Luciano
- → Vitor é **liderado indireto**, 2 níveis abaixo
- Luciano disse "Sim, te vira" → Falai notificou #people-hr + Catarcione

### Ver também

- `references/avaliacao-lista-lideres.md` — extração líderes×liderados e correção de JSON quando lista é contestada

---

## Regras Gerais
- Uma pergunta por vez
- Validar cada resposta
- Confirmar resumo antes de salvar
- NUNCA salvar sem "ok"
- NUNCA enviar DM/comunicado sem aprovação prévia do solicitante
- Slack ID do destinatário → `access.verify` (identifica e obtém slack_user_id)
- ⛔ **DM PARA LÍDERES — NUNCA dizer "me avise por aqui":** líderes não conseguem responder ao bot por DM. Sempre rotear alterações para a pessoa do time de People que solicitou o envio. Ver `references/dm-lideres-roteamento.md`.

## Tratamento de Erros da API (OBRIGATORIO)

⛔ **REGRA ABSOLUTA (20/08/2026, definido por Leonardo):** Quando QUALQUER endpoint da condopower-api retornar erro durante um fluxo (1x1, feedback, PDI, avaliacao), a Falai DEVE automaticamente:

1. **Abrir ticket de Bug no Jira PAIX** com todos os detalhes: colaborador afetado, dados preenchidos, erro retornado (codigo + mensagem)
2. **Informar o usuario** do erro e do link do ticket criado
3. **NUNCA simplesmente reportar o erro e parar** — o ticket DEVE ser criado

### Erros que disparam ticket automatico

| Erro | Ticket requerido? |
|---|---|
| `NOT_YOUR_REPORT` | ✅ Sim |
| `NO_OPEN_CYCLE` | ✅ Sim |
| `CONSTRAINT_VIOLATION` | ✅ Sim |
| `NO_OPEN_ROUND` | ✅ Sim |
| `ROUND_ALREADY_EXISTS` | ✅ Sim |
| `EMPLOYEE_NOT_FOUND` | ❌ Nao (problema de cadastro) |
| `LEADER_NOT_FOUND` | ❌ Nao (problema de cadastro) |
| `UPSTREAM_UNAVAILABLE` | ❌ Nao (transiente) |

Template do ticket em `references/jira-bug-template.md`.

## Ver também

- `condopower-rbac` — RBAC por nível (fluxos de cada método por permissionamento)
- `condopower-api` v2.0.0 — API de People (métodos `form.*` com campos livres)
- `falai-rbac` — roles, níveis e identificação
- `falai-analise-candidatos` — análise de candidatos do InHire

## Referências de apoio
- `references/lancamento-ciclo-dm-lideres.md` — fluxo completo de DM em massa para lançamento de ciclo de avaliação
- `references/dm-templates-avaliacao.md` — ⭐ templates de DM para liderança e autoavaliação (CHA, deadlines, menções)
- `references/pitfalls-lancamento-ciclo.md` — ⛔ pitfalls críticos: fuzzy matching, DM overwrite, auditoria de links, menções
- `references/avaliacao-ordem-unificada.md` — ⭐ ordem canônica de perguntas: autoavaliação e liderança alinhadas (1=Resultados, 2=Área, 3=Competências, 4=Autonomia, 5=Potencial, 6=V+, 7=V-, 8=PDI/Recomendação)
- `references/email-override-map.md` — mapa de overrides email→nome para `gerar_form_avaliacao.py` (evita colisões de fuzzy matching)
- `references/dm-lideres-roteamento.md` — ⛔ pitfall: NUNCA rotear alterações para o bot; sempre para People
- `references/encontrar-lider.md` — ⚠️ `access.verify` não retorna supervisor; como descobrir o líder de alguém
- `references/avaliacao-lista-lideres.md` — extrair líderes×liderados dos JSONs do Convenia *e corrigir lista quando líder contesta*
- `references/avaliacao-lista-lideres.md` — extrair líderes×liderados dos JSONs do Convenia **e corrigir lista quando líder contesta**
- `references/form-submit-pattern.md` — padrão de submit (URL, auth, CORS) dos formulários
- `references/form-generators-catalog.md` — catálogo dos scripts geradores de HTML
- `references/jira-bug-template.md` — template de Bug Jira PAIX para erros da API
- `references/pulse-report-delivery-v2.md` — ⛔ regra de ouro para entrega de dados Pulse + deleção de DMs (v2 com correções de 01/09/2026)
- `references/pulse-lideres-dm-v2.md` — ⛔ engajamento de líderes via DM: pitfalls, template, fluxo completo (v2 com correções de 01/09/2026)
- `references/formularios-json-exemplos.md` — modelos de JSON (pulse, autoavaliação, avaliação líder)
- `references/valores-condoconta.md` — ⚠️ valores CondoConta: não existe lista oficial no Confluence; o que fazer quando perguntarem