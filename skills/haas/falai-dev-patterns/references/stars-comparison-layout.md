# 1x1 Stars Comparison Layout

O `gerar_form_1x1.py` exibe o comparativo 🟡 auto × 🔵 líder usando `div.stars` (mesmo padrão
visual dos formulários de autoavaliação e avaliação do líder), NÃO colunas `row/cell`.

## Estrutura HTML

```html
<div class="cmp-section">
  <div class="cmp-label">1. Resultados</div>
  <div class="stars">
    <button class="" data-value="1" onclick="toggleStar(this,1)">1</button>
    <button class="sel-lider" data-value="2" onclick="toggleStar(this,2)">2</button>
    <button class="sel-auto" data-value="3" onclick="toggleStar(this,3)">3</button>
    <button class="mixed" data-value="4" onclick="toggleStar(this,4)">4</button>
    <button class="" data-value="5" onclick="toggleStar(this,5)">5</button>
  </div>
  <div class="resp auto-resp">Texto da autoavaliação</div>
  <div class="resp lider-resp">Texto do líder</div>
</div>
```

## Classes CSS

| Classe | Significado |
|---|---|
| `.sel-auto` | Só autoavaliação assinalou esse valor (fundo amarelo `var(--auto-bg)`) |
| `.sel-lider` | Só o líder assinalou esse valor (fundo azul `var(--lider-bg)`) |
| `.mixed` | Ambos assinalaram o mesmo valor — gradiente diagonal 135° amarelo/azul |
| `.resp.auto-resp` | Texto da autoavaliação (respostas não-numéricas) |
| `.resp.lider-resp` | Texto do líder (respostas não-numéricas) |

## CSS essencial

```css
.stars{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.stars button{width:44px;height:44px;border-radius:8px;border:1.5px solid var(--line);background:#FBFCFE;font-size:15px;font-weight:600;cursor:pointer;color:var(--muted);transition:all .15s}
.stars button.sel-auto{background:var(--auto-bg);border-color:var(--auto-border);color:#8B6914;font-weight:700}
.stars button.sel-lider{background:var(--lider-bg);border-color:var(--lider-border);color:#14365C;font-weight:700}
.stars button.mixed{background:linear-gradient(135deg,var(--auto-bg) 0% 50%,var(--lider-bg) 50% 100%);border-color:var(--auto-border);border-right-color:var(--lider-border);border-bottom-color:var(--lider-border);color:#14365C;font-weight:800}
```

## Lógica Python

Apenas respostas numéricas (1-5) viram stars. Textos longos vão abaixo como `.resp`:

```python
def star_val(v):
    try: return int(float(str(v).strip().replace(",",".")))
    except: return None

n_auto = star_val(av)
n_lider = star_val(lv)

for s_val in range(1, 6):
    cls = ""
    if n_auto == s_val and n_lider == s_val:
        cls = " mixed"
    elif n_lider == s_val:
        cls = " sel-lider"
    elif n_auto == s_val:
        cls = " sel-auto"
```

## Pitfall: resposta "4.5" não é int

`int(float("4.5"))` funciona — o `float` converte 4.5, depois `int` trunca. Se a resposta for
texto puro ("Alto", "Bom"), `star_val` retorna None e o texto vai pra `.resp`.