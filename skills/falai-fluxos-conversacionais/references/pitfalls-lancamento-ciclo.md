# Pitfalls do Lançamento de Ciclo de Avaliação

Registro de todos os problemas encontrados no lançamento 2026.2 (31/08/2026) e suas soluções permanentes.

---

## 1. Fuzzy Matching Trocando Links de Autoavaliação (CRÍTICO)

### Sintoma
Colaboradores recebem link de autoavaliação com o nome de outra pessoa no slug. Ex: `joao.carvalho@condoconta.com.br` recebe `avaliacao-raphael-de-carvalho-cortes`.

### Causa raiz
`gerar_form_avaliacao.py` usa fuzzy matching: quebra o e-mail em partes (`joao`, `carvalho`) e procura nos nomes do JSON de autoavaliação. Os nomes no JSON são **truncados a ~31 caracteres** (ex: "João Guilherme Teixeira Brag" em vez de "João Guilherme Teixeira Braga Carvalho"). Quando duas pessoas compartilham partes do nome, o primeiro no JSON ganha.

### Correção permanente
1. **Arquivo `email_override_map.json`** em `/opt/data/convenia/` — mapa de email → nome exato no JSON:
```json
{
  "vanessa.silva@condoconta.com.br": "Vanessa da Silva",
  "joao.carvalho@condoconta.com.br": "João Guilherme Teixeira Brag",
  ...
}
```

2. **Script `gerar_form_avaliacao.py`** foi patchado com dupla prioridade:
   - **Prioridade 1:** Se o email está no override map → match exato pelo nome do override (usa prefix matching pois nomes são truncados)
   - **Prioridade 2:** Fuzzy matching original

### Lista completa de overrides (9 entradas em 31/08/2026)
| Email | Nome no JSON |
|---|---|
| vanessa.silva@ | Vanessa da Silva |
| vitoria.sousa@ | Vitória Kimberllan Carvalho Lemos de Sousa |
| caua.lima@ | Cauã Daniel Lima da Silva |
| leticia.santos@ | Letícia Francisco dos Santos |
| juliana.simoes@ | Juliana Xavier Simões |
| danielly.costa@ | Danielly Maire Oliveira da Costa |
| solange.pereira@ | Solange Gonçalves da Costa Pereira |
| joao.carvalho@ | João Guilherme Teixeira Brag |
| caju@ | Paulo Fernando da Costa Pere |

### Como adicionar novas entradas
Editar `/opt/data/convenia/email_override_map.json` e adicionar o par email:nome. O nome DEVE ser exatamente como aparece no JSON de autoavaliação (incluindo truncamento).

---

## 2. DMs Sobrescritas por Edições Posteriores (CRÍTICO)

### Sintoma
Após corrigir links nas DMs e confirmar visualmente, uma edição posterior (ex: mudar prazo de 1→4 dias) regravou as DMs com JSON antigo que continha os links errados, desfazendo todas as correções.

### Causa raiz
O fluxo de edição em massa carregava o JSON de mensagens do disco (`mensagens_autoavaliacao_2026.2.json`), mas esse JSON **não havia sido atualizado** com os links corrigidos (as correções foram feitas direto nas DMs via `chat.update`, sem persistir no JSON).

### Correção permanente
**SEMPRE** seguir esta ordem ao editar DMs em massa:
1. Atualizar o JSON fonte com as correções
2. Regravar o JSON no disco
3. Só então disparar `chat.update` para todas as DMs a partir do JSON atualizado

NUNCA fazer `chat.update` com dados parciais ou de memória — sempre ler do JSON que é a fonte da verdade.

---

## 3. Auditoria de Links Pós-Envio (OBRIGATÓRIO)

### Procedimento
Após QUALQUER envio ou edição de DMs com links de formulários, executar auditoria completa:

```python
# Para cada DM enviada:
# 1. Ler a DM real do Slack via conversations.history
# 2. Extrair o slug da URL do static-server
# 3. Verificar se partes do nome da pessoa aparecem no slug
# Mínimo: 2 partes do nome com >= 4 caracteres devem estar no slug
```

### Gatilhos que exigem re-auditoria
- Qualquer `chat.update` em massa
- Mudança de prazo ou template
- Adição de novas pessoas ao override map
- Report de link errado por qualquer colaborador

---

## 4. Slug do `gerar_form_lider.py` = Prefixo do Email

O script `gerar_form_lider.py` (linha 336) usa:
```python
slug = "avaliacao-lider-" + EMAIL.lower().split("@")[0].replace(".", "-")[:50]
```

Ex: `rodrigo.catarcione@condoconta.com.br` → `avaliacao-lider-rodrigo-catarcione`

⚠️ NUNCA tentar adivinhar o slug a partir do nome — sempre usar o prefixo do e-mail.

---

## 5. Executivos C-Level Fora do JSON de Autoavaliação

### Sintoma
Líderes que também são liderados (ex: C-level reportando ao CEO) podem não constar no JSON de autoavaliação padrão.

### Solução
- Verificar se todos os líderes receberam autoavaliação (cruzar `relatorio_lideres.json` × `resultado_envio_autoavaliacao.json`)
- Para os faltantes: solicitar as planilhas Excel individuais (arquivos `.xlsx` com abas por executivo)
- Extrair perguntas diretamente do XML do Excel (zipfile + ElementTree, colunas B=pergunta, D=tipo)
- Gerar formulários HTML com template CondoConta (mesmo CSS/JS dos outros formulários)
- Publicar via webhook-proxy → static-server

### Executivos que precisaram de formulários manuais (31/08/2026)
Marcelo Cruz, Luciano Bernardi, Rodrigo Costa, Rodrigo Borer, Rodrigo Catarcione, Rodolfo Pinotti (avaliação de liderança pelo CEO).

---

## 6. Menção no Slack — Sintaxe Correta

- ✅ `<@U0AS4CSDUUU>` — vira menção clicável
- ❌ `@U0AS4CSDUUU` — texto puro, não notifica
- ❌ `<@U0AS4CSDUUU> Beatrís Xavier` — a menção já mostra o nome, o texto extra fica redundante