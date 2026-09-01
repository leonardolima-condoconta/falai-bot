# Extração de Steps do Confluence para cargos CondoConta

## Fonte
- Página índice: https://condoconta.atlassian.net/wiki/spaces/CDAP/pages/2613280770
- 38 páginas filhas, uma por cargo
- Cada página tem 3 tabelas (Júnior JI-JV, Pleno PI-PV, Sênior SI-SV)
- 15 steps por cargo × 38 cargos = 555 steps extraídos

## Extração da tabela HTML do Confluence

```python
import re, json, subprocess

r = subprocess.run(["curl","-s","-u",f"{email}:{token}",
    f"https://{domain}/wiki/rest/api/content/{pid}?expand=body.storage"
], capture_output=True, text=True)

data = json.loads(r.stdout)
body = data["body"]["storage"]["value"]
rows = re.findall(r'<tr>(.*?)</tr>', body, re.DOTALL)

for row in rows:
    cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
    if len(cells) >= 2:
        step_code = decode_entities(cells[0]).strip()  # JI, JII, ..., SV
        desc = decode_entities(cells[1]).strip()
        if re.match(r'^[JPS]I{0,3}V?$', step_code):
            steps[step_code] = desc
```

## Decodificação de entidades HTML

```python
for e, c in [('&iacute;','í'),('&atilde;','ã'),('&ccedil;','ç'),('&oacute;','ó'),
              ('&Iacute;','Í'),('&uacute;','ú'),('&eacute;','é'),('&acirc;','â'),
              ('&ecirc;','ê'),('&otilde;','õ'),('&ntilde;','ñ'),('&aacute;','á'),
              ('&Acirc;','Â'),('&Ecirc;','Ê'),('&Ccedil;','Ç')]:
    text = text.replace(e, c)
```

## Mapeamento cargo JSON → página Confluence (60 entradas)

```python
def map_cargo(jc):
    c = normalizar_sem_acentos(jc.lower())
    mapping = {
        "analista administrativo": "Analista Administrativo",
        "analista juridico": "Analista Jurídico",
        "analista de cobranca": "Analista Cobrança",
        "analista de credito": "Analista Crédito/Risco",
        "analista de credito e risco": "Analista Crédito/Risco",
        "analista de dados": "Analista de MIS",
        "analista de endomarketing": "Analista de Endomarketing",
        "analista de fp&a": "Analista FP&A",
        "analista de marketing": "Analista Marketing",
        "analista de qualidade": "Analista Suporte",
        "analista de relacionamento": "Analista Relac.",
        "analista de service desk": "Analista Service Desk",
        "analista de sucesso do parceiro": "Analista Relac.",
        "analista de suporte": "Analista Suporte",
        "analista de suporte tecnico": "Analista Service Desk",
        "analista de tesouraria": "Analista Tesouraria",
        "analista de tesouraria junior": "Analista Tesouraria",
        "analista de tesouraria pleno": "Analista Tesouraria",
        "assistente administrativo": "Analista Administrativo",
        "assistente juridico": "Assist. Jurídico",
        "assistente de cobranca": "Assist. Cobrança",
        "assistente de vendas": "Analista Relac.",
        "backend lead": "Backend Lead",
        "business partner": "Business Partner (HRBP)",
        "cs & cx manager": "Coord. Relac.",
        "cs onboarding analyst": "Analista Onboarding",
        "cientista de dados": "Cientista de Dados",
        "collection coordinator": "Coord. Cobrança",
        "collection specialist": "Analista Cobrança",
        "controller juridico": "Controller Jurídico",
        "coordenador de controladoria": "Coord. Controladoria",
        "coordenador de legal ops": "Coord. Cobrança",
        "coordenador de sales": "Coord. Relac.",
        "coordenadora de implatacao": "Coord. Onboarding",
        "customer experience coordinator": "Coord. Suporte",
        "desenvolvedor": "Dev Backend",
        "desenvolvedor backend": "Dev Backend",
        "desenvolvedor front-end": "Dev Front-End",
        "desenvolvedor mobile": "Dev Mobile",
        "desenvolvedor de software": "Dev Backend",
        "engenheiro devops": "Dev Backend",
        "engenheiro de dados": "Eng. de Dados",
        "executivo de banking pleno": "Analista Relac.",
        "executivo(a) de negocios": "Analista Relac.",
        "financial specialist": "Analista Financeiro",
        "gerente de cobranca": "Gerente Cobrança",
        "gerente de growth marketing": "Gerente Growth",
        "head ai expert": "Head AI Expert",
        "head de sales": "Gerente Growth",
        "head of finance & credito": "Gerente Tesouraria",
        "lider de dados": "Eng. de Dados",
        "product designer": "Product Designer",
        "product manager": "Product Manager",
        "product marketing manager": "Product Manager",
        "registration analyst": "Analista Onboarding",
        "sdr": "Analista Relac.",
        "sales manager": "Gerente Growth",
        "tech lead ai expert": "Head AI Expert",
        "treasury manager": "Gerente Tesouraria",
        "ai expert analyst": "Analista AI Expert",
    }
    for k, v in mapping.items():
        if c == k or c in k or k in c:
            return v
    return None
```

## Step code → senioridade + nível

```python
def get_step_code(senioridade, nivel_sr):
    if not senioridade or not nivel_sr:
        return None
    prefix = {"junior": "J", "júnior": "J", "pleno": "P", "senior": "S", "sênior": "S"}
    p = prefix.get(senioridade.lower().strip(), "")
    n = nivel_sr.strip().upper()
    if n in ("1",): n = "I"
    if n in ("2",): n = "II"
    if n in ("3",): n = "III"
    if n in ("4",): n = "IV"
    if n in ("5",): n = "V"
    return p + n
```

## Inferência para cargos sem senioridade

18 cargos de liderança (Head, Coordenador, Gerente, Manager, Lead) não têm `senioridade` nem `nivel_senioridade` no CSV do Convenia.

```python
def infer_step(cargo):
    cargo_l = cargo.lower()
    if "head" in cargo_l or "gerente" in cargo_l or "manager" in cargo_l or "lead" in cargo_l:
        return "SV"
    if "coordenador" in cargo_l or "coord" in cargo_l:
        return "PV"
    return "PIII"
```

## Aplicação no JSON

```python
for col in colaboradores:
    cf = map_cargo(col["cargo"])
    sc = get_step_code(col["senioridade"], col["nivel_senioridade"]) or infer_step(col["cargo"])
    if cf and sc and confluence_steps.get(cf, {}).get(sc):
        col["step_atual"] = confluence_steps[cf][sc]
```

Output:
```json
{"nome":"Rodrigo Silva da Luz","cargo":"Tech Lead AI Expert",
 "step_atual":"Entrega: define a visão técnica de IA da empresa. Competência: ..."}
```

## Resultado (31/08/2026)
- 38 páginas fetched, 555 steps extraídos
- 111/111 colaboradores com `step_atual` no JSON de líder
- 111/122 com `step_atual` no JSON de autoavaliação

## Pitfalls
- "Assist. Implantação" tem 0 steps (tabela vazia) — cargo sem trilha publicada
- `step_code` regex: `^[JPS]I{0,3}V?$` captura JI a SV
- Páginas têm 3 tabelas (Júnior, Pleno, Sênior), cada uma com header + 5 step rows
- Autenticação: mesma do Jira (`condoconta.atlassian.net` com `JIRA_EMAIL` + `JIRA_API_TOKEN`)
- A página índice (id=2613280770) lista 37 cargos — útil para descobrir novos