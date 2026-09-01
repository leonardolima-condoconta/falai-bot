# Extração de Steps do Confluence CDAP

Workflow para mapear descrições de step (JI-JV, PI-PV, SI-SV) do Confluence
para cada colaborador nos JSONs de avaliação.

## Estrutura do Confluence

Space: `CDAP` (Plano de Cargos e Salários 2026)
Página índice: ID `2613280770`
Cada cargo tem uma página própria com tabela de steps (15 linhas: JI a SV).

Colunas da tabela:
| Step | Descrição (5 dimensões) |
|---|---|

Dimensões: Entrega, Competência, Autonomia, Comportamento, Avança quando.

## Passo 1 — Buscar IDs das páginas

```bash
curl -s -u "email:token" \
  "https://condoconta.atlassian.net/wiki/rest/api/search?cql=text~'Step+I+Entrega'+AND+space='CDAP'+AND+type=page&limit=50"
```

Extrai `results[].content.id` e `results[].content.title`.

## Passo 2 — Fetch cada página

```bash
curl -s -u "email:token" \
  "https://condoconta.atlassian.net/wiki/rest/api/content/{page_id}?expand=body.storage"
```

## Passo 3 — Parse tabelas

```python
import re, json
body = data["body"]["storage"]["value"]
rows = re.findall(r'<tr>(.*?)</tr>', body, re.DOTALL)
for row in rows:
    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
    if len(cells) >= 2:
        step_code = clean_html(cells[0]).strip()
        desc = clean_html(cells[1]).strip()
        if re.match(r'^[JPS]I{0,3}V?$', step_code):
            steps[step_code] = desc
```

`clean_html()` remove tags e decodifica HTML entities (í, ç, ã, etc.).

## Passo 4 — Mapear cargos JSON → Confluence

60 cargos no JSON do Convenia → 38 páginas Confluence. Mapeamento:

| JSON cargo | Confluence page |
|---|---|
| Analista de Cobrança / Collection Specialist | Analista Cobrança |
| Analista de Dados | Analista de MIS |
| Analista de Qualidade / Analista de Suporte | Analista Suporte |
| Analista de Relacionamento / Executivo de Negócios / SDR | Analista Relac. |
| Analista de Service Desk / Analista de Suporte Técnico | Analista Service Desk |
| Analista de Tesouraria (Jr/Pleno) | Analista Tesouraria |
| Analista de Crédito / Crédito e Risco | Analista Crédito/Risco |
| Analista de FP&A / Financial Specialist | Analista FP&A |
| Analista Financeiro | Analista Financeiro |
| Analista Administrativo / Assistente Administrativo | Analista Administrativo |
| Analista Jurídico | Analista Jurídico |
| Analista de Marketing | Analista Marketing |
| Analista de Endomarketing | Analista de Endomarketing |
| Analista AI Expert / AI Expert Analyst | Analista AI Expert |
| Assistente de Cobrança | Assist. Cobrança |
| Assistente Jurídico | Assist. Jurídico |
| Assistente de Vendas / Assist. Implantação | Assist. Implantação |
| Backend Lead | Backend Lead |
| Business Partner / HRBP | Business Partner (HRBP) |
| Cientista de Dados | Cientista de Dados |
| Controller Jurídico | Controller Jurídico |
| Coordenador de Controladoria | Coord. Controladoria |
| Coordenador de Cobrança / Coord. Legal Ops / Collection Coordinator | Coord. Cobrança |
| Coordenador de Sales / CS & CX Manager | Coord. Relac. |
| Coord. Suporte / Customer Experience Coordinator | Coord. Suporte |
| Coord. de Implantação / Coord. Onboarding | Coord. Onboarding |
| Desenvolvedor Backend / DevOPS / Software | Dev Backend |
| Desenvolvedor Front-End | Dev Front-End |
| Desenvolvedor Mobile | Dev Mobile |
| Engenheiro de Dados / Líder de Dados | Eng. de Dados |
| Gerente de Cobrança | Gerente Cobrança |
| Gerente de Growth / Head de Sales / Sales Manager | Gerente Growth |
| Gerente Tesouraria / Head of Finance | Gerente Tesouraria |
| Head AI Expert / Tech Lead AI Expert | Head AI Expert |
| Product Designer | Product Designer |
| Product Manager / Product Marketing Manager | Product Manager |
| GPM / Group Product Manager | GPM (Group Product Manager) |
| Registration Analyst / CS Onboarding Analyst | Analista Onboarding |

## Passo 5 — Determinar step code

A partir de `senioridade` + `nivel_senioridade`:

```python
prefix = {"junior": "J", "júnior": "J", "pleno": "P", "senior": "S", "sênior": "S"}
p = prefix.get(senioridade.lower().strip(), "")
n = nivel_sr.strip().upper()  # "I","II","III","IV","V" or "1"-"5"
sc = p + n  # Ex: "PIII"
```

Buscar `step_map[cargo_title][sc]` → descrição completa do step.

## Passo 6 — Salvar no JSON

Adicionar campo `step_atual` em cada colaborador do JSON:

```python
col["step_atual"] = step_map[cf][sc]  # ou "" se não encontrado
```

## Pitfalls

- 18 colaboradores (cargos de liderança) não tinham `senioridade`/`nivel_sr` no CSV → `step_atual` vazio
- Passos "I" a "V" sem prefixo (J/P/S) nos dados brutos precisam combinar com o nível
- HTML entities precisam ser decodificadas (í, ç, ã, õ, etc.)
- Alguns cargos do Convenia não têm correspondente exato no Confluence → usar mapeamento manual