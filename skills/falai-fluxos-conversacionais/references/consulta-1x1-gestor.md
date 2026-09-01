# Consulta: "quem é meu gestor" / "quando é meu 1x1"

Perguntas frequentes de colaboradores que exigem cruzar API + SQLite + Calendar.
A API sozinha NÃO responde — veja por quê abaixo.

## Por que a API não basta

`access.verify` retorna `employee.id` (UUID), `department`, `reports[]` (liderados),
mas **NÃO retorna `supervisor_id`**. Para saber QUEM LIDERA a pessoa, só SQLite.

## Passo a passo

1. `access.verify` (Slack ID) → `employee.id` (UUID) + `email` + `department` + `full_name`.
2. Achar o gestor no SQLite (backup mais recente):
   ```sql
   SELECT s.name, s.last_name, s.email, s.job_id
   FROM employees e JOIN employees s ON e.supervisor_id = s.id
   WHERE e.id = '<UUID>';
   ```
   DB vivo `/opt/data/convenia_data/convenia.db` está VAZIO (0 bytes).
   Usar `/opt/data/convenia_data/backups/convenia_YYYY-MM-DD.db` (o mais recente).
3. Ver se já existe 1x1 registrado / próximo agendado:
   ```sql
   SELECT data, proximo_1x1, energia, motivacao, pauta_liderado
   FROM registro_1x1 WHERE colaborador_id = '<UUID>' ORDER BY data DESC;
   ```
   `proximo_1x1` = data do próximo 1x1, se o líder registrou.
4. Buscar no Calendar (se o SQLite não tiver):
   - O 1x1 NÃO fica no calendário People (`people@condoconta.com.br`) — esse só tem
     eventos corporativos (CondoCoffee, onboarding, all-hands, datas comemorativas).
   - `agendar_reunioes.py` cria 1x1 no `calendars/primary` do líder/colaborador,
     com summary `1x1: {lider} ↔ {colab}`.
   - Para achar o 1x1 de alguém, consulte o calendário primário DA PESSOA ou DO
     GESTOR, filtrando summary que contenha `1x1` ou o nome.

## Google Calendar — acesso sem googleapiclient

O pacote `googleapiclient` NÃO está instalado no container. Usar `urllib` puro:

- Token: `/opt/data/google_token.json` (chaves `token` + `refresh_token`;
  `client_id`/`client_secret` dentro do próprio arquivo).
- Refresh:
  ```python
  import json, urllib.request, urllib.parse
  tok = json.load(open('/opt/data/google_token.json'))
  data = urllib.parse.urlencode({'client_id': tok['client_id'],
      'client_secret': tok['client_secret'],
      'refresh_token': tok['refresh_token'], 'grant_type': 'refresh_token'}).encode()
  access = json.loads(urllib.request.urlopen(urllib.request.Request(
      'https://oauth2.googleapis.com/token', data=data), timeout=30).read())['access_token']
  ```
- Listar eventos do People calendar (primary = `people@condoconta.com.br`):
  ```
  GET https://www.googleapis.com/calendar/v3/calendars/people%40condoconta.com.br/events?timeMin=...&timeMax=...&singleEvents=true&orderBy=startTime&maxResults=250
  ```
- Descobrir todos os calendários acessíveis: `GET .../users/me/calendarList`.

## Pitfalls

- O token do `people@condoconta.com.br` NÃO alcança os calendários primários
  individuais dos colaboradores (cada 1x1 fica no primary de cada um). Se o SQLite
  não tem `proximo_1x1` e o People calendar não tem o evento, o 1x1 provavelmente
  está no primary do gestor — fora do alcance do token. Nesse caso: responder que
  não há 1x1 agendado no sistema e orientar a combinar com o gestor.
- `registro_1x1` pode estar vazio para a pessoa (1x1 ainda nunca registrado) —
  resposta válida, não erro.
- `email` e `slack_user_id` podem vir nulos; buscar por nome (`LIKE`) se o email falhar.
