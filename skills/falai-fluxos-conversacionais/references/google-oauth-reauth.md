# Reautorização OAuth Google (Gmail.send / Calendar.events)

Quando precisar reautorizar o Google OAuth para adicionar scopes de escrita (gmail.send, calendar.events), a partir de um client "Web" (redirect `http://localhost`).

## Técnica que funciona (sem PKCE)

`InstalledAppFlow` gera PKCE por padrão, mas o client Web da CondoConta não aceita `code_verifier` — dá erro `invalid_grant: code_verifier or verifier is not needed`.

Passo a passo:

1. Gerar URL SEM PKCE:
   ```python
   flow = InstalledAppFlow.from_client_secrets_file(
       '/opt/data/google_client_secret.json',
       scopes=SCOPES,
       redirect_uri='http://localhost')
   auth_url, _ = flow.authorization_url(
       access_type='offline', prompt='consent', code_challenge=None)
   ```
2. Usuário abre a URL, autoriza, o browser redireciona para `http://localhost/?code=4/0AX...`
3. Trocar o código DIRETO (sem code_verifier):
   ```bash
   curl -s -X POST https://oauth2.googleapis.com/token \
     -d code=4/0AX... \
     -d client_id=... \
     -d client_secret=... \
     -d redirect_uri=http://localhost \
     -d grant_type=authorization_code
   ```

## Pitfalls

- **O código é de USO ÚNICO.** Se a primeira troca falhar, o código queima e precisa gerar nova URL. NUNCA tentar trocar o mesmo código 2x (a segunda retorna `invalid_grant: Bad Request`).
- **`code_verifier` salvo em arquivo não persiste entre turnos** — o `flow` objeto (com `state`) se perde na compactação. Gerar a URL e trocar o código na MESMA sequência, ou usar `code_challenge=None` para eliminar a necessidade do verifier.
- **Token final usa chave `access_token`, não `token`** — quando trocado via curl direto, o JSON tem `access_token`, `refresh_token`, `expires_in`, `scope` (singular). A lib `google.oauth2.credentials.Credentials.from_authorized_user_file` espera `token`, `refresh_token`, `token_uri`, `client_id`, `client_secret`, `scopes`, `expiry`. Para usar a lib, converter o formato ou usar curl direto.
- **`redirect_uri` válido para client Web é `http://localhost`** (sem porta). `urn:ietf:wg:oauth:2.0:oob` só funciona para client "Desktop/native".

## Teste pós-token

```bash
# Listar 5 arquivos do Drive (confirma token vivo)
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://www.googleapis.com/drive/v3/files?pageSize=5"
```
