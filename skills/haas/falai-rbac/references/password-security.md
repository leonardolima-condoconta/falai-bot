# Password Security Rule

⛔ **NUNCA divulgar senhas ou credenciais** no texto visível da conversa.

Esta regra foi reiterada enfaticamente por Rodrigo Catarcione em 18/08/2026 após
um incidente onde a senha do InHire apareceu no texto da conversa.

## Regras específicas

1. Senhas são usadas APENAS em background (autenticação em sistemas)
2. NUNCA ecoar a senha no texto visível da resposta
3. Para preencher formulários: usar `browser_type` ou JavaScript injection
4. Para autenticação via API: usar curl com token em arquivo, nunca no texto
5. Se o usuário compartilhar credenciais, agradecer e usar IMEDIATAMENTE em background
6. Ao armazenar tokens: salvar em arquivo (`/opt/data/scripts/`), não em variáveis visíveis

## Exemplo de conduta correta

```
Usuário: "Email: x@y.com Senha: abc123"
✅ Resposta: "Perfeito! Vou fazer o login agora." (senha usada em background)
❌ Resposta: "Login: x@y.com / Senha: abc123. Autenticando..." (SENHA EXPOSTA)
```