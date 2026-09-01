# 1x1 Semantic Mapping — Par de Perguntas Auto × Líder

O `gerar_form_1x1.py` monta um comparativo lado a lado entre autoavaliação e
avaliação do líder. As perguntas têm enunciados DIFERENTES em cada formulário:
"Como você avalia seus Resultados" (auto) vs "Como você avalia os Resultados de
Fulano" (líder). Portanto o pareamento NÃO é por string match — é por palavra-chave
semântica.

## Mapeamento final (8 linhas, definido pela Amandinha em 01/09/2026)

| # | Label | Auto (keywords) | Líder (keywords) | Nota |
|---|---|---|---|---|
| 1 | Resultados | `resultados`, `ciclo` | `resultados`, `ciclo` | |
| 2 | Entrega / Área | `quantos`, `entregou` | `quantos`, `entregou` | |
| 3 | Competências | `competências` | `competências` | |
| 4 | Escala de Energia × Potencial | `motivação` | `potencial` | Conceitos DIFERENTES — auto mede motivação, líder mede potencial |
| 5 | Step × Step | `step`, `analisando` | `pronto`, `step` | |
| 6 | Valor Vivido × SCI | `valor`, `viveu` | `valor`, `exemplo`, `situação` | |
| 7 | Valor Evoluir × Exemplo Evoluir | `valor`, `evoluir` | `valor`, `evoluir`, `precisa` | |
| 8 | PDI (Autoavaliação) | `carreira`, `fazer` | — (sem par no líder) | Somente na autoavaliação |

## Função de match

```python
def match_key(data, *keywords):
    for k, v in data.items():
        kl = k.lower()
        if all(kw.lower() in kl for kw in keywords):
            return v
    return ""
```

Itera sobre as chaves do dict `raw.perguntas` e retorna o VALOR (resposta). As
chaves são o texto completo da pergunta. O match é ALL keywords — evita falsos
positivos (ex: "valor" sozinho casa V+ e V-).

## Regras importantes

- **NUNCA usar ordem alfabética.** As perguntas da auto e do líder têm redações
  diferentes e a ordem lexicográfica não produz alinhamento correto.
- **NUNCA assumir que a pergunta existe em ambos.** A linha 8 (PDI) só existe na
  autoavaliação — o líder não tem pergunta equivalente.
- **A linha 4 (Escala de Energia × Potencial) é um pareamento INTENCIONAL de
  conceitos diferentes.** A pergunta de "motivação" da auto e a de "potencial" do
  líder medem coisas distintas, mas são comparadas lado a lado por decisão de
  design.
- **Ordem no 1x1:** a ordem das linhas é DIFERENTE da ordem dos formulários
  individuais. O 1x1 REORDENA as perguntas para o fluxo de conversa do feedback.