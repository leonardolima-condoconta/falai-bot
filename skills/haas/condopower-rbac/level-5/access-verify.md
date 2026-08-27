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

## Uso pelos crons
- `aniversarios-do-dia` → usa `access.verify` para resolver menções
- `tempo-casa-mensal` → idem
- `sync-convenia-employees` → chama `roster.sync` diretamente