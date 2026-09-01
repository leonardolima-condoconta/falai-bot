#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${STATIC_SERVER_URL:-https://webhook-proxy.condoconta.com.br/webhooks/static-server}"
file="${1:-}"; [ -n "$file" ] || { echo "uso: publish.sh <arquivo.html> [slug]" >&2; exit 2; }
[ -f "$file" ] || { echo "erro: arquivo não encontrado: $file" >&2; exit 1; }
case "$file" in *.html|*.htm) ;; *) echo "erro: só .html/.htm" >&2; exit 1;; esac
slug="${2:-}"; [ -z "$slug" ] && slug="$(basename "$file" | sed 's/\.[^.]*$//')"
slug=$(printf '%s' "$slug" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9-]+/-/g; s/-+/-/g; s/^-//; s/-$//' | cut -c1-64)
token="${STATIC_SERVER_SA_TOKEN:-}"; [ -n "$token" ] || { echo "erro: defina STATIC_SERVER_SA_TOKEN" >&2; exit 1; }
resp=$(curl -sS -w '%{http_code}' -X POST "$BASE_URL" -H 'accept: application/json' -H "X-Service-Account-Token: $token" -F "slug=$slug" -F "file=@${file};type=text/html")
code=$(printf '%s' "$resp" | tail -n1); body=$(printf '%s' "$resp" | sed '$d')
[ "$code" = "200" ] && printf '%s' "$body" | python3 -c 'import sys, json; print(json.load(sys.stdin)["url"])' || { echo "erro HTTP $code: $body" >&2; exit 1; }