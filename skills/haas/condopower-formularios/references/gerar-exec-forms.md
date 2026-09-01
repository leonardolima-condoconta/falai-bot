# gerar_exec_forms.py — Formulários C-Level

Script separado para gerar autoavaliações dos executivos (diferente do `gerar_form_avaliacao.py`).

Arquivos:
- `/opt/data/gerar_exec_forms.py` — gerador
- `/opt/data/executive_autoavaliacao.json` — perguntas específicas para C-level
- `/opt/data/exec_form_template.html` — template HTML separado

5 executivos:
| Nome | Cargo | Email |
|---|---|---|
| Marcelo Cruz | COO | marcelo@condoconta.com.br |
| Luciano Helio Bernardi | CFO | luciano.bernardi@condoconta.com.br |
| Rodrigo Costa | CTO | rodrigo.costa@condoconta.com.br |
| Rodrigo Borer Magela de Oliveira | CRO | rodrigo.borer@condoconta.com.br |
| Rodrigo Alexandre Catarcione | Head of People | rodrigo.catarcione@condoconta.com.br |

Ordem das perguntas (diferente da autoavaliação padrão):
```
Original: 1=Resultados, 2=Área, 3=Autonomia, 4=Competências, 5=V+, 6=V-, 7=PDI, 8=Motivação
Nova:     1=Resultados, 2=Área, 3=Competências, 4=Autonomia, 5=Potencial(NOVO), 6=V+, 7=V-, 8=PDI
```

Reordenação: `new_order = [0, 1, 3, 2, None, 4, 5, 6]`
- Índice 4 (None) = pergunta nova de Potencial
- Motivação/energia (índice 7 original) é removida