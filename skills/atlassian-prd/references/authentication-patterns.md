# Autenticacao Jira/Confluence
Basic auth: email + API token (gerado em https://id.atlassian.com/manage-profile/security/api-tokens).
Header: Authorization: Basic base64(email:token).
OAuth 2.0 (3LO): para apps distribuidos. Client ID + Secret → authorization code → access token.
NUNCA hardcodar tokens. Usar .env (JIRA_API_TOKEN, JIRA_EMAIL, JIRA_DOMAIN).