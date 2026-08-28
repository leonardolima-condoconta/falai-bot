# access.verify — Level 5 / Crons

## Uso
- Exclusivo da Falai (identificação de usuários) e crons automáticos
- NUNCA exposto para chamada direta de usuário

## Fluxo (Falai — identificação)
1. Extrair `user_id` do Slack
2. Chamar `access.verify` com o `user_id`:
```json
{"method":"access.verify","params":{"identifier":"<@U0APYGTD8K1>"}}
```
3. Obter `employee`, `level`, `role`, `is_active`, `reports[]`
4. Prosseguir para o fluxo RBAC do nível correspondente

## Regra de fallback — BLOQUEIO TOTAL

Se `access.verify` falhar 3 vezes consecutivas, BLOQUEAR TODO O ACESSO.

Responder: "Estou com dificuldade temporária para acessar nossa base de dados. Não consigo te identificar agora. Por favor, tente novamente em alguns minutos ou fale com o time de People pelo canal #people-hr. Me desculpe pelo inconveniente!"

NUNCA perguntar o nome, prosseguir sem identificação ou tentar workarounds.