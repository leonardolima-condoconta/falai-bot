# Layout full-screen do 1x1

O 1x1 NÃO usa o layout centralizado com `max-width` como os outros formulários (autoavaliação, líder, Pulses). Ele ocupa **100% da tela** com scroll único no body (todas as seções rolam juntas).

## Estrutura

```
body (100vh, flex column, overflow-y: auto — SCROLL ÚNICO)
├── header (full-width, navy background)
├── wrapper (flex:1, 2-column grid)
│   ├── coluna esquerda (padding:20px)
│   │   ├── comparativo 🟡 Auto | 🔵 Líder
│   │   ├── justificativa (textarea)
│   │   └── botão Salvar 1x1
│   └── coluna direita (padding:20px, fundo branco, border-left)
│       ├── 🎯 Nine Box (grid 3×3 + inputs nota)
│       └── 📈 PDI (6 campos)
└── footer (full-width, navy background)
```

## CSS crítico

```css
body{padding:0;height:100vh;overflow-y:auto;display:flex;flex-direction:column}
body > header{flex-shrink:0}
.wrapper{flex:1;display:grid;grid-template-columns:3fr 2fr;gap:0}
.wrapper > div{padding:20px}
.wrapper > div:last-child{background:var(--card);border-left:1px solid var(--line)}
```

## Diferença: scroll único vs scroll independente

A VERSÃO FINAL usa `overflow-y:auto` no **body** (não nas colunas). Motivo: o usuário pediu que formulário, 9box e PDI rolem juntos como uma página única, sem barras de scroll separadas.

| Versão | body | colunas |
|---|---|---|
| Anterior (v1) | `overflow:hidden` | `overflow-y:auto` em cada |
| Final (v2) | `overflow-y:auto` | sem overflow |

## Comparação com outros formulários

| Formulário | Layout |
|---|---|
| Pulses | centralizado, `max-width: 600px`, scroll no body |
| Autoavaliação | centralizado, `max-width: 700px`, scroll no body |
| Líder | centralizado, `max-width: 800px`, scroll no body |
| 1x1 | full-screen, 100vw×100vh, scroll único no body |