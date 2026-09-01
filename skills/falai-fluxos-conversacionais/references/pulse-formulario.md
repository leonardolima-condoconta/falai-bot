# Pulse — Formulário HTML

## Arquivo
`/opt/data/formularios/form-pulse.html`

## Publicação
https://static-server.aiexpert-condoconta.info/pesquisa-pulses

## Estrutura

### Perguntas (conforme formulário original)
1. **Área** — dropdown (15 áreas: Banking Operations, Collection ExtraJudicial, ..., Sales)
2. **Liderança Direta** — dropdown (26 líderes)
3. **Sentimento pessoal** — botões com emoji + texto (😥 Muito Mal → 🤩 Muito Bem)
4. **Relação com liderança** — botões com emoji (😥 Muito Ruim → 🤩 Muito Boa)
5. **Sentimento do time** — botões com emoji (😥 Muito Ruim → 🤩 Muito Bom)
6. **IA ganhou tempo** — botões (😥 Não ajudou → 🤩 Ajudou muito)
7. **IA melhorou qualidade** — botões (😥 Não melhorou → 🤩 Melhorou muito)
8. **eNPS** — botões 0-10
9. **Motivo da nota** — textarea livre

### Dados enviados no submit
```json
{
  "method": "pulse.submit",
  "params": {
    "area": "People",
    "lideranca_direta": "Rodrigo Catarcione",
    "sentimento_pessoal": "4",
    "relacao_lideranca": "4",
    "sentimento_time": "5",
    "ia_ganho_tempo": "5",
    "ia_qualidade": "4",
    "enps": "9",
    "motivo_nota": "Time engajado"
  }
}
```

### Detalhes técnicos
- Botões de escala 1-5 usam `data-value` para enviar número (não texto) no JSON
- Botões eNPS enviam o número direto
- Header com banner (coração + ECG do Pulses) em base64, overlay navy reduzido para imagem ficar visível
- Anônimo: sem email, sem identificação

## Pitfalls
- **CORS:** `Content-Type: application/json` + headers customizados (X-Service-Account-Token, auth) → preflight → 302 → ERR_FAILED. Ver `references/cors-formularios.md`.
- **respondent_email é obrigatório:** `pulse.submit` exige `respondent_email` para controle de participação e bloqueio de duplicidade. Testado empiricamente (19/08/2026): sem email → `MISSING_PARAMS`. O formulário atual NÃO envia email.
- **form-urlencoded rejeitado:** API espera JSON, não form-urlencoded (`Input should be a valid dictionary`).
- **submit atual falha no navegador:** devido ao CORS. Sem proxy no mesmo domínio ou CORS liberado na API, o formulário não funciona no browser.