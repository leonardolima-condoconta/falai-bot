# SQLite ainda é necessário — supervisor_id e 1x1

⚠️ Correção da seção "Banco de Dados" do SKILL.md, que dizia que consultas SQLite
estavam "DESCONTINUADAS". Isso é impreciso: a API `condopower-api` NÃO cobre tudo.

## O que a API NÃO devolve

- `access.verify` retorna `employee` (id, full_name, email, slack_user_id, job,
  department), `level`, `role`, `is_active` e `reports[]` (quem a pessoa LIDERA).
- **NÃO retorna `supervisor_id`** — não há como saber QUEM LIDERA a pessoa pela API.
  Para isso, só SQLite: `employees.supervisor_id`.

## Onde estão os dados (IMPORTANTE)

- `/opt/data/convenia_data/convenia.db` — o arquivo vivo está **VAZIO (0 bytes)**.
- Os dados reais estão nos backups: `/opt/data/convenia_data/backups/convenia_YYYY-MM-DD.db`.
- Use o backup mais recente: `ls -t /opt/data/convenia_data/backups/convenia_*.db | head -1`.

## Tabelas úteis

- `employees`: `id` (UUID Convenia = o que `access.verify` retorna como `employee.id`),
  `name`, `last_name`, `email`, `job_id`, `department_id`, `supervisor_id`,
  `is_active`, `hiring_date`, `birth_date`.
- `jobs`: `id`, `name` (para resolver o cargo do gestor/colaborador).
- `registro_1x1`: `id`, `data` (último 1x1), `colaborador_id`, `lider_id`,
  `energia`, `motivacao`, `pauta_liderado`, `proximo_1x1` (próximo agendado).

## Achar o gestor de alguém

```sql
SELECT s.name, s.last_name, s.email, s.job_id
FROM employees e JOIN employees s ON e.supervisor_id = s.id
WHERE e.id = '<UUID_DO_ACCESS_VERIFY>';
```

## Responder "quando é meu 1x1"

```sql
SELECT data, proximo_1x1 FROM registro_1x1
WHERE colaborador_id = '<UUID>' ORDER BY data DESC LIMIT 5;
```

- `proximo_1x1` preenchido = próxima data.
- Sem registro = 1x1 ainda nunca registrado (resposta válida, não erro).

Fluxo completo (incluindo busca no Google Calendar) em:
`falai-fluxos-conversacionais` → `references/consulta-1x1-gestor.md`.
