# Fontes de Dados de People — Cargos, Salários, Plano de Carreira

Mapa de onde encontrar informações de People na CondoConta.

## Plano de Carreira & Descrições de Cargo → Confluence CDAP

**Espaço:** CDAP (Central de Ajuda People)
**URL:** https://condoconta.atlassian.net/wiki/spaces/CDAP
**Conteúdo:** 41 páginas, uma por cargo, com trilhas de senioridade completas.

Cada página contém:
- Trilha de senioridade (Júnior → Pleno → Sênior, steps I a V)
- Área funcional (ex: ENG. E DESENVOLVEDORES DE SOFTWARE, PEOPLE, DADOS AI)
- Expectativas, competências e critérios de avanço por step
- Fonte: *CondoConta — Plano de Carreira & Desenvolvimento 2026*

### Áreas mapeadas (38 cargos):
- ENG. E DESENVOLVEDORES DE SOFTWARE (5): Analista Service Desk, Backend Lead, Dev Backend, Dev Front-End, Dev Mobile
- DADOS AI (4): Analista AI Expert, Cientista de Dados, Eng. de Dados, Head AI Expert
- PRODUTO E DESIGN (3): GPM, Product Designer, Product Manager
- RELACIONAMENTO, SUPORTE E ONBOARDING (7): Analista Onboarding, Analista Relac., Analista Suporte, Assist. Onboarding, Coord. Onboarding, Coord. Relac., Coord. Suporte
- JURÍDICO E COBRANÇA (7): Analista Cobrança, Analista Jurídico, Assist. Cobrança, Assist. Jurídico, Controller Jurídico, Coord. Cobrança, Gerente Cobrança
- FINANCE (6): Analista Crédito/Risco, Analista Financeiro, Analista FP&A, Analista Tesouraria, Coord. Controladoria, Gerente Tesouraria
- PEOPLE (3): Analista Administrativo, Analista de Endomarketing, Business Partner (HRBP)
- MARKETING (2): Analista Marketing, Gerente Growth
- Outros: Analista de MIS

## Descrições de Vagas (JDs) → Confluence PT

**Espaço:** PT (People)
**URL:** https://condoconta.atlassian.net/wiki/spaces/PT
**Páginas-chave:**
- VAGAS (JDs): https://condoconta.atlassian.net/wiki/spaces/PT/pages/401768492
- 5.10 Descrições de Vagas: https://condoconta.atlassian.net/wiki/spaces/PT/pages/721682443

## Remuneração / Faixas Salariais → Google Drive

**NÃO estão no Confluence.** Os valores salariais (mínimo e máximo) ficam nas JDs armazenadas no Google Drive:

**Pasta:** https://drive.google.com/drive/folders/1ZCylbQekuaaf19VsmvCcDo-TZPqM_wRB

Cada JD contém: informações da vaga, remuneração mínima e máxima, perfil técnico e comportamental, percepções de People pós conversa com gestor.

## Fluxo para queries de "cargos e salários"

1. **Confluence CDAP** → estrutura de cargos, trilhas de senioridade, descrições de competências
2. **Google Drive** → faixas salariais, remuneração
3. **Confluence PT** → JDs template, processo de recrutamento, benefícios

## Pitfalls

