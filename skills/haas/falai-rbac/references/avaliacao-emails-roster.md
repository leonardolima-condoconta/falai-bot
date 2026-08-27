# E-mails corretos e roster — geração de formulários de avaliação

## Problema

Os JSONs de avaliação **não têm e-mail** — o campo `email` de todo colaborador em
`autoavaliacao_perguntas.json` e `avaliacao_lider_perguntas.json` vem `null`:

```
"nome": "Luana Beatris Xavier",
"email": null,   ← SEMPRE null
"cargo": "People Business Partner",
```

Mas `gerar_form_avaliacao.py <email>` e `gerar_form_lider.py <email>` **precisam do
e-mail correto**: ele vira o campo oculto `colaborador_email` do HTML e é usado
client-side no `access.verify` (via `/proxy/condopower-rpc`) para resolver o UUID.
E-mail errado ⇒ o formulário abre mas não resolve o `colaborador_id` ⇒ submit falha
com `MISSING_PARAMS`.

## De onde sai o e-mail correto

**NÃO adivinhar `firstname.lastname@condoconta.com.br`** — os e-mails reais são
encurtados. A fonte é o SQLite de backup (`employees.email`):

```
/opt/data/convenia_data/backups/convenia_*.db  (usar o mais recente)
SELECT name, last_name, email FROM employees WHERE email IS NOT NULL;
```

O `access.verify` também devolve o e-mail certo, mas quando a API está fora de
alcance do container (o caso atual), o SQLite é o fallback que funciona.

## Roster do time People (conferido 25/08/2026)

| Colaborador(a) | Cargo | E-mail (SQLite) |
|---|---|---|
| Amanda Elena de Almeida | Analista de Employer Branding & Endomarketing | `amanda.almeida@condoconta.com.br` |
| Ana Paula de Britto Sosa | Analista Administrativo de People | `ana.britto@condoconta.com.br` |
| Luana Beatrís Xavier | People Business Partner | `luana.xavier@condoconta.com.br` |
| Schaiane da Cruz | (People) | **`email` = null no banco** |

⚠️ **Disambiguation:** existe outra "Ana Paula" — `Ana Paula Bunn`
(`ana.bunn@condoconta.com.br`, depto **Relacionamento**, gestora Renata Otacilio).
Não confundir com Ana Paula de Britto Sosa (People).

## Gap conhecido do JSON de autoavaliação

O JSON `autoavaliacao_perguntas.json` (área "People") tem **3** colaboradores
(Amanda, Ana Paula de Britto, Luana). O banco tem **4** no time People — **Schaiane
da Cruz está fora do JSON** (e tem `email` null no banco). Antes de gerar o formulário
do time inteiro, comparar JSON vs SQLite (`SELECT ... WHERE department_id = (SELECT id
FROM departments WHERE name='People')`) e avisar o solicitante de quem ficou de fora.

## Fluxo — líder quer revisar o formulário do time inteiro

1. `access.verify` do líder (ou SQLite) → lista de `reports[]`.
2. Para **cada** liderado, achar o e-mail correto (SQLite `employees.email`).
3. Rodar uma vez por e-mail: `python3 /opt/data/convenia/gerar_form_avaliacao.py <email>`.
4. Devolver a lista de links + lembrete de VPN 🔐 + avisar dos liderados que faltam no JSON.
