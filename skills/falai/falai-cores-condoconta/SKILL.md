---
name: falai-cores-condoconta
version: "1.0.0"
description: "Cores CondoConta: #00263e #fdc32f #e1bf6e. Usar sempre."
---

# Cores Oficiais CondoConta

**Fonte:** Catarcione / Time de People — Ago/2026

## Cores oficiais

| Cor | Hex | Uso |
|-----|-----|-----|
| **Navy** | `#00263e` | Fundo institucional, headers, footer, seções escuras |
| **Gold (fundo escuro)** | `#fdc32f` | Destaque sobre navy — títulos, acentos, números |
| **Gold (fundo claro)** | `#e1bf6e` | Destaque sobre branco — eyebrows, ícones, tags |

## Regra de aplicação

- `#fdc32f` → usar SOMENTE sobre fundo escuro (`#00263e`)
- `#e1bf6e` → usar SOMENTE sobre fundo claro (branco/card)
- `#00263e` → azul institucional principal para fundos escuros

## Mapeamento para CSS tokens do design system

```css
--navy:      #00263e;   /* seções dark, títulos */
--navy-deep: #00263e;   /* header, footer */
--gold:      #fdc32f;   /* destaque sobre navy */
--gold-deep: #e1bf6e;   /* destaque sobre claro */
```

## Obrigatório

⚠️ TODOS os relatórios, dashboards, apresentações e HTMLs gerados pela Falai DEVEM usar estas cores. Nunca usar cores antigas (`#14365C`, `#0A2138`, `#F4B72C`, `#C98F0C`).