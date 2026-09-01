# DM em massa para líderes — roteamento de alterações

⛔ **PITFALL CRÍTICO (28/08/2026):** O bot NUNCA deve dizer "me avise por aqui" em DMs para líderes. Líderes NÃO conseguem responder ao bot por DM — eles não estão no `SLACK_ALLOWED_USERS`. Toda alteração deve ser roteada para a pessoa do time de People que solicitou o envio.

## Como aconteceu

No lançamento do ciclo 2026.2, a DM original dizia "me avise por aqui que encaminho na hora". Luana Xavier (People) corrigiu: líderes não conseguem falar com a Falai por DM. Foi necessário reenviar 23 DMs de correção.

## Template correto (já com roteamento para People)

```
Olá, *{nome_curto}*! 👋

Na *segunda-feira, {data}*, daremos início ao ciclo de *Avaliação de Desempenho {ciclo}* da CondoConta. Os links individuais serão encaminhados no decorrer do dia.

Antes disso, peço que confira a lista de liderados que está cadastrada para você:

  {lista_numerada_de_liderados_com_cargo}

⚠️ *Se houver qualquer alteração* (liderado faltando, sobrando ou nome incorreto), envie diretamente para *{nome_people}* — é {pronome} quem está centralizando os ajustes.

Se estiver tudo certo, não precisa responder — na {dia_da_semana} você recebe os links! 🚀

*by Falai — People*
```

## Template de correção (quando a primeira DM errou o roteamento)

```
⚡ *Corrigindo:* se houver qualquer alteração na lista de liderados, envie diretamente para a *{nome_people}* (<@{slack_id}>). {pronome_cap} vai centralizar os ajustes e repassar para correção nos formulários.

Valeu! 🙏
```

## Regra geral

> **Sempre confirmar com o solicitante PARA QUEM os líderes devem enviar alterações.** Nunca assumir que é para o bot. O padrão seguro é rotear para a pessoa do time de People que pediu o envio.