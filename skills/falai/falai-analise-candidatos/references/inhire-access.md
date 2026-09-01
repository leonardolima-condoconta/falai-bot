# InHire Access Patterns

## Login via Browser (método principal)

1. Navegar para `https://condoconta.inhire.app/login`
2. Preencher campos via JS (não via `browser_type` — os refs podem mudar):
   ```js
   var email = document.querySelector('input[name="email"]');
   var pass = document.querySelector('input[name="password"]');
   var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
   setter.call(email, '...');
   email.dispatchEvent(new Event('input', { bubbles: true }));
   setter.call(pass, '...');
   pass.dispatchEvent(new Event('input', { bubbles: true }));
   ```
3. Clicar "Acessar conta" via JS
4. Confirmar login: snapshot deve mostrar "Olá, [Nome]!"

## Extração de Dados

### Página de vaga (pública)
`document.body.innerText` retorna toda a descrição da vaga.

### Lista de candidatos
`document.body.innerText` retorna todos os candidatos com:
- Iniciais, dias no funil, fonte, nome, etapa

### Card de candidato (logado)
Navegar para `?card=<id>` e usar `document.body.innerText` para extrair:
- Pretensão salarial
- Disponibilidade presencial
- Localização
- Email, telefone, LinkedIn
- CV completo (se disponível)

## SPA Limitations

- `browser_snapshot` frequentemente retorna incompleto ou vazio
- `browser_console` com `document.body.innerText` é mais confiável
- A página perde sessão entre navegações — re-logar quando necessário
- O card ID pode ser extraído da URL após clicar num candidato: `?card=<uuid>`

## API Auth (descoberto em 18/08/2026)

- Endpoint: `POST https://auth.inhire.app/login`
- Header: `X-Tenant: condoconta`
- Retorna JWT válido mas API REST (`api.inhire.app`) retorna 403
- A SPA usa mecanismo adicional (cookie de sessão ou header customizado)
- Browser com sessão ativa > curl com token

## Token JWT Decode

```python
import json, base64
parts = token.split('.')
payload = parts[1] + '=' * (4 - len(parts[1]) % 4)
decoded = base64.urlsafe_b64decode(payload)
data = json.loads(decoded)
# Contém: id, name, email, tenantId, roleName, teams, iat, exp, iss
```