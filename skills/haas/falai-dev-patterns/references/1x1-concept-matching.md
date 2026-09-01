# 1x1 Semantic Concept Matching

Quando o `gerar_form_1x1.py` monta o comparativo 🟡 autoavaliação × 🔵 líder, as perguntas
NÃO podem ser pareadas por ordem alfabética — os enunciados são DIFERENTES entre os dois
formulários (ex: "Como você avalia seus Resultados" vs "Como você avalia os Resultados de Fulano").

## Solução: match por palavras-chave

```python
def match_key(data, *keywords):
    for k, v in data.items():
        kl = k.lower()
        if all(kw.lower() in kl for kw in keywords):
            return v
    return ""

linhas = [
    ("1. Resultados",                  match_key(auto_p, "resultados", "ciclo"),                match_key(av_p, "resultados", "ciclo")),
    ("2. Entrega / Área",              match_key(auto_p, "quantos", "entregou"),               match_key(av_p, "quantos", "entregou")),
    ("3. Competências",                match_key(auto_p, "competências"),                      match_key(av_p, "competências")),
    ("4. Escala de Energia × Potencial", match_key(auto_p, "motivação"),                      match_key(av_p, "potencial")),
    ("5. Step × Step",                 match_key(auto_p, "step", "analisando"),                match_key(av_p, "pronto", "step")),
    ("6. Valor Vivido × SCI",          match_key(auto_p, "valor", "viveu"),                    match_key(av_p, "valor", "exemplo", "situação")),
    ("7. Valor Evoluir × Exemplo Evoluir", match_key(auto_p, "valor", "evoluir"),            match_key(av_p, "valor", "evoluir", "precisa")),
    ("8. PDI (Autoavaliação)",         match_key(auto_p, "carreira", "fazer"),                 ""),
]
```

**Ordem definida pelo usuário:** Resultados, Competências, Escala de Energia × Potencial, Step × Step, Valor Vivido × SCI, Valor Evoluir × Exemplo Evoluir, PDI sozinho (auto).

## Estrutura das perguntas (Ciclo 2026.2)

### Autoavaliação (8 perguntas)
| N | Conceito | Keywords |
|---|---|---|
| 1 | Resultados | resultados, ciclo |
| 2 | Área/Entrega | quantos, entregou |
| 3 | Step | step, analisando |
| 4 | Competências | competências |
| 5 | Valor Viveu Bem | valor, viveu |
| 6 | Valor Evoluir | valor, evoluir |
| 7 | Motivação/Energia | motivação, escala |
| 8 | PDI/Plano | carreira, fazer |

### Avaliação do Líder (7 perguntas, Q8 Recomendação removida)
| N | Conceito | Keywords |
|---|---|---|
| 1 | Resultados de Fulano | resultados, ciclo |
| 2 | Área/Entrega | quantos, entregou |
| 3 | Step de Fulano | pronto, step |
| 4 | Competências de Fulano | competências |
| 5 | Potencial | potencial |
| 6 | SCI (Viveu Bem) | valor, exemplo, situação |
| 7 | Evoluir | valor, evoluir, precisa |

## Cuidados
- `"valor"` aparece nas perguntas 5 e 6 — keyword adicional disambigua
- Potencial SÓ existe na avaliação do líder (autoavaliação não tem)
- PDI/Motivação SÓ existem na autoavaliação (líder não tem — Q8 removida)