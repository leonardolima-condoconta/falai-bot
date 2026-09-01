# JSON de Exemplos — Formulários People

⚠️ Atualizado 21/08/2026 — `lider_email`, `lider_id`, `colaborador_email` e validação empírica do `pulse.submit`.

---

## Pulse (form-pulse.html)

Submit: `POST /rpc` → `pulse.submit`

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

Notas: valores são strings numéricas 1-5 (mapeadas no JS via `data-value` no formulário, exibindo emojis + texto), exceto `enps` que é 0-10.

⚠️ **Validação empírica (21/08/2026):** `pulse.submit` EXIGE `respondent_email`. Chamada sem esse campo retorna:
`{"ok":false,"error":{"code":"MISSING_PARAMS","fields":[{"field":"respondent_email","reason":"Field required"}]}}`

O formulário HTML NÃO inclui email por decisão de anonimato. Se precisar incluir: o email vai pra tabela de participação (controle de duplicidade), NÃO pra tabela de respostas (que é anônima).

---

## Autoavaliação (gerar_form_avaliacao.py)

Submit: `POST /rpc` → `desempenho.register_avaliacao`

```json
{
  "method": "desempenho.register_avaliacao",
  "params": {
    "colaborador_id": "ad9fbf44-d192-469d-9cc7-26ce659bbee5",
    "colaborador_email": "leonardo.lima@condoconta.com.br",
    "colaborador_nome": "Leonardo de Lima",
    "area": "Finance",
    "perguntas": {
      "Como você avalia seus Resultados neste ciclo? (1 = muito abaixo do esperado, 5 = excepcional)": "4",
      "Quantos relatórios/dashboards você entregou no prazo este ciclo...": "TESTE",
      "Analisando o seu step atual sugerido...": "TESTE",
      "Como você avalia suas Competências neste ciclo?": "4",
      "Cite um valor CondoConta que você sente que viveu bem neste ciclo, com um exemplo concreto.": "TESTE",
      "Cite um valor CondoConta que você sente que precisa evoluir, com um exemplo concreto.": "TESTE",
      "O que você quer fazer, nos próximos 6 meses, para evoluir na sua carreira? (isso vira seu PDI)": "TESTE",
      "Em uma escala de 1 a 5, qual seu nível de motivação/energia hoje na CondoConta?": "5"
    }
  }
}
```

### Campos e origens
| Campo | Origem |
|---|---|
| `colaborador_id` | `access.verify(email)` → `employee.id` (UUID 36 chars). Se API falhar = string vazia. |
| `colaborador_email` | `access.verify(email)` → `employee.email` (fallback: email usado na consulta) |
| `colaborador_nome` | JSON de perguntas → `colaborador.nome` |
| `area` | JSON de perguntas → `colaborador.area` (ex: "Finance", "Dados e AI") |
| `perguntas` | Mapa `enunciado → resposta`. Enunciado = texto completo da pergunta do JSON. Escala → valor numérico via `data-value`. |

---

## Avaliação do Líder (gerar_form_lider.py)

Submit: `POST /rpc` → `desempenho.register_avaliacao`

```json
{
  "method": "desempenho.register_avaliacao",
  "params": {
    "lider_email": "andrieli.elmatos@condoconta.com.br",
    "lider_id": "bfd80779-d0e1-4bc6-9b75-abc123def456",
    "colaborador_id": "d722bf4b-0be3-48cc-ad30-c4284f20d9ce",
    "colaborador_nome": "Dasaev Melo Menezes",
    "area": "Implantação",
    "perguntas": {
      "Como você avalia os Resultados de Dasaev Melo Menezes neste ciclo? (1 = muito abaixo do esperado, 5 = excepcional)": "5",
      "Quantos fluxos de IA você implementou e colocou em produção neste ciclo...": "2 fluxos, ganho de 20h/mês",
      "Dasaev Melo Menezes está pronto(a) para o próximo step?...": "Sim, domina arquitetura",
      "Como você avalia as Competências de Dasaev Melo Menezes neste ciclo?": "4",
      "Como você avalia o Potencial de Dasaev Melo Menezes para assumir mais responsabilidade nos próximos 12-18 meses?": "5",
      "Cite um exemplo concreto (SCI) de um valor CondoConta bem vivido por essa pessoa.": "Na migração de Maio, antecipou riscos",
      "Cite um exemplo concreto de onde essa pessoa precisa evoluir em relação aos Valores CondoConta.": "Comunicação com stakeholders",
      "Recomendação para este colaborador neste ciclo (Promoção / Mérito / Bônus / Manter / PDI intensivo / PIP / Desligamento):": "Promoção"
    }
  }
}
```

### Campos e origens
| Campo | Origem |
|---|---|
| `lider_email` | `access.verify(lider_slack_id)` → `employee.email` |
| `lider_id` | `access.verify(lider_slack_id)` → `employee.id` |
| `colaborador_id` | `access.verify(lider_slack_id)` → `reports[i].id` (UUID) |
| `colaborador_nome` | `access.verify(lider_slack_id)` → `reports[i].full_name` |
| `area` | `access.verify(lider_slack_id)` → `reports[i].department` (fallback: `area` do JSON de perguntas) |
| `perguntas` | Mapa `enunciado → resposta` do `avaliacao_lider_perguntas.json` |

⚠️ **Nome do campo:** `lider_email` e `lider_id` (não `leader_email`/`leader_id`). Alterado em 21/08/2026.

### Fluxo do gerar_form_lider.py
1. `access.verify` com email do líder → obtém `reports[]` + `leader.id`
2. Para cada `rep` em `reports[]`, busca perguntas no `avaliacao_lider_perguntas.json` (match por partes do nome)
3. Gera HTML com dropdown de liderados + perguntas dinâmicas (JS carrega ao selecionar)
4. Hidden inputs: `colaborador_id`, `colaborador_nome`, `area`, `lider_email`, `lider_id`
5. Submit: `data-pergunta` → enunciado completo, `data-value` → valor

### Cobertura do JSON de perguntas
- `avaliacao_lider_perguntas.json` cobre 120 de 121 colaboradores
- Schaiane da Cruz (liderada do Catarcione) NÃO está no spreadsheet
- Alguns emails vêm `null` da API (~20 de 121) — isso NÃO afeta o formulário (usa UUID como identificador)

### ⚠️ Pitfall CORS
fetch() cross-origin com `Content-Type: application/json` + headers customizados dispara preflight OPTIONS → ForwardAuth redireciona para login → `Redirect is not allowed for a preflight request` → ERR_FAILED.

Abordagens testadas (21/08/2026):
- Auth no body como `URLSearchParams` + `Content-Type: application/x-www-form-urlencoded` → API rejeita (`Input should be a valid dictionary`)
- Auth como headers custom + JSON body → preflight 302 → ERR_FAILED
- `Content-Type: application/json` sem auth nos headers (auth no body) → ainda dispara preflight

Solução pendente: proxy no mesmo domínio do static-server ou CORS liberado na condopower-api.