# Renderização do step_atual no HTML de avaliação do líder

## Comportamento

- `step_atual` **NÃO aparece no dropdown** — só quando o liderado é selecionado
- Exibido como card azul (`var(--lider-bg)`) abaixo do label "Avaliando: Nome · Cargo · Pleno V"

## Código JavaScript no gerador

```javascript
var stepInfo = matchStepAtual(l.nome);
var html = '<div style="color:var(--muted);font-size:12px;margin-bottom:6px">'
  + 'Avaliando: <b>' + l.nome + '</b> · ' + l.cargo + srInfo + '</div>';
if(stepInfo){
  html += '<div style="background:var(--lider-bg);'
    + 'border:1px solid var(--lider-border);'
    + 'border-radius:6px;padding:10px 12px;margin-bottom:18px;'
    + 'font-size:11px;color:var(--navy);line-height:1.5">'
    + '<span style="font-weight:700;font-size:10px;'
    + 'text-transform:uppercase;letter-spacing:.08em;'
    + 'color:var(--muted)">Step Atual</span><br>'
    + stepInfo + '</div>';
}
```

## Mapa embutido no HTML

O Python gera `STEP_ATUAL_MAP` a partir de `avaliacao_lider_perguntas.json`:

```python
step_atual_map = {}
for area in lider_json.get("areas", []):
    for col in area["colaboradores"]:
        nome = col["nome"]
        sat = col.get("step_atual","")
        if sat:
            step_atual_map[nome.lower()] = sat
            if nome.lower().split():
                step_atual_map[nome.lower().split()[0]] = sat
            key = strip_accents(nome.lower())
            step_atual_map[key] = sat
step_atual_json = json.dumps(step_atual_map, ensure_ascii=False)
```

O JS faz fuzzy match igual à `matchSenioridade()`: busca por nome completo, depois por primeiro nome, depois por chave sem acentos.

## Nível implícito para cargos de liderança (18 sem senioridade no CSV)

18 cargos (Coordenador, Head, Gerente, Manager, Lead) não têm `senioridade` nem `nivel_senioridade`
no CSV do Convenia. Inferência por natureza do cargo:

| Padrão no cargo | Step inferido |
|---|---|
| Head, Gerente, Manager, Lead, Diretor | SV (Sênior V) |
| Coordenador, Coordinator | PV (Pleno V) |
| Analista, Developer, Analyst | PIII (Pleno III — fallback) |

```python
def infer_step(cargo):
    cargo_l = cargo.lower()
    if any(kw in cargo_l for kw in ["head","gerente","manager","lead"]):
        return "SV"
    if any(kw in cargo_l for kw in ["coordenador","coord"]):
        return "PV"
    return "PIII"
```

Combina com `map_cargo()` para obter a página Confluence correta, então busca `step_map[cargo_title][sc]`.