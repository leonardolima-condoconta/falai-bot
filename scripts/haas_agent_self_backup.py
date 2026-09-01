#!/usr/bin/env python3
"""
haas_agent_self_backup.py — Script padronizado de auto-backup para agentes HaaS.

Cada agente roda isso via cron diário (dentro do container).
Salva SOUL.md, skills custom, profiles, configs em /opt/data/backup/
A Mirna coleta tudo no repo_sync diário → instances/{nome}/

Uso:
  python3 /opt/data/scripts/self_backup.py
"""

import os
import sys
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
DATA = Path("/opt/data")
BACKUP = DATA / "backup"

# Agentes conhecidos — cada um deve ter seu nome aqui
# Ou detecta automaticamente do hostname do container
AGENT_NAME = os.environ.get("HaaS_AGENT_NAME") or os.environ.get("HERMES_PROFILE") or "unknown"

def main():
    now = datetime.now(BRT).strftime("%Y-%m-%d %H:%M BRT")
    print(f"🔄 {AGENT_NAME} self-backup — {now}")

    # Limpa backup anterior
    if BACKUP.exists():
        shutil.rmtree(BACKUP)
    BACKUP.mkdir(parents=True, exist_ok=True)

    copied = []
    skipped = []

    # 1. SOUL.md
    for soul in [DATA / "SOUL.md", DATA / "profiles" / AGENT_NAME / "SOUL.md"]:
        if soul.exists():
            dest = BACKUP / ("SOUL.md" if soul.parent == DATA else f"SOUL_{soul.parent.name}.md")
            shutil.copy2(soul, dest)
            copied.append(str(soul))
            break

    # 2. config.yaml (sanitizado — sem secrets)
    config = DATA / "config.yaml"
    if config.exists():
        dest = BACKUP / "config.yaml"
        with open(config) as f:
            lines = f.readlines()
        with open(dest, "w") as f:
            for line in lines:
                # Redacta values de chaves sensíveis
                if any(k in line for k in ["OPENROUTER_API_KEY", "TELEGRAM_BOT_TOKEN",
                    "INFISICAL_TOKEN", "SLACK_BOT_TOKEN", "SLACK_USER_TOKEN",
                    "WHATSAPP_TOKEN", "GOOGLE_CLIENT_SECRET", "API_KEY", "SECRET"]):
                    f.write(line.split("=")[0] + "=***\n")
                else:
                    f.write(line)
        copied.append(str(config))

    # 3. Profiles (SOUL, MEMORY, USER)
    profiles_dir = DATA / "profiles"
    if profiles_dir.exists():
        for profile in profiles_dir.iterdir():
            if profile.is_dir():
                dest_dir = BACKUP / "profiles" / profile.name
                dest_dir.mkdir(parents=True, exist_ok=True)
                for f in profile.glob("*.md"):
                    shutil.copy2(f, dest_dir / f.name)
                    copied.append(str(f))
                # Cron jobs snapshot
                cron_json = profile / "cron" / "jobs.json"
                if cron_json.exists():
                    (dest_dir / "cron").mkdir(parents=True, exist_ok=True)
                    shutil.copy2(cron_json, dest_dir / "cron" / "jobs.json")
                    copied.append(str(cron_json))

    # 4. Skills custom (não bundled)
    skills_dir = DATA / "skills"
    if skills_dir.exists():
        # Skills que começam com categoria "productivity" ou "agents" geralmente são custom
        for category in ["productivity", "agents", "comms", "haas", "devops"]:
            cat_dir = skills_dir / category
            if cat_dir.exists():
                for skill in cat_dir.iterdir():
                    if skill.is_dir() and (skill / "SKILL.md").exists():
                        dest_dir = BACKUP / "skills" / category / skill.name
                        dest_dir.mkdir(parents=True, exist_ok=True)
                        for f in skill.rglob("*"):
                            if f.is_file() and not f.name.startswith("."):
                                rel = f.relative_to(skill)
                                (dest_dir / rel.parent).mkdir(parents=True, exist_ok=True)
                                shutil.copy2(f, dest_dir / rel)
                        copied.append(str(skill))

    # 5. Hooks custom
    hooks_dir = DATA / "hooks"
    if hooks_dir.exists():
        for hook in hooks_dir.iterdir():
            if hook.is_dir():
                dest_dir = BACKUP / "hooks" / hook.name
                dest_dir.mkdir(parents=True, exist_ok=True)
                for f in hook.rglob("*"):
                    if f.is_file():
                        shutil.copy2(f, dest_dir / f.relative_to(hook))
                copied.append(str(hook))

    # 6. .env.example (sanitizado)
    env_file = DATA / ".env"
    if env_file.exists():
        with open(env_file) as f:
            env_lines = f.readlines()
        with open(BACKUP / ".env.example", "w") as f:
            for line in env_lines:
                if line.strip() and not line.startswith("#"):
                    key = line.split("=")[0]
                    f.write(f"{key}=***\n")
        copied.append(".env → .env.example")

    # 7. README com metadados
    readme = BACKUP / "README.md"
    with open(readme, "w") as f:
        f.write(f"# {AGENT_NAME} — Auto-backup\n\n")
        f.write(f"Gerado: {now}\n\n")
        f.write(f"## Arquivos\n\n")
        for c in copied:
            f.write(f"- {c}\n")

    print(f"✅ {len(copied)} itens salvos em {BACKUP}")
    print(f"   Agente: {AGENT_NAME}")

if __name__ == "__main__":
    main()