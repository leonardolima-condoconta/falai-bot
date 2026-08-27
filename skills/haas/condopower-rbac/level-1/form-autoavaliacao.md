# form.autoavaliacao — Level 1

## Pré-condições
- Usuário identificado via `access.verify`
- `level === 1`
- `colaborador_id` e `email` obtidos da verificação de identidade

## Fluxo

### 1. Validar identidade
```
O colaborador_id DEVE ser o id do próprio usuário que está falando.
NUNCA gerar HTML de autoavaliação para outro colaborador.
```

### 2. Gerar HTML de autoavaliação
```bash
cd /opt/data/convenia && /opt/data/.venv/bin/python3 gerar_form_avaliacao.py <email_do_usuario>
```

### 3. Retornar o link
```
Servir o link gerado (ex: https://static-server.aiexpert-condoconta.info/avaliacao-...)
```

### 4. Após submit (via fetch no HTML)
O HTML envia `form.autoavaliacao` direto para a API com:
- `colaborador_id`: UUID do próprio usuário
- `colaborador_email`: email do próprio usuário
- `colaborador_nome`: nome do próprio usuário
- `area`: departamento
- `perguntas`: { enunciado: resposta }

## Regras
- ❌ NUNCA gerar HTML para outro colaborador
- ❌ NUNCA aceitar email ou nome diferente do usuário autenticado
- O `colaborador_id` é IMPLÍCITO — sempre o id de quem está falando

## Gerador Python
- Script: `/opt/data/convenia/gerar_form_avaliacao.py`
- Uso: `python3 gerar_form_avaliacao.py <email>`