# Scripts de Geração de Formulários de Avaliação

Ciclo 2026.2. Scripts separados por tipo de formulário.

## `gerar_form_autoavaliacao.py`

Formulário individual de autoavaliação para UM colaborador.

```bash
cd /opt/data/convenia
/opt/data/.venv/bin/python3 gerar_form_autoavaliacao.py <email>
```

**O que faz:**
1. Busca o colaborador em `autoavaliacao_perguntas.json` (APENAS este JSON)
2. Match por email normalizado (nome.sobrenome) contra `col.nome`
3. Gera HTML com 8 perguntas (escala 1-5, texto aberto, valores CondoConta)
4. Publica no static-server

**Exemplo:** `leonardo.lima@condoconta.com.br` → `https://static-server...info/avaliacao-leonardo-de-lima`

---

## `gerar_form_lider.py`

Formulário UNIFICADO para líderes avaliarem seus liderados. Um único HTML com dropdown + perguntas dinâmicas.

```bash
cd /opt/data/convenia
/opt/data/.venv/bin/python3 gerar_form_lider.py <email_lider>
```

**O que faz:**
1. Chama `access.verify` na condopower-api → obtém `reports[]` com nome, cargo, id, email
2. Para cada liderado, busca perguntas em `avaliacao_lider_perguntas.json` (APENAS este JSON)
3. Gera HTML com dropdown de liderados (nome + cargo)
4. Ao selecionar um liderado: perguntas carregam dinamicamente com o enunciado da pergunta como `data-pergunta` em cada campo
5. Injeta `colaborador_id` (UUID do `reports[].id`), `colaborador_nome` e `leader_email` como hidden inputs
6. Submit envia JSON estruturado com enunciado→resposta:

```json
{
  "method": "desempenho.register_avaliacao",
  "params": {
    "leader_email": "andrieli.elmatos@condoconta.com.br",
    "colaborador_id": "d722bf4b-0be3-48cc-ad30-c4284f20d9ce",
    "colaborador_nome": "Dasaev Melo Menezes",
    "perguntas": {
      "Como você avalia os Resultados de Dasaev...?": "5",
      "Dasaev está pronto(a) para o próximo step?...": "Sim, domina arquitetura",
      "Recomendação para este colaborador...": "Promoção"
    }
  }
}
```

**Exemplo:** `andrieli.elmatos@condoconta.com.br` → formulário com 7 liderados no dropdown

---

## JSONs de perguntas

| Arquivo | Tipo | Colaboradores | Perguntas |
|---------|------|--------------|-----------|
| `autoavaliacao_perguntas.json` | Autoavaliação | 121 | 968 |
| `avaliacao_lider_perguntas.json` | Avaliação pelo líder | 120 | 960 |

**Estrutura da pergunta:**
```json
{
  "n": 1,
  "pergunta": "Como você avalia seus Resultados neste ciclo?",
  "tipo": "Escala 1-5",
  "celula_resposta": "C7",
  "opcoes": ["1","1.5","2","2.5","3","3.5","4","4.5","5"]
}
```

**Tipos de pergunta:**
- `Escala 1-5` → botões de seleção única (stars)
- `Lista suspensa` → botões de recomendação (reco)
- `Texto aberto` → textarea

---

## Pitfalls

- **Busca separada:** nunca combinar os dois JSONs. `auto` busca só em `autoavaliacao_perguntas.json`, `lider` busca só em `avaliacao_lider_perguntas.json`. Combinar retorna dados errados (o colaborador pode estar em ambos com perguntas diferentes).
- **Slug com acentos:** ç, ã, é, etc. são rejeitados pelo static-server. Sanitizar antes de publicar.
- **CORS:** enviar JSON cross-origin com headers customizados → preflight → 302 → ERR_FAILED. Nenhuma solução client-side funciona. Ver `references/cors-formularios.md`.
- **Líder sem liderados:** `access.verify` → `reports[]` vazio → informar "Você não possui liderados ativos" e encerrar.
- **Email nulo nos reports:** ~20% dos colaboradores têm `email: null` no `access.verify`. O `gerar_form_lider.py` usa `reports[].id` como `colaborador_id` (UUID), não email.
- **Perguntas por líder vs autoavaliação:** lider avalia Resultados e Potencial (escalas separadas), autoavaliacao pergunta sobre valores CondoConta e motivação. Estruturas diferentes.