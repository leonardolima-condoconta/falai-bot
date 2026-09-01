# Padrão div.stars com Dupla Cor no 1x1

O formulário 1x1 usa `div.stars` (mesmo componente visual da autoavaliação e
avaliação do líder), mas com um comportamento especial: quando auto e líder
concordam no mesmo número, o botão mostra um GRADIENTE diagonal mesclando as
duas cores.

## Classes CSS

```css
.stars{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.stars button{
  width:44px;height:44px;border-radius:8px;
  border:1.5px solid var(--line);background:#FBFCFE;
  font-size:15px;font-weight:600;cursor:pointer;color:var(--muted);
  transition:all .15s;
}
.stars button.sel-auto{
  background:var(--auto-bg);border-color:var(--auto-border);
  color:#8B6914;font-weight:700;
}
.stars button.sel-lider{
  background:var(--lider-bg);border-color:var(--lider-border);
  color:#14365C;font-weight:700;
}
.stars button.mixed{
  background:linear-gradient(135deg,var(--auto-bg) 0% 50%,var(--lider-bg) 50% 100%);
  border-color:var(--auto-border);
  border-right-color:var(--lider-border);
  border-bottom-color:var(--lider-border);
  color:#14365C;font-weight:800;
}
```

## Geração Python (server-side)

Os stars são gerados no Python com dados vindos da API. O Jinja/F-string itera
de 1 a 5 e aplica as classes conforme `n_auto` e `n_lider`:

```python
n_auto = star_val(av)   # int 1-5 ou None
n_lider = star_val(lv)  # int 1-5 ou None

for s_val in range(1, 6):
    cls = ""
    if n_auto == s_val and n_lider == s_val:
        cls = " mixed"       # ambos concordam → gradiente
    elif n_lider == s_val:
        cls = " sel-lider"   # só líder → azul
    elif n_auto == s_val:
        cls = " sel-auto"    # só auto → amarelo
    stars += f'<button class="{cls}">{s_val}</button>'
```

## lógica

- **Solo auto:** `sel-auto` — fundo amarelo claro, texto #8B6914
- **Solo líder:** `sel-lider` — fundo azul claro, texto #14365C
- **Ambos concordam:** `mixed` — gradiente diagonal 135° (50% amarelo, 50% azul),
  texto azul marinho #14365C, font-weight 800

O gradiente é: `linear-gradient(135deg, #FFF8E1 0% 50%, #E8F0FE 50% 100%)`

## Prioridade de renderização

Quando ambos concordam, `mixed` tem precedência sobre `sel-auto` e `sel-lider`.
O if/elif garante que o bloco "ambos concordam" seja checado primeiro.

## Textos longos (não numéricos)

Para perguntas de texto aberto, a resposta aparece em cards abaixo dos stars:

```html
<div class="resp auto-resp">Texto da autoavaliação</div>
<div class="resp lider-resp">Texto da avaliação do líder</div>
```

```css
.resp{font-size:12px;line-height:1.5;padding:8px 12px;border-radius:6px;margin-top:6px}
.resp.auto-resp{background:var(--auto-bg);border:1px solid var(--auto-border);color:#8B6914}
.resp.lider-resp{background:var(--lider-bg);border:1px solid var(--lider-border);color:#14365C}
```

## Layout da seção comparativa

Cada conceito do 1x1 é um bloco `.cmp-section`:

```
┌─────────────────────────────────────────┐
│ 1. Resultados                           │  ← .cmp-label
│ [1] [2] [3] [4] [5]                     │  ← .stars buttons
│ ┌───────────────────────────────────┐   │
│ │ Texto da autoavaliação (se houver)│   │  ← .resp.auto-resp
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ Texto do líder (se houver)        │   │  ← .resp.lider-resp
│ └───────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Estrutura HTML

```html
<div class="cmp-section">
  <div class="cmp-label">1. Resultados</div>
  <div class="stars">
    <button>1</button>
    <button>2</button>
    <button class="sel-auto">3</button>       <!-- auto respondeu 3 -->
    <button class="mixed">4</button>            <!-- ambos responderam 4 -->
    <button>5</button>
  </div>
  <div class="resp auto-resp">Meu texto</div>
  <div class="resp lider-resp">Texto líder</div>
</div>
```

```css
.cmp-section{padding:16px 28px;border-bottom:1px solid var(--line)}
.cmp-label{font-size:13px;font-weight:600;color:var(--navy);margin-bottom:10px;line-height:1.4}
```