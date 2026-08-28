# form.*.get — Leitura de formulários (Level 3+)

## Pré-condições
- Usuário level 3+ (`team_people`, `admin` ou `superadmin`)
- `requester_email` = email do usuário autenticado

## Métodos disponíveis

| Método | Filtros |
|---|---|
| `form.autoavaliacao.get` | `colaborador_id`, `area`, `quantidade` |
| `form.avaliacao_lider.get` | `lider_id`, `colaborador_id`, `area`, `quantidade` |
| `form.1x1.get` | `lider_id`, `colaborador_id`, `area`, `quantidade` |
| `form.pdi.get` | `lider_id`, `colaborador_id`, `area`, `quantidade` |
| `form.9box.get` | `lider_id`, `colaborador_id`, `area`, `quantidade` |
| `form.pulse.get` | `area`, `quantidade` |

## Fluxo genérico

### 1. Coletar parâmetros
```
Para consultar os formulários respondidos, preciso de:
- Tipo de formulário (autoavaliacao / avaliacao_lider / 1x1 / pdi / 9box / pulse)
- Email do colaborador ou área (opcional)
- Quantidade de respostas (opcional, padrão 50, máximo 50)
```

### 2. Resolver o colaborador_id
Se o usuário informou nome ou email:
- Chamar `access.verify` com o identificador → obter `colaborador_id`
- Se não encontrado, reportar erro

### 3. Enviar para API
```json
{
  "method": "form.autoavaliacao.get",
  "params": {
    "requester_email": "people@condoconta.com.br",
    "colaborador_id": "uuid...",
    "quantidade": 5
  }
}
```

### 4. Formatar resposta
Retornar as respostas em formato legível:
- Número de respostas encontradas
- Para cada resposta: `id`, `created_at`, `tipo_formulario`, `area`
- Conteúdo do `raw` formatado (perguntas → respostas)

Exemplo de resposta:
```
📋 *Autoavaliação — Leonardo de Lima*
Resposta #42 — 25/08/2026 14:03 — Finance

Resultados: 5
Competências: 4
...
```

## Regras
- O serviço já filtra por nível: level 3+ vê tudo, abaixo não tem acesso
- `form.pulse.get` é anônimo — não traz `colaborador_id` nem nome
- Lista vazia não prova inexistência do formulário — pode estar fora do alcance
- `requester_email` DEVE existir no cadastro (404 se não existir)