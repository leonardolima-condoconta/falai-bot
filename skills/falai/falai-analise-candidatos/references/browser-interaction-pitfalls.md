# Falai — Pitfalls de Interação com o Browser no InHire

Registro de comportamentos observados do InHire (SPA React) que impactam
a automação via browser. Atualizado em 20/08/2026.

## Button vs Link no Card de Candidato

No modo Lista, cada linha de candidato tem dois elementos com o texto do nome:

```html
<!-- Botão: abre o card no próprio InHire -->
<button>Laura Schmidt de Oliveira <img alt="expand" /></button>

<!-- Link: leva ao LinkedIn (externo) -->
<a href="https://www.linkedin.com/in/lauraschmidto">Laura Schmidt de Oliveira</a>
```

O `browser_snapshot` diferencia:
- `button "Laura Schmidt de Oliveira" [ref=e87]` → **clicar neste**
- `link "Laura Schmidt de Oliveira" [ref=e88]` → **NUNCA clicar**

Clicar no link redireciona para `linkedin.com/authwall` e perde a sessão do InHire.

## Kanban View — Cliques Não Confiáveis

Na visualização Kanban, os cards são elementos customizados da SPA.
O `browser_click` frequentemente NÃO registra — a URL permanece na mesma página
sem abrir o card. Comportamento observado em 20/08/2026:

- `browser_click` no card da Laura no Kanban → nenhuma mudança de URL
- `browser_click` repetido → mesmo resultado
- Solução: alternar para Lista e clicar no botão

## Extração de Card IDs — NÃO FUNCIONA pelo DOM

Tentativas de extrair card UUIDs em lote falharam consistentemente:

| Abordagem | Resultado |
|---|---|
| `querySelectorAll('[onclick*="card"]')` | `[]` — onclick não está nos atributos HTML |
| React fiber walking (`__reactFiber$`, `__reactInternalInstance$`) | `[]` — props não expõem `cardId` publicamente |
| `querySelectorAll('[class*="card"]')` | `[]` — classes são hashes CSS-in-JS |

**Única forma confiável de obter um card UUID:**
1. Isolar candidato via busca
2. Clicar no botão do nome (modo Lista)
3. Capturar `window.location.href` → extrair `?card=<uuid>`

Não perca tempo tentando extrair todos os IDs de uma vez. Extraia um por um.

## Sessão Expira

Após ~10-15 minutos sem interação, o InHire redireciona para `/login`.
Sinais de que a sessão expirou:

- `document.body.innerText` mostra "Acesse sua conta", "Esqueceu sua senha?" etc.
- Snapshot mostra apenas "Service and" / "Privacy" no header
- Ou snapshot normal com campos de login (`textbox "Email *"`, `textbox "Senha *"`)

Solução:
1. Navegar para `/login`
2. Fazer `browser_snapshot` para obter refs dos campos
3. `browser_type` email e senha
4. `browser_snapshot` para confirmar que o botão liberou
5. `browser_click` no botão "Acessar conta"
6. Confirmar com `document.body.innerText` mostrando "Olá, [Nome]!"
7. Re-navegar para `/jobs/<uuid>` e retomar

## Snapshot Vazio ou Incompleto

A SPA React frequentemente retorna snapshot vazio após navegação:
- `browser_snapshot` → "(empty page)" ou apenas 1-3 elementos genéricos
- `document.body.innerText` → conteúdo completo

**Regra:** sempre use `browser_console` com `document.body.innerText` para extrair
dados. Use `browser_snapshot` apenas para identificar refs de elementos interativos
(botões, inputs).

## Busca por Nome

Digitar no campo de busca + Enter isola o candidato. Útil para encontrar um nome
específico quando há dezenas de cards espalhados por colunas no Kanban.

Após a busca, os contadores mudam (ex: "Ativos 28" → "Ativos 1"). Para ver a lista
completa novamente, limpe o campo ou re-navegue.

**Fluxo recomendado para análise em lote:**
1. Alterne para modo **Lista** (nunca Kanban)
2. Para cada candidato alvo: busque pelo nome → clique no **botão** (não link) →
   extraia `document.body.innerText` → repita
3. Se a sessão expirar no meio, re-autentique e continue

## Navegação Direta por URL com ?card=

A URL `https://condoconta.inhire.app/jobs/<uuid>?card=<card-uuid>` abre o card
diretamente, mas SÓ funciona com sessão ativa. Sem sessão, redireciona para login.

Para obter o `card-uuid` de um candidato, a forma mais confiável é:
1. Alternar para Lista
2. Clicar no botão do nome
3. Capturar `window.location.href` que agora contém `?card=<uuid>`

## Clicar na Row vs no Botão

No modo Lista, cada linha tem o elemento pai com `onclick` (ex: `e65`, `e66`).
Clicar nesse elemento pai NÃO abre o card — apenas seleciona a linha (checkbox).
Sempre clique no **botão** interno que contém o nome da candidata.