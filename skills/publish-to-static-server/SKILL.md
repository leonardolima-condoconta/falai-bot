---
name: publish-report
description: Publish HTML to static-server.aiexpert-condoconta.info.
---

# Publish to static-server

## Steps
1. Write HTML to a `.html` file
2. Token: `STATIC_SERVER_SA_TOKEN` from .env
3. Run: `STATIC_SERVER_SA_TOKEN='<token>' bash scripts/publish.sh path/to/page.html [slug]`
4. URL: `https://static-server.aiexpert-condoconta.info/{slug}` (expires 7 days)

## Errors
- 400: invalid slug/file type
- 401: token mismatch
- 403: service account inactive