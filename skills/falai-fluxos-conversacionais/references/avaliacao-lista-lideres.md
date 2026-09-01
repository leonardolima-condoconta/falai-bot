# Lista de Líderes e Liderados — Ciclo de Avaliação

## Quando usar

Quando o time de People (nível 3+) pedir para montar a lista de líderes e seus liderados
para envio de links de avaliação (autoavaliação + avaliação pelo líder).

## Fonte dos dados

Há **duas fontes** com propósitos diferentes:

### 1. Convenia API — mapeamento líder→liderados (FONTE PRIMÁRIA ✅)

A API Convenia (`/api/v3/employees`) é a **fonte autoritativa e mais eficiente** para
construir o mapeamento completo de líderes e liderados. Use-a SEMPRE em primeiro lugar.

**Vantagens sobre os JSONs:**
- Retorna **todos os 123 colaboradores** com supervisor em uma única chamada
- Cada registro inclui **email** (ausente nos JSONs)
- O campo `supervisor` é preenchido pelo RH no Convenia — é a verdade cadastral
- Sem fuzzy match de nomes, sem nomes truncados

**Exemplo de extração (Python, de dentro de `/opt/data/convenia/`):**

```python
import sys, os
os.chdir('/opt/data/convenia')
sys.path.insert(0, '/opt/data')
from convenia import ConveniaClient

with ConveniaClient() as client:
    resp = client._client.get("/api/v3/employees", params={"per_page": 200})
    employees = resp.json()["data"]

leaders = {}
for emp in employees:
    sup = emp.get("supervisor", {}) or {}
    sup_id = sup.get("id")
    if not sup_id:
        continue  # sem supervisor definido — tratar separadamente
    sup_name = f"{sup.get('name', '')} {sup.get('last_name', '')}".strip()
    if sup_id not in leaders:
        leaders[sup_id] = {"name": sup_name, "reports": []}
    leaders[sup_id]["reports"].append({
        "name": f"{emp.get('name', '')} {emp.get('last_name', '')}".strip(),
        "email": emp.get("email"),
        "job": emp.get("job", {}).get("name", ""),
        "department": emp.get("department", {}).get("name", ""),
    })
```

⚠️ Executar de `/opt/data/convenia/` (`.env` isolado). `PYTHONPATH` aponta para `/opt/data`.

### 2. JSONs do Convenia — perguntas de avaliação (FONTE SECUNDÁRIA)

Os JSONs contêm as perguntas específicas por colaborador, que a API Convenia não tem:

| Arquivo | Conteúdo |
|---|---|
| `/opt/data/convenia/autoavaliacao_perguntas.json` | 122 colaboradores com perguntas de autoavaliação |
| `/opt/data/convenia/avaliacao_lider_perguntas.json` | 121 colaboradores com perguntas de avaliação pelo líder |

⚠️ **Diferença crítica entre os JSONs:**
- `autoavaliacao_perguntas.json`: campo `gestor` é `None` para todos (autoavaliação é individual)
- `avaliacao_lider_perguntas.json`: campo `gestor` contém o nome do líder
- **Nenhum dos dois tem campo `email`** — use a API Convenia para cruzar nomes com emails

## Como extrair o mapeamento líder → liderados

### Método preferido: API Convenia (recomendado)

Use o código Python da seção "Fonte dos dados → Convenia API" acima. Ele retorna
em uma única chamada todos os líderes com seus liderados, incluindo emails.

### Método alternativo: JSON `avaliacao_lider_perguntas.json` (fallback)

Use apenas se a API Convenia estiver indisponível. Não tem emails — só nomes.

```python
from collections import defaultdict
leader_reports = defaultdict(list)
for area in data['areas']:
    for colab in area['colaboradores']:
        gestor = colab.get('gestor', '').strip()
        if gestor:
            leader_reports[gestor].append({
                'nome': colab['nome'], 'cargo': colab['cargo'],
                'area': area['area'], 'nivel': colab.get('nivel', '')
            })
sorted_leaders = sorted(leader_reports.items(), key=lambda x: len(x[1]), reverse=True)
```

## Geração do relatório HTML consolidado

Quando o time de People pedir "o relatório de líderes e liderados com links de avaliação",
gerar um HTML único no padrão CondoConta Design System com:

1. **Header** padrão (logo, tag confidencial, título, subtítulo com ciclo e data)
2. **Barra de KPIs** (total líderes, total liderados, com e-mail, sem e-mail)
3. **Bloco por líder** — tabela com nome, cargo, área, e-mail e link do formulário
4. **Seção de alerta** para colaboradores sem supervisor definido
5. **Footer** padrão

**URL dos formulários:** `https://static-server.aiexpert-condoconta.info/avaliacao-{slug}.html`
onde `slug` = nome em lowercase, espaços→hífens, só `[a-z0-9\-]`, truncado em 40 chars.

**Template base:** usar `condoconta-design-system` (tema claro, `.sheet` 860px, cores padrão).
Para relatórios com tabelas densas, aumentar `max-width` para 1100px.

Exemplo de slug: `"André Romão de Oliveira"` → `"andre-romao-de-oliveira"`

⚠️ **Os formulários HTML precisam ser gerados e publicados ANTES** de o relatório fazer
sentido. O link no relatório é só o destino — se o HTML não existir no static server,
o link vai dar 404.

## Geração dos formulários HTML individuais

Dois scripts geram formulários e publicam no static server:

| Script | Para quem | Comando |
|---|---|---|
| `gerar_form_avaliacao.py` | Autoavaliação individual | `python3 gerar_form_avaliacao.py <email>` |
| `gerar_form_lider.py` | Avaliação de liderados | `python3 gerar_form_lider.py <email>` |

