---
name: people-ops-automation
description: Standardized workflows for periodic People Ops tasks.
version: 1.1.0
---

# people-ops-automation — autonomous workflows for People Ops

## Purpose

Provides blueprints for agents running as scheduled cron jobs to handle recurring People processes like Pulse surveys, engagement tracking, and lifecycle automation.

## Core Workflow Pattern: Periodic Survey Reporting (e.g., Pulse)

When an agent is tasked with periodic reporting for a survey, follow this logic to ensure resource efficiency and proper lifecycle management:

### 1. Initialization & Auth
*   **Credentials:** Extract `CONDOPOWER_SA_TOKEN` and `CONDOPOWER_AUTH` from `/opt/data/.env`.
*   **Endpoint:** Use `https://webhook-proxy.condoconta.com.br/webhooks/condopower-api`.
*   **Headers:** Must include `X-Service-Account-Token` and `auth`.

### 2. Decision Tree (Branching on Status)

Call `pulse.round_status` first.

**A. If `aberta: true` (Tracking Mode):**
*   **Data Fetch:** Call `pulse.answers` to retrieve current responses.
*   **Aggregation:** Group responses by `area` (from `raw.area`) to show distribution.
*   **Message:** Format as "Acompanhamento diário" (Daily Tracking).
*   **Delivery:** Send via Slack DM to the designated stakeholder.
*   **Persistence:** The cron job MUST remain active.

**B. If `aberta: false` (Closing Mode):**
*   **Data Fetch:** Get final consolidated counts.
*   **Message:** Format as "RESULTADO FINAL" (Final Result) with a "Rodada encerrada" disclaimer.
*   **Cleanup (CRITICAL):** The agent must remove its own cron job to prevent infinite looping.
    *   **Technique:** Use the identifier in the crontab line.
    *   **Command:** `crontab -l | grep -v '<job_id>' | crontab -`
*   **Delivery:** Send the final report before the job is removed.

### 3. Error Handling & Resilience

*   **API Failures (5xx, Timeouts):** If the API is unreachable, do NOT remove the job. Report "API indisponível no momento — nova tentativa amanhã" (if possible) and exit. The next cron cycle will handle the retry.
*   **Auth Failures (401/403):** Log the error and stop. This requires manual intervention by the People team.

## Implementation Standards

*   **Dependencies:** Use `urllib` instead of `requests` for maximum compatibility in minimal container/cron environments.
*   **Cron Identifiers:** Always include a unique comment in the cron line (e.g., `# job_id: 413bb7dd1438`) to allow for surgical removal.
*   **Self-Cleaning:** An autonomous agent should always clean up its own schedule once its mission (the specific survey round) is complete.

## Evaluation Cycle Workflow (Líderes + Liderados)

When running a performance evaluation cycle (e.g., 2026.2), the full pipeline has 4 stages:

### 1. Extract Leader → Reports Mapping

Fetch all employees from Convenia API and build the hierarchy:

```python
from convenia import ConveniaClient
with ConveniaClient() as client:
    resp = client._client.get("/api/v3/employees", params={"per_page": 200})
    employees = resp.json()["data"]
```

Build `leaders` dict keyed by `supervisor.id`, collecting `name`, `email`, `job`, `department` for each report. Two edge cases: (a) supervisor may exist in the leader map but not in the employee list, and (b) some employees have no supervisor (`supervisor.id` is null).

### 2. Generate Leader Evaluation Forms en Masse

Use the **unified** form generator — one form per leader, with a dropdown of all their reports:

```bash
python3 /opt/data/convenia/gerar_form_lider.py <email_do_lider>
```

The script auto-publishes to the static server. Run for ALL leaders in batch (25 in 2026.2). Takes ~7 seconds total.

### 3. Generate Individual Slack Messages

Each leader gets a DM with:
- Greeting by name
- Form link
- List of their reports (name + job + department)
- Deadline (e.g., 31/08 + 4 days = 04/09/2026)
- Instructions on how the unified form works

Store in `/opt/data/mensagens_lideres_avaliacao_<ciclo>.md` and `.json` for review + dispatch.

### 4. Generate the Oversight Report

HTML report with all leaders, their reports, emails, and evaluation links. Uses `condoconta-design-system` for styling. Saved to `/opt/data/relatorio_lideres_<ciclo>.html`.

### 🔴 CRITICAL PITFALL — URL Slug Mismatch

**The `gerar_form_lider.py` script generates URLs from the EMAIL PREFIX, NOT the person's name:**

```python
# CORRECT — line 336 of gerar_form_lider.py:
slug = "avaliacao-lider-" + EMAIL.lower().split("@")[0].replace(".", "-")[:50]
# Example: franco.brognoli@condoconta.com.br → avaliacao-lider-franco-brognoli
```

When generating messages with form links, use the same logic:
```python
slug = email.lower().split("@")[0].replace(".", "-")[:50]
url = f"https://static-server.aiexpert-condoconta.info/avaliacao-lider-{slug}"
```

**NEVER** derive the slug from the person's full name (e.g., `"Franco Maiole Brognoli"` → `franco-maiole-brognoli` is WRONG). The published URL is `franco-brognoli` (email prefix only). Always cross-check generated URLs against the published ones before sending messages.

## Pitfalls

*   **Ignoring the 'aberta' flag:** Sending daily reports for a closed round wastes resources and confuses stakeholders.
*   **Not using the proxy:** Calling the direct `condopower-api` URL from a container will result in a 60s timeout. Always use the `webhook-proxy`.
*   **Removing the job too early:** Ensure the final report is successfully sent (or at least the attempt is logged) before executing the `crontab` removal command.
*   **URL slug mismatch in evaluation forms:** `gerar_form_lider.py` slugs are email-prefix-based, not name-based. Always verify generated URLs match published ones before sending messages with links. Use `email.split("@")[0].replace(".", "-")` — never name-based slug.
