# Git secrets cleanup — remover tokens do histórico

## Problema

GitHub Push Protection bloqueia pushes que contêm tokens hardcoded no histórico de commits.
O erro típico:

```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Push cannot contain secrets
remote:   —— Slack API Token —————————————————————————
remote:     locations:
remote:       - commit: 3133020...
remote:         path: convenia/cafe_ceo.py:8
```

## Solução: `git filter-branch`

### Passo 1 — Remover o arquivo de TODOS os commits
```bash
git filter-branch --force \
  --index-filter 'git rm --cached --ignore-unmatch <caminho/do/arquivo>' \
  --prune-empty -- --all
```

### Passo 2 — Corrigir o arquivo localmente (remover o token)
```bash
sed -i 's|return "xoxb-.*TOKEN"|return os.environ.get("SLACK_BOT_TOKEN", "")|' <arquivo>
```

### Passo 3 — Recomitar e push
```bash
git add <arquivo> && git commit -m "fix: remover token hardcoded" && git push --force
```

## Pitfalls

- `git filter-branch` exige working tree limpo (`git stash` antes se necessário)
- Rewrite branches com `--force` para sobrescrever o histórico
- Push precisa de `--force` porque o histórico foi reescrito
- Verificar outros arquivos com `grep -rn "xoxb-\|ghp_\|sk-"` depois

## Pré-requisito: `.gitignore`

O `.gitignore` deve excluir `.env`, `google_token.json`, `auth.json` e todos os arquivos
de credenciais ANTES do primeiro commit. Se o primeiro commit já subiu com token, usar
`filter-branch` para limpar.