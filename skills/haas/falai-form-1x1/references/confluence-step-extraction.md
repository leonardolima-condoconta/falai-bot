# Extração de Steps do Confluence para os JSONs

## Fluxo completo

1. **Buscar página índice** (`2613280770` — Plano de Cargos e Salários 2026)
   - Extrai links `<ri:page>` → 38 páginas de cargo (Analista Financeiro, Dev Backend, etc.)

2. **Fetch de cada página** → extrair tabelas `<tr>` com steps
   - Passo: `JI`, `JII`, `JIII`, `JIV`, `JV`, `PI`, ..., `SV`
   - Descrição: 5 dimensões (Entrega, Competência, Autonomia, Comportamento, Avança quando)

3. **Mapear cargo JSON → página Confluence**
   - Função `map_cargo()`: normaliza acentos, faz lookup em dict
   - Ex: "Analista de Endomarketing" → "Analista de Endomarketing" (page id `2580414488`)

4. **Cargos de liderança sem senioridade** (18 pessoas)
   - Inferir nível implícito: Head/Gerente/Manager/Lead → Sênior SV; Coordenador → Pleno PV
   - Fetch do step correspondente da página Confluence

5. **Salvar nos JSONs**
   - Campo `step_atual` com a descrição completa
   - `autoavaliacao_perguntas.json` e `avaliacao_lider_perguntas.json`

## Código de referência

```python
# Mapeamento de cargo
def map_cargo(jc):
    c = ''.join(ch for ch in unicodedata.normalize('NFD', jc.lower()) 
                if unicodedata.category(ch) != 'Mn')
    mapping = {
        "analista administrativo": "Analista Administrativo",
        "desenvolvedor backend": "Dev Backend",
        "head ai expert": "Head AI Expert",
        # ... 60 mapeamentos
    }
    for k, v in mapping.items():
        if c == k: return v

# Fetch Confluence page
def fetch_page(pid):
    r = subprocess.run(["curl","-s","-u",f"{email}:{token}",
        f"https://{domain}/wiki/rest/api/content/{pid}?expand=body.storage"
    ], capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout)
```

## Resultado

- 38 cargos mapeados, 555 steps extraídos
- 111/111 colaboradores com `step_atual` no JSON do líder
- 111/122 na autoavaliação (11 não encontrados no CSV)