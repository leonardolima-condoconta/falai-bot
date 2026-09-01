# Publicacao no ClickUp
Usar API ClickUp via REST. Description em plain text. Formato ALL CAPS + emojis + • bullets.
Rate limit: 100 req/min. Usar sleep(1) entre chamadas.
POST /list/{list_id}/task → criar Epic/Task.
parent=epic_id para filhos.