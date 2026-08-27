# form.pulse — Level 1

## Pré-condições
- Usuário identificado via `access.verify`
- `level === 1`
- `PULSE_PATH_USERS` definido no ambiente

## Fluxo

### 1. Verificar se o usuário já respondeu
```
Ler $PULSE_PATH_USERS (CSV: id_usuario, respondido, created_at)
Se o id_usuario consta E respondido = true →
  "Você já respondeu a pesquisa deste mês. A pesquisa é anônima — obrigado pela participação!"
  FIM.
```

### 2. Servir o formulário
```
Gerar link: https://static-server.aiexpert-condoconta.info/pesquisa-pulses
```

### 3. Após submit (via fetch no HTML)
O HTML do pesquisa-pulses envia `form.pulse` direto para a API.
Quando a resposta chegar (o agente NÃO precisa interceptar — o HTML faz o POST direto):

### 4. Registrar no CSV temporário
```bash
python3 /opt/data/convenia/pulse_csv.py register <id_usuario>
```
O script `pulse_csv.py`:
- Abre `$PULSE_PATH_USERS`
- Adiciona linha: `<id_usuario>,true,<ISO timestamp>`
- Se o arquivo não existe, cria com header: `id_usuario,respondido,created_at`

## Regras
- NUNCA associar resposta ao usuário (anonimato)
- O CSV registra apenas PARTICIPAÇÃO, não conteúdo da resposta
- Se `$PULSE_PATH_USERS` não está definido → erro: "Pesquisa não está aberta no momento"

## Gerador HTML
- Arquivo estático: `/opt/data/formularios/form-pulse.html`
- Publicado em: `https://static-server.aiexpert-condoconta.info/pesquisa-pulses`