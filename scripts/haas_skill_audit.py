#!/usr/bin/env python3
"""Cron semanal: verifica se todos agentes HaaS têm todos os DEFAULT_SKILLS.
Executa via cronjob no host Mirna. Reporta gaps no output.
"""

import subprocess, sys
from pathlib import Path

# ── DEFAULT_SKILLS (espelhado de haas_deploy.py) ──
DEFAULT_SKILLS = [
    "productivity/confluence-search",
    "productivity/jira",
    "productivity/hubspot",
    "productivity/databricks",
    "productivity/condoconta-design-system",
    "productivity/gamma-presentations",
    "productivity/powerpoint",
    "creative/infographic-generator",
    "creative/image-gen-openrouter",
    "productivity/data-viz",
    "productivity/pdf-generator",
    "productivity/document-parse",
    "productivity/nano-pdf",
    "productivity/ocr-and-documents",
    "productivity/cnpj-lookup",
    "google-maps-api",
    "productivity/brazilian-holidays",
    "productivity/aix-label-classifier",
    "productivity/jira-issue-manager",
    "productivity/prd-creation",
    "productivity/slack-messaging",
    "productivity/slack-block-kit-messaging",
    "productivity/google-workspace",
    "devops/haas-infisical-secrets-client",
    "productivity/kanban-task-tracking",
    "devops/gateway-session-persist",
    "creative/humanizer",
    "productivity/llm-model-guide",
    "productivity/daily-plan",
    "productivity/meeting-followups",
    "haas/haas-onboarding",
]

AGENTS = ["eva", "della", "sebastiao", "rod"]

def docker_exec(agent, cmd):
    r = subprocess.run(
        f"docker exec haas-{agent}-agent sh -c '{cmd}'",
        shell=True, capture_output=True, text=True, timeout=30
    )
    return r.stdout.strip()

def main():
    total_gaps = 0
    lines = []

    for agent in AGENTS:
        missing = []
        for skill in DEFAULT_SKILLS:
            path = f"/opt/data/skills/{skill}/SKILL.md"
            out = docker_exec(agent, f"test -f {path} && echo ok || echo missing")
            if out != "ok":
                missing.append(skill)

        if missing:
            total_gaps += len(missing)
            lines.append(f"\n🔴 {agent.upper()}: {len(missing)} skills ausentes")
            for s in missing:
                lines.append(f"   ❌ {s}")

    if total_gaps == 0:
        # Silencioso quando OK — nada de "tudo OK" nos canais
        return 0
    else:
        lines.insert(0, f"⚠️  {total_gaps} gaps de skills encontrados nos agentes HaaS.")
        print("\n".join(lines))
        return 1

if __name__ == "__main__":
    sys.exit(main())
