# Formato JSON dos formulários de avaliação — validado empiricamente 21/08/2026

## Autoavaliação (gerar_form_avaliacao.py / gerar_form_autoavaliacao.py)

```json
{
  "method": "desempenho.register_avaliacao",
  "params": {
    "colaborador_id": "ad9fbf44-d192-469d-9cc7-26ce659bbee5",
    "colaborador_email": "leonardo.lima@condoconta.com.br",
    "colaborador_nome": "Leonardo de Lima",
    "perguntas": {
      "Como você avalia seus Resultados neste ciclo? (1 = muito abaixo do esperado, 5 = excepcional)": "5",
      "Quantos fluxos de IA você implementou...": "3 fluxos, redução de 40h/mês",
      "Analisando o seu step atual sugerido (Step IV)...": "Sim, domina arquitetura",
      "Como você avalia suas Competências neste ciclo?": "4",
      "Cite um valor CondoConta que você sente que viveu bem...": "Inovação - pipeline de IA",
      "Cite um valor CondoConta que você sente que precisa evoluir...": "Documentação técnica",
      "O que você quer fazer, nos próximos 6 meses...": "Liderar squad e mentoria",
      "Em uma escala de 1 a 5, qual seu nível de motivação...": "4"
    }
  }
}
```

## Avaliação do Líder (gerar_form_lider.py)

```json
{
  "method": "desempenho.register_avaliacao",
  "params": {
    "leader_email": "andrieli.elmatos@condoconta.com.br",
    "colaborador_id": "d722bf4b-0be3-48cc-ad30-c4284f20d9ce",
    "colaborador_nome": "Dasaev Melo Menezes",
    "perguntas": {
      "Como você avalia os Resultados de Dasaev Melo Menezes neste ciclo? (1 = muito abaixo do esperado, 5 = excepcional)": "5",
      "Quantos fluxos de IA você implementou e colocou em produção neste ciclo... (responda pensando na entrega de Dasaev Melo Menezes.)": "2 fluxos, 20h/mês",
      "Dasaev Melo Menezes está pronto(a) para o próximo step? O que falta...": "Sim, falta mentoria de juniores",
      "Como você avalia as Competências de Dasaev Melo Menezes neste ciclo?": "4",
      "Como você avalia o Potencial de Dasaev Melo Menezes para assumir mais responsabilidade nos próximos 12-18 meses?": "5",
      "Cite um exemplo concreto (SCI) de um valor CondoConta bem vivido por essa pessoa.": "Migração de Maio - antecipou riscos",
      "Cite um exemplo concreto de onde essa pessoa precisa evoluir em relação aos Valores CondoConta.": "Comunicação com stakeholders",
      "Recomendação para este colaborador neste ciclo (Promoção / Mérito / Bônus / Manter / PDI intensivo / PIP / Desligamento):": "Promoção"
    }
  }
}
```

## Pulse (form-pulse.html)

```json
{
  "method": "pulse.submit",
  "params": {
    "area": "People",
    "lideranca_direta": "Rodrigo Catarcione",
    "sentimento_pessoal": "4",
    "relacao_lideranca": "4",
    "sentimento_time": "5",
    "ia_ganho_tempo": "5",
    "ia_qualidade": "4",
    "enps": "9",
    "motivo_nota": "Time engajado, autonomia e propósito claro."
  }
}
```

## Regras de ouro

- `colaborador_id` é o UUID do `access.verify` → `employee.id` ou `reports[].id` (nunca email)
- `leader_email` vem de `access.verify` → `employee.email`
- Perguntas vão como **chaves** no objeto `perguntas` (enunciado completo), não como `q1`, `q2`
- Escalas (1-5, eNPS 0-10) enviam o valor **numérico** (string), não o texto do botão
- `pulse.submit` **exige** `respondent_email` (validado empiricamente: omitir → `MISSING_PARAMS`)