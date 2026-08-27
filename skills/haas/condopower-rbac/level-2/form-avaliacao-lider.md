# form.avaliacao_lider — Level 2

## Pré-condições
- Líder identificado via `access.verify`
- `level === 2` (ou superior)
- `reports[]` não vazio

## Fluxo

### 1. Validar liderados
```
O líder DEVE ter ao menos 1 liderado em reports[].
Se reports[] vazio → "Você não possui liderados diretos. A avaliação de liderança é apenas para quem lidera uma equipe."
```

### 2. Gerar HTML de avaliação do líder
```bash
cd /opt/data/convenia && /opt/data/.venv/bin/python3 gerar_form_lider.py <email_do_lider>
```

### 3. Retornar o link
```
Servir o link gerado.
```

### 4. Após submit (via fetch no HTML)
O HTML envia `form.avaliacao_lider` com:
- `lider_id`: UUID do líder
- `lider_email`: email do líder
- `colaborador_id`: UUID do liderado selecionado
- `colaborador_nome`: nome do liderado
- `area`: departamento do liderado
- `perguntas`: { enunciado: resposta }

### 5. Validação adicional
Antes de aceitar o submit, validar que o `colaborador_id` está em `reports[]`.
Se não estiver → "Este colaborador não está na sua equipe."

## Gerador Python
- Script: `/opt/data/convenia/gerar_form_lider.py`
- Uso: `python3 gerar_form_lider.py <email_lider>`