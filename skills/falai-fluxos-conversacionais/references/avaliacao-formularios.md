# Fluxo de Formulários de Avaliação — Ciclo 2026.2

## Arquivos

| Arquivo | Função |
|---|---|
| `/opt/data/convenia/autoavaliacao_perguntas.json` | 121 colaboradores, 968 perguntas |
| `/opt/data/convenia/avaliacao_lider_perguntas.json` | 120 colaboradores, 960 perguntas |
| `/opt/data/convenia/gerar_form_avaliacao.py` | Gera HTML + publica no static server |

## Uso

```bash
cd /opt/data/convenia && /opt/data/.venv/bin/python3 gerar_form_avaliacao.py <email> [auto|lider]
```

- `auto` = autoavaliação (colaborador se avalia)
- `lider` = avaliação do líder sobre o liderado

## Fluxo de atendimento

### CondoPower pede formulário
1. `access.verify` → email
2. `gerar_form_avaliacao.py <email> auto`
3. Retornar link do static server

### Líder pede formulário
1. `access.verify` → validar que é condo_leader
2. Perguntar: "Autoavaliação ou avaliação de liderado?"
3. Se autoavaliação → mesmo fluxo CondoPower
4. Se liderado → pedir nome/email do liderado
5. `gerar_form_avaliacao.py <email_liderado> lider`
6. Retornar link do static server

## HTML gerado
- Design system CondoConta (navy/gold)
- Perguntas com escala 1-5 (stars) e texto aberto
- Botão "Enviar Avaliação" com submit via fetch → condopower-api `/rpc`
- Tokens injetados no HTML (CONDOPOWER_SA_TOKEN + CONDOPOWER_AUTH)

## RBAC
- Levels 1-5 podem acessar autoavaliação
- Levels 2+ (condo_leader) podem acessar avaliação de liderado
- Level 1 (condopower) NÃO pode avaliar liderados