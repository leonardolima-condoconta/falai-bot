# Queries Jira (JQL)
project = <KEY> AND sprint in openSprints() ORDER BY priority DESC
project = <KEY> AND status = "Pronto" AND sprint IS EMPTY
project = <KEY> AND issuetype = Epic AND status != Concluido
project = <KEY> AND issuetype = Bug AND resolution IS EMPTY
project = <KEY> AND labels IN (N4, N5) ORDER BY created DESC
Sempre validar com maxResults=1 antes de lote.