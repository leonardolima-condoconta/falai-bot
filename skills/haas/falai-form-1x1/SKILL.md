---
name: falai-form-1x1
description: Gera HTML de 1x1 com stars comparativos lado a lado.
version: 1.0.0
---

# 1x1 — Geração e Layout

## Gatilho
"1x1 do <lider> com <colaborador>" / "gerar 1x1"

## Script
```bash
python3 /opt/data/convenia/gerar_form_1x1.py <email_lider> <email_colaborador>
```

## Layout (full-screen)

```
┌─── HEADER (full width) ──────────────────┐
│  CondoConta · People         1x1          │
│  Líder ↔ Colaborador                       │
├────────────── 60% ───┬────── 40% ─────────┤
│ div.stars lado a lado │ 🎯 Nine Box 3×3   │
│ cmp-section × 8       │ + inputs notas     │
│ Pergunta (label)      │                    │
│ [1] [2] [3] [4] [5]   ├────────────────────┤
│  amarelo=auto         │ 📈 PDI             │
│  azul=líder           │ 6 campos           │
│  gradiente=mesmo valor│                    │
├───────────────────────┴────────────────────┤
│ 📝 Justificativa + [Salvar 1x1]           │
└────────────────────────────────────────────┘
```

## CSS — Stars (padrão autoavaliação/líder)

```css
.stars button { width:44px; height:44px; border-radius:8px; }
.stars button.sel-auto { background:var(--auto-bg); border-color:var(--auto-border); color:#8B6914; }
.stars button.sel-lider { background:var(--lider-bg); border-color:var(--lider-border); color:#14365C; }
.stars button.mixed { background:linear-gradient(135deg, var(--auto-bg) 50%, var(--lider-bg) 50%); }
```

## Mapeamento semântico (8 linhas)

| # | Conceito | Auto (keyword) | Líder (keyword) |
|---|---|---|---|
| 1 | Resultados | resultados + ciclo | resultados + ciclo |
| 2 | Entrega / Área | quantos + entregou | quantos + entregou |
| 3 | Competências | competências | competências |
| 4 | Escala de Energia × Potencial | motivação | potencial |
| 5 | Step × Step | step + analisando | pronto + step |
| 6 | Valor Vivido × SCI | valor + viveu | valor + exemplo + situação |
| 7 | Valor Evoluir × Exemplo Evoluir | valor + evoluir | valor + evoluir + precisa |
| 8 | PDI (Autoavaliação) | carreira + fazer | — (sem par) |

Perguntas são pareadas por PALAVRA-CHAVE, não por ordem alfabética.

## Pitfalls

- `linhas` = lista de tuplas `(label, valor_auto, valor_lider)` — NÃO um dict
- Textos não-numéricos aparecem como `<div class="resp">` abaixo dos stars
- Sem dados salvos: placeholder "Nenhuma avaliação registrada ainda"