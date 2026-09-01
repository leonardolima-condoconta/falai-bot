# form.pulse.get vs pulse.answers — discrepância de resultados por área

## Caso real — 01/09/2026

**Contexto:** Renata Paim (Treasury Manager, Banking Operations, nível 2) pediu para verificar
quantas pessoas de Banking Operations responderam a rodada de Pulses de Agosto/2026.

## Resultados conflitantes

| Método | Params | Resultado |
|---|---|---|
| `form.pulse.get` | `requester_email: "rodrigo.catarcione@condoconta.com.br"`, `area: "Banking Operations"` | **4 respostas** (ids 49, 77, 80, 113) |
| `pulse.answers` | `requester_email: "rodrigo.catarcione@condoconta.com.br"` → filtro manual por `raw.area` | **6 respostas** (ids 18, 22, 49, 77, 80, 113) |

## O que faltou

As duas respostas ausentes no `form.pulse.get`:
- **id 18** — 24/08, eNPS 9, liderança: Luciano Bernardi
- **id 22** — 24/08, eNPS 9, liderança: Renata Paim

Ambas do **primeiro dia da rodada** (24/08). A causa raiz do filtro incompleto não foi
identificada — pode ser relacionada ao `area` ter sido populado depois da gravação inicial
ou a uma diferença na indexação entre os dois métodos.

## Lição

1. **`form.pulse.get` com `area` NÃO é autoritativo para contagem total.** Use como consulta
   rápida, mas sempre cruze com `pulse.answers` quando:
   - O usuário contestar a contagem
   - O número parecer baixo para o tamanho do time
   - A pergunta for "quantas pessoas já responderam?"

2. **Padrão de dupla verificação:**
   ```python
   # 1. Consulta rápida
   form.pulse.get(requester_email=people_email, area="Área X")
   
   # 2. Confirmação autoritativa (sempre)
   pulse.answers(requester_email=people_email)
   # → filtre manualmente por raw["area"]
   ```

3. **Quando o usuário diz "tem mais gente que respondeu":** acredite nele e refaça com
   `pulse.answers` — não insista no `form.pulse.get`.