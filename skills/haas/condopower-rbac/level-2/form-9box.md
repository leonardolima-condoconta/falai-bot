# form.9box — Level 2

## Status
❌ **Gerador Python NÃO CRIADO**

O arquivo `/opt/data/convenia/gerar_form_9box.py` ainda não foi desenvolvido.

## Fluxo planejado

### Quando implementado:
1. Líder identificado via `access.verify`
2. Selecionar liderado da lista `reports[]`
3. Coletar: nota resultados (peso 50%), nota competências (peso 30%), nota potencial (peso 20%), recomendação
4. Enviar `form.9box` com `lider_id` + `colaborador_id` + campos do formulário

### Enquanto não implementado:
"O posicionamento no Nine Box ainda não está disponível via formulário. Por enquanto, posso registrar sua avaliação conversacionalmente — me conte as 3 notas (resultados, competências, potencial) que eu registro."

A coleta conversacional deve pedir:
- Nota de Resultados (1-5) — entrega nas atribuições atuais
- Nota de Competências (1-5) — comportamentais e técnicas
- Nota de Potencial (1-5) — prontidão para o próximo nível
- Recomendação: Promoção, Mérito, Bônus, Manter, PDI intensivo, PIP, Desligamento
- Comentários adicionais