# CondoConta OAuth Client — Mirna Admin Use

## The Two GCP Projects

CondoConta uses **two** Google Cloud projects with separate OAuth clients:

| Project | Client ID | Use Case |
|---------|-----------|----------|
| `hermes-gateway` | `269564140127-mgculbt35urfs2248oskp55b7dsr1oas` | HaaS agents (Google OAuth onboarding flow) |
| `condoconta` (764640240643) | `764640240643-7c7t0pomj4jjmh441glh3d16eo0ih9h1` | Mirna (admin agent, native) |

## The 403 PERMISSION_DENIED Trap

**Symptom:** Token has all correct scopes (including `spreadsheets`, `drive`, etc.) but Sheets API returns `403 PERMISSION_DENIED`.

**Root cause:** Token was issued by the **wrong GCP client**. The Hermes Desktop client (`269564140127-...`) can never access resources that belong to the CondoConta project — even with identical scopes and the same user authorizing both.

**Fix:** Re-authenticate with the CondoConta client (`764640240643-7c7t0pomj...`).

## Mirna Admin PKCE Flow

When Mirna needs to re-authenticate with the CondoConta client:

### Step 1 — Save PKCE verifier FIRST

```bash
python3 -c "
import json, hashlib, base64, secrets, os
verifier = secrets.token_urlsafe(32)
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
pkce_path = os.path.expanduser('~/.hermes/google_tokens/pkce_condoconta.json')
with open(pkce_path, 'w') as f:
    json.dump({'code_verifier': verifier, 'code_challenge': challenge}, f)
print('Saved:', pkce_path)
"
```

### Step 2 — Build auth URL

```
client_id = "764640240643-7c7t0pomj4jjmh441glh3d16eo0ih9h1"
client_secret = from Caju (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)
scopes = gmail.readonly, gmail.send, gmail.modify, calendar, drive.readonly,
         drive.file, contacts.readonly, spreadsheets, documents.readonly,
         presentations, chat.spaces, chat.spaces.readonly, chat.messages,
         chat.messages.readonly, chat.memberships, chat.memberships.readonly
redirect_uri = http://localhost:1
access_type = offline
prompt = consent
```

### Step 3 — Exchange code for tokens

Use the saved `pkce_condoconta.json` verifier + `client_secret` from Caju.

### Step 4 — Save to BOTH locations

```python
paths = [
    '~/.hermes/google_tokens/condoconta_token.json',
    '~/.hermes/google_tokens/google_token.json'
]
```

## Credential Sources

- **CondoConta client_secret:** Ask Caju directly. NOT in Infisical (Mirna is native, doesn't use Infisical client).
- **Hermes Desktop client_secret:** `~/.hermes/mirna-hermes-repo/projects/haas/shared/google_client_secret.json`

## Quick Reference

```
CondoConta project ID: 764640240643
CondoConta client_id: 764640240643-7c7t0pomj4jjmh441glh3d16eo0ih9h1
CondoConta client_secret: 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
Hermes Desktop client_id: 269564140127-mgculbt35urfs2248oskp55b7dsr1oas
Hermes Desktop client_secret: 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
```