- O termo "salário" não retorna resultados no Confluence — as faixas salariais estão exclusivamente no Drive
- O espaço CDAP não aparece em buscas por "People" — buscar por "cargos" ou pelo nome específico do cargo
- O script `confluence_search.py` retorna `[Errno 13] Permission denied` no container HaaS. **Não use curl** como fallback — o `JIRA_API_TOKEN` tem caracteres especiais (`{`, `}`, `!`, `$`) que o shell corrompe. Use **Python puro com `urllib`** (funciona direto do container, sem script):
  ```python
  import os, json, base64, urllib.request, urllib.parse, re
  env = {}
  with open('/opt/data/.env') as f:
      for line in f:
          line = line.strip()
          if '=' in line and not line.startswith('#'):
              k, v = line.split('=', 1); env[k] = v
  auth = base64.b64encode(f"{env['JIRA_EMAIL']}:{env['JIRA_API_TOKEN']}".encode()).decode()
  BASE = "https://condoconta.atlassian.net/wiki/rest/api"
  def get(path):
      req = urllib.request.Request(f"{BASE}/{path}", headers={"Authorization": f"Basic {auth}", "Accept": "application/json"})
      with urllib.request.urlopen(req) as r: return json.loads(r.read())
  # busca:  get("search?cql=" + urllib.parse.quote('space = "CDAP" AND text ~ "Crédito"') + "&limit=10")
  # página: get("content/{id}?expand=body.storage")
  ```
  Strip de HTML para leitura: `re.sub(r'<[^>]+>', ' ', v)` + replace de `&mdash;`, `&middot;`, `&nbsp;`, `&amp;`, `&lt;`, `&gt;`.
- A busca nativa do Confluence cobre TODOS os espaços, inclusive CDAP e PT, sem precisar declará-los

## Índice do Plano de Cargos e Salários 2026 (CDAP) — IDs mapeados

- Página-índice **"Plano de Cargos e Salários 2026"**: ID `2613280770`
- **"Status - Plano de Cargos e Salários"**: ID `2612953097`
- Pasta **FINANCE**: folder ID `2580348929` → Analista Tesouraria, Analista Crédito/Risco (`2579824643`), Analista FP&A, Analista Financeiro, Coord. Controladoria, Gerente Tesouraria
- Estrutura oficial: **8 áreas · 38 cargos · 37 trilhas publicadas** (página "Analista Suporte" está pendente)
- Cada página de cargo traz a trilha completa (Júnior/Pleno/Sênior × steps I–V) com 5 dimensões: Entrega, Competência, Autonomia, Comportamento e "Avança quando"

## ⚠️ RBAC — "cargos e salários" são duas metades distintas

- **Cargos / trilha de senioridade** (Confluence CDAP): aberto a TODOS os levels (1–5). Pode mostrar.
- **Salários / faixas de remuneração** (Google Drive): **NÃO** compartilhar com level < 3. Redirecionar para Catarcione (People) ou gestor direto.

## ⛔ Limite — salário INDIVIDUAL não é acessível (verificado 26/08/2026)

Quando o pedido for "quem ganha até X", "impacto de reajuste no piso", "média salarial por
área", "menor salário da empresa" etc., a resposta é uma **limitação de dados**, NÃO de
permissão do usuário. Não existe salário individual em NENHUMA fonte acessível à Falai:

- **Convenia (token `Falai-Bot`)**: `salary` vem `null` na lista (`/api/v3/employees`) E no
  detalhe (`/api/v3/employees/{id}`). Não há campo de remuneração exposto ao token.
- **condopower-api**: remuneração está FORA do escopo do serviço — não existe método de
  payroll/salário (só identidade, forms, clima, celebrações, roster).
- **SQLite local** (`convenia_data/backups/convenia_*.db`, tabela `employees`): NÃO tem
  coluna de salário. Colunas reais: `id, name, last_name, email, birth_date, hiring_date,
  department_id, cost_center_id, job_id, supervisor_id, is_active, synced_at, senioridade,
  nivel_senioridade, cellphone`.

Só existem **faixas** salariais (mín–máx) por cargo nas JDs do Google Drive — não salários
de folha. **Não prometa calcular piso, reajuste, média ou qualquer distribuição de salário
com as fontes atuais** — confirmado empiricamente nas três fontes acima.

**O que oferecer no lugar:**
1. Roster completo por área e cargo (headcount) — disponível no Convenia/SQLite.
2. Se o usuário apontar uma planilha/arquivo com os salários (Drive/arquivo), rodar a
   análise completa em cima dela (é a alternativa que destrava a conta).
3. Para ter salário individual via API, seria preciso um token Convenia com escopo de
   remuneração (o atual não tem) — escalar para Leonardo de Lima.