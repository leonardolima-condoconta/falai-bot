# Integração Confluence → step_atual

## Objetivo
Popular o campo `step_atual` nos JSONs `autoavaliacao_perguntas.json` e `avaliacao_lider_perguntas.json` com a descrição completa do step de carreira do Confluence, baseado na senioridade e nível de senioridade de cada colaborador.

## Fonte
Página índice: https://condoconta.atlassian.net/wiki/spaces/CDAP/pages/2613280770 (Plano de Cargos e Salários 2026)

Cada cargo tem uma página filha com tabelas de steps (JI-JV, PI-PV, SI-SV). Cada step descreve 5 dimensões: Entrega, Competência, Autonomia, Comportamento, Avança quando.

## Fluxo

### 1. Buscar páginas do Confluence
Usar a API REST do Confluence (mesma autenticação Jira):
```python
GET /wiki/rest/api/search?cql=text~'Step+I+Entrega'+AND+space='CDAP'+AND+type=page&limit=50
GET /wiki/rest/api/content/{page_id}?expand=body.storage
```

### 2. Extrair steps das tabelas
Cada tabela HTML tem linhas `<tr>` com `<td>`: step_code (JI, JII, ..., SV) + descrição completa.
Regex: `re.findall(r'<tr>(.*?)</tr>', body, re.DOTALL)` → para cada row, extrair `<t[dh][^>]*>(.*?)</t[dh]>`.

### 3. Mapear cargo JSON → página Confluence
Os nomes de cargo no JSON (ex: "Analista de Cobrança") não batem exatamente com os do Confluence ("Analista Cobrança"). Manter um dicionário de mapeamento fixo com ~60 entradas.

### 4. Converter senioridade + nivel → step code
| Senioridade | Prefixo |
|---|---|
| Junior / Júnior | J |
| Pleno | P |
| Senior / Sênior | S |

Nivel: I→I, II→II, III→III, IV→IV, V→V. Resultado: "JIII", "PV", "SI", etc.

### 5. Cargos sem senioridade no CSV
Para cargos de liderança/coordenação sem senioridade preenchida, inferir nível implícito:
- Head/Gerente/Manager/Lead → Sênior (SV)
- Coordenador → Pleno (PV)
- Analista/Desenvolvedor → Pleno (PIII)

### 6. Salvar nos JSONs
```python
col["step_atual"] = step_map[confluence_title][step_code]
```
Aplicar em ambos os JSONs. Usar nome.lower() como chave para matching.

## Q7/Q8 swap na autoavaliação
No `gerar_form_avaliacao.py`, as perguntas 7 e 8 são trocadas antes da renderização:
```python
perguntas_render = list(colaborador["perguntas"])
if len(perguntas_render) >= 8:
    perguntas_render[6], perguntas_render[7] = perguntas_render[7], perguntas_render[6]
    perguntas_render[6]["n"], perguntas_render[7]["n"] = perguntas_render[7]["n"], perguntas_render[6]["n"]
```
Isso garante que o `n` (número da pergunta) também é trocado, mantendo consistência no submit.

## step_atual no HTML do líder
No `gerar_form_lider.py`, o `step_atual` é carregado via `STEP_ATUAL_MAP` (JSON embutido) e exibido como card azul abaixo do nome do liderado ao selecionar no dropdown. Função `matchStepAtual(nome)` faz fuzzy match por primeiro nome e nome completo sem acentos.