Os scripts fazem fuzzy match do email com os nomes nos JSONs.

⚠️ O container **não alcança** a URL direta `condopower-api.aiexpert-condoconta.info`.
Use sempre o webhook-proxy para chamadas server-side:
`https://webhook-proxy.condoconta.com.br/webhooks/condopower-api`
com headers `X-Service-Account-Token` + `auth` (do `.env`).

## Quem recebe o quê

| Pessoa | Autoavaliação | Avaliação de liderados |
|---|---|---|
| Colaborador sem liderados | ✅ | ❌ |
| Líder com liderados | ✅ | ✅ (formulário de líder) |
| Líder que também é liderado | ✅ (auto) | ✅ (avalia seus liderados) |

## Correção de lista contestada por líder

**Contexto:** após o envio das DMs com a lista de liderados, um líder pode responder
contestando quem está ou não está na lista (ex: "Fulano não está no meu time, deveria
constar Ciclano").

### Fluxo de correção

1. **Identificar o líder** — usar `access.verify` com o Slack ID do remetente.
   A resposta traz `employee` e `reports[]` — **esta é a fonte autoritativa**.

2. **Comparar `reports[]` × `avaliacao_lider_perguntas.json`:**
   - Para cada `reports[]` do `access.verify`, verificar se o `gestor` no JSON bate.
   - Se o JSON discorda do `access.verify`, o JSON está errado.

3. **Corrigir o JSON** — editar `avaliacao_lider_perguntas.json`:
   ```python
   for area in data['areas']:
       for colab in area['colaboradores']:
           if colab['nome'] == 'Nome da Pessoa':
               colab['gestor'] = 'Nome Correto do Gestor'
   ```
   - Remover liderados que não pertencem ao gestor (mover `gestor` para o gestor correto)
   - Adicionar liderados que estão faltando (ajustar `gestor` do antigo para o novo)

4. **Confirmar as mudanças** — listar o antes/depois para o líder.

5. **Regenerar formulário** (se necessário) — rodar `gerar_form_lider.py` com o email do líder
   para gerar um HTML com a lista corrigida.

### Exemplo real (28/08/2026)

Humberto Basso contestou: Michelle Pacheco Soares não era liderada dele; Vitória Melo sim.

| Ação | `access.verify` (autoritativo) | JSON (antes) |
|---|---|---|
| Humberto → Bruno Mattos | ✅ | ✅ |
| Humberto → Vitória Melo | ✅ | ❌ (estava com Ayrton) |
| Humberto → Willian Soares | ✅ | ❌ (estava com Bruno V.) |
| Humberto → Michelle Pacheco | ❌ | ✅ (estava com Humberto) |

Correção aplicada no JSON: Vitória e Willian → Humberto; Michelle → Bruno Veronese.

## Liderados Indiretos — Org Chain Tracing

Quando um líder contesta alguém que **não está** em `reports[]`, a pessoa pode ser liderado indireto (2 níveis abaixo). Nesse caso, NÃO editar o JSON — a atribuição está correta, o líder simplesmente não deveria avaliar essa pessoa.

### Fluxo de tracing

1. Para cada `report` do líder, chamar `access.verify` com o email e inspecionar os `reports[]` dele
2. Se a pessoa contestada aparecer lá → é **liderado indireto**
3. Explicar ao líder: "X é liderado de Y, que reporta a você. A avaliação de liderança é da gestora direta."
4. Se o líder delegar ("te vira") → **notificar People**, não editar JSON
5. Se o sistema está pedindo para o líder errado avaliar → problema no JSON do Convenia ou no ciclo

### Exemplo real (28/08/2026)

Luciano Bernardi (CFO) contestou Vitor Pacheco. Vitor NÃO estava em `reports[]` do Luciano.
Tracing: Renata Paim (report do Luciano) → `reports[]` contém Vitor Pacheco.
→ Vitor é liderado indireto (Luciano → Renata → Vitor).
→ Ação: Falai notificou #people-hr + Catarcione para ajustar a atribuição no ciclo.

### "Te vira" — delegação sênior

Quando um líder C-level/VP/diretor diz "te vira", "resolve aí" ou "se vira", ele está delegando ação autônoma. NÃO pedir permissão adicional. Ação imediata:
- Postar no #people-hr (C0BJLA3H16F) com detalhes completos
- DM para Catarcione (U0AFGRGC80P)
- Confirmar ao líder que a notificação foi feita

## Pitfalls

- **API Convenia > JSONs para mapeamento.** O JSON `avaliacao_lider_perguntas.json` não tem
  emails, tem nomes truncados, e pode divergir do cadastro real. Use a API Convenia como
  fonte primária e o JSON apenas para as perguntas de avaliação.
- **Colaboradores sem email no Convenia.** ~4 dos 123 colaboradores não têm email cadastrado.
  Para esses, não é possível gerar link de formulário — exibir "sem e-mail" no relatório.
- **Colaboradores sem supervisor.** ~2 colaboradores não têm `supervisor` definido no
  Convenia. Listá-los em seção separada no relatório para o time de People revisar.
- **Nomes truncados** nos JSONs (ex: "Eduardo Victor Nóbrega Ferna" em vez de "Fernandes").
  O fuzzy match do script lida com isso, mas a API Convenia elimina o problema.
- **Gestores que também são liderados** (ex: Ayrton, Gianluca, Joanna Rosa, Renata Otacilio,
  Mateus Medeiros, Victor Oliveira, Leonardo Perin) — precisam dos DOIS tipos de link.
- **Slug de URL = nome lowercase com hífens.** Se o formulário foi gerado com um nome e
  depois o nome foi corrigido no cadastro, o link quebra. Conferir o slug gerado vs. o
  arquivo publicado no static server.