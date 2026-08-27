# pulse.reopen — Level 4

## ⚠️ ATENÇÃO — Método crítico

Este método REABRE uma rodada de clima já encerrada, estendendo seu prazo.
**Isso pode alterar dados já consolidados da pesquisa.**

Antes de executar, você DEVE informar o usuário:

```
⚠️ *ATENÇÃO — Reabertura de Pesquisa de Clima*

Você está prestes a REABRIR uma rodada de clima já encerrada.
Isso significa que:
1. O prazo da pesquisa será estendido
2. Novas respostas poderão ser enviadas
3. Os números de adesão e eNPS poderão MUDAR
4. Respostas recebidas na extensão serão incluídas na mesma rodada

Tem certeza que deseja continuar?
```

Só prossiga se o usuário confirmar EXPLICITAMENTE.

## Pré-condições
- Usuário level 4+ (`admin` ou `superadmin`)
- Rodada deve estar ENCERRADA (`ROUND_NOT_CLOSED` se estiver aberta)
- `requester_email` = email do usuário autenticado

## Fluxo

### 1. Coletar parâmetros DE UMA VEZ
```
Para reabrir a rodada, preciso de:
- Ano (ex: 2026)
- Mês (ex: 7)
- Nova data de fim (ex: 2026-08-15)
```

### 2. Confirmar criticidade (ver acima)

### 3. Enviar para API
```json
{
  "method": "pulse.reopen",
  "params": {
    "requester_email": "<email>",
    "ano": 2026,
    "mes": 7,
    "fim": "2026-08-15"
  }
}
```

### 4. Confirmar ao usuário
```
✅ Rodada 2026-07 reaberta!
- Novo prazo final: 2026-08-15
- A pesquisa aceitará novas respostas até esta data.
```