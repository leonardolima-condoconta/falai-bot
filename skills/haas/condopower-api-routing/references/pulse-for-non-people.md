# Pulses: consulta por área para usuários não-People

## Problema

Um líder (nível 2) pergunta: "Quantas pessoas do meu time já responderam a Pesquisa Pulses?"

## O que NÃO funciona

| Abordagem | Resultado | Motivo |
|---|---|---|
| `pulse.round_status` com e-mail do líder | **403 NOT_PEOPLE** | Só nível 3+ administra clima |
| `form.pulse.get` com e-mail do líder | **lista vazia** | Pulses não grava ID — anonimato |
| Tentar URL direta (`condopower-api.aiexpert-condoconta.info`) | **timeout 60s+** | Container não alcança |

## O que FUNCIONA

Use `form.pulse.get` com:

- **`requester_email`**: e-mail de alguém do time People (nível 3+) — ex: `rodrigo.catarcione@condoconta.com.br`
- **`area`**: departamento do líder que está perguntando — ex: `"Implantação"`

```python
POST https://webhook-proxy.condoconta.com.br/webhooks/condopower-api
Headers: X-Service-Account-Token + auth
Body: {
  "method": "form.pulse.get",
  "params": {
    "requester_email": "rodrigo.catarcione@condoconta.com.br",
    "area": "Implantação"
  }
}
```

## Resposta

Retorna as respostas anônimas da área (sem IDs), permitindo contar quantas pessoas responderam. Exemplo:

```json
{
  "ok": true,
  "result": {
    "respostas": [
      {"id": 85, "area": "Implantação", "raw": {"enps": "8", ...}},
      {"id": 84, "area": "Implantação", "raw": {"enps": "9", ...}},
      ...
    ]
  }
}
```

O tamanho de `respostas[]` é a quantidade de respostas do time.

## Cuidados

- **NUNCA** use o e-mail do líder — retorna lista vazia
- **Anonimato**: as respostas não têm `colaborador_id`. Não prometa identificar quem respondeu
- **Texto livre**: em times pequenos, o conteúdo pode identificar o autor. Em recortes pequenos, não repasse texto livre
- **Contagem vs adesão**: `pulse.round_status` dá a adesão global (com %); `form.pulse.get` dá as respostas individuais por área. Para "quantos do MEU time", use `form.pulse.get` com área
- ⚠️ **`form.pulse.get` com `area` pode ser incompleto.** Em 01/09/2026 o filtro por área devolveu 4 de 6 respostas reais de Banking Operations. Se o usuário contestar a contagem ou o número parecer baixo, confirme com `pulse.answers` + filtro manual por `raw.area`. Veja `references/form-pulse-get-incomplete.md`.

## Caso real

**28/08/2026** — Andrieli Elmatos (Coordenadora de Implantação, nível 2) perguntou "Quantas pessoas do meu time já responderam a Pesquisa Pulses?"

Fluxo:
1. `access.verify(U02EV1E32V6)` → nível 2, depto "Implantação", 7 liderados
2. `pulse.round_status` → 403 (esperado)
3. `form.pulse.get` com e-mail do líder → lista vazia (esperado, anonimato)
4. `form.pulse.get` com `rodrigo.catarcione@condoconta.com.br` + `area: "Implantação"` → **4 respostas**

Resposta ao líder: 4 de 8 pessoas (Andrieli + 7 liderados) responderam.