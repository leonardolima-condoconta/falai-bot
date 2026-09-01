#!/usr/bin/env python3
"""Pos-update fix: restaura skills + configs apos 'hermes update' ou pull de imagem.
Usa docker exec/cp (sem acesso direto ao filesystem — evita permission denied).

Uso: python3 ~/.hermes/scripts/haas_post_update_fix.py --all
      python3 ~/.hermes/scripts/haas_post_update_fix.py --agent eva
"""

import subprocess, sys, time, argparse
from pathlib import Path

SHARED_SKILLS = Path("/home/hermes/.hermes/skills")
AGENTS = ["eva", "della", "sebastiao", "rod"]

GOLDEN_VOICE = {
    "sebastiao": "pt-BR-AntonioNeural",
    "default": "pt-BR-FranciscaNeural",
}

DEFAULT_SKILLS = [
    "productivity/confluence-search", "productivity/jira", "productivity/hubspot",
    "productivity/databricks", "productivity/condoconta-design-system",
    "productivity/gamma-presentations", "productivity/powerpoint",
    "creative/infographic-generator", "creative/image-gen-openrouter",
    "productivity/data-viz", "productivity/pdf-generator",
    "productivity/document-parse", "productivity/nano-pdf",
    "productivity/ocr-and-documents", "productivity/cnpj-lookup",
    "google-maps-api", "productivity/brazilian-holidays",
    "productivity/aix-label-classifier", "productivity/jira-issue-manager",
    "productivity/prd-creation", "productivity/slack-messaging",
    "productivity/slack-block-kit-messaging", "productivity/google-workspace",
    "devops/haas-infisical-secrets-client", "productivity/kanban-task-tracking",
    "devops/gateway-session-persist", "creative/humanizer",
    "productivity/llm-model-guide", "github/github",
    "productivity/daily-plan", "productivity/meeting-followups",
    "haas/haas-onboarding",
    "haas/whatsapp-onboarding",
    "haas/google-oauth-onboarding",
]

def run(cmd, timeout=30):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)

def docker(agent, cmd):
    """Executa comando dentro do container."""
    return run(f"docker exec haas-{agent}-agent sh -c '{cmd}'")

def info(msg):    print(f"  \033[36m{msg}\033[0m")
def ok(msg):      print(f"  \033[32m✓ {msg}\033[0m")
def warn(msg):    print(f"  \033[33m⚠ {msg}\033[0m")
def err(msg):     print(f"  \033[31m✗ {msg}\033[0m")

def fix_skills(agent):
    """Restaura DEFAULT_SKILLS usando docker cp."""
    restored, present = 0, 0
    for skill in DEFAULT_SKILLS:
        # Check inside container
        r = docker(agent, f"test -f /opt/data/skills/{skill}/SKILL.md && echo ok || echo missing")
        if r.stdout.strip() == "ok":
            present += 1
            continue
        
        # Copy from shared to container
        src = SHARED_SKILLS / skill
        if not src.exists():
            warn(f"  Fonte ausente no shared: {skill}")
            continue
        
        r2 = run(f"docker cp {src} haas-{agent}-agent:/opt/data/skills/{skill}")
        if r2.returncode == 0:
            restored += 1
    
    return restored, present

def fix_config(agent):
    """Corrige config.yaml via docker exec + sed."""
    voice = GOLDEN_VOICE.get(agent, GOLDEN_VOICE["default"])
    changes = []
    
    # Check TTS voice
    r = docker(agent, f"grep 'voice: {voice}' /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append(f"TTS→{voice}")
        docker(agent, f"sed -i 's/voice: .*/voice: {voice}/' /opt/data/config.yaml 2>/dev/null || echo 'TTS fix skip'")
    
    # Check STT model
    r = docker(agent, "grep 'model: small' /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("STT model→small")
        docker(agent, "sed -i 's/model: base/model: small/' /opt/data/config.yaml 2>/dev/null || echo 'STT fix skip'")
    
    # Check STT language
    r = docker(agent, "grep 'language: pt' /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("STT language→pt")
        docker(agent, "sed -i '/model: small/a\\    language: pt' /opt/data/config.yaml 2>/dev/null || echo 'lang fix skip'")
    
    # Check voice beep
    r = docker(agent, "grep 'beep_enabled: true' /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("beep→true")
        docker(agent, "sed -i 's/beep_enabled: false/beep_enabled: true/' /opt/data/config.yaml 2>/dev/null || echo 'beep fix skip'")
    
    # Check tool_progress: off (nunca 'none')
    r = docker(agent, "grep 'tool_progress: off' /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("tool_progress→off")
        docker(agent, "sed -i 's/tool_progress: none/tool_progress: off/' /opt/data/config.yaml 2>/dev/null || echo 'tool_progress fix skip'")
    
    # Check WhatsApp mention_patterns
    r = docker(agent, "grep \"mention_patterns: '(?i)@?\" /opt/data/config.yaml 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("mention_patterns")
        docker(agent, "sed -i 's/mention_patterns:.*/mention_patterns: (''\\\"(?i)@?\\\\\\\\bmirna\\\\\\\\b\\\"'')/' /opt/data/config.yaml 2>/dev/null || echo 'mention fix skip'")
    
    return changes

def fix_whatsapp_bridge(agent):
    """Corrige bridge.js do WhatsApp: faster_whisper + initial_prompt."""
    changes = []
    
    # 1. Install faster_whisper system-wide (survives hermes update)
    r = docker(agent, "python3 -c 'from faster_whisper import WhisperModel; print(\"ok\")' 2>/dev/null || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("faster-whisper")
        docker(agent, "pip3 install --break-system-packages faster-whisper 2>&1 | tail -1")
    
    # 2. Patch bridge.js: venv python + initial_prompt
    bridge_path = "/home/hermes/.local/lib/python3.12/site-packages/scripts/whatsapp-bridge/bridge.js"
    r = docker(agent, f"grep 'initial_prompt' {bridge_path} 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("bridge.js-prompt")
        docker(agent, f"sed -i \"s/language='pt')/language='pt', initial_prompt='Agent CC, Caju, CondoConta')/\" {bridge_path} 2>/dev/null || echo 'bridge prompt fix skip'")
    
    # 3. Patch bridge.js: usar venv python (nao system)
    r = docker(agent, f"grep 'venv.*bin.*python3' {bridge_path} 2>/dev/null && echo ok || echo missing")
    if r.stdout.strip() != "ok":
        changes.append("bridge.js-venv")
        docker(agent, f"sed -i \"s|execFileAsync('python3'|execFileAsync(path.join(process.env.HOME, '.hermes', 'venv', 'bin', 'python3')|g\" {bridge_path} 2>/dev/null || echo 'bridge venv fix skip'")
    
    return changes

def restart(agent):
    """Reinicia e aguarda health check."""
    run(f"docker restart haas-{agent}-agent")
    time.sleep(2)
    for _ in range(15):
        r = docker(agent, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8642/health 2>/dev/null || echo 000")
        if r.stdout.strip() == "200":
            return True
        time.sleep(2)
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    
    targets = AGENTS if args.all else ([args.agent] if args.agent else None)
    if not targets:
        print("Use --agent <nome> ou --all")
        sys.exit(1)
    
    any_change = False
    
    for agent in targets:
        print(f"\n{'='*50}")
        print(f"🔧 {agent.upper()}")
        print(f"{'='*50}")
        
        # 1. Skills
        info("Skills...")
        restored, present = fix_skills(agent)
        if restored > 0:
            warn(f"  {restored} skills restaurados ({present} ja OK)")
            any_change = True
        else:
            ok(f"  {present}/{len(DEFAULT_SKILLS)} OK")
        
        # 2. Config
        info("Config (TTS/STT/Voice)...")
        changes = fix_config(agent)
        
        # 3. WhatsApp Bridge
        info("WhatsApp Bridge...")
        w_changes = fix_whatsapp_bridge(agent)
        if w_changes:
            changes.extend(w_changes)
            warn(f"  Bridge corrigido: {', '.join(w_changes)}")
        else:
            ok("  Bridge OK")
        
        if changes:
            warn(f"  Corrigido: {', '.join(changes)}")
            any_change = True
        else:
            ok("  Golden config OK")
        
        # 3. Restart
        if any_change and (restored > 0 or changes):
            info("Reiniciando container...")
            if restart(agent):
                ok("  Container saudavel")
            else:
                err("  Timeout health check — verificar manualmente")
        else:
            info("  Sem mudancas — sem restart")
    
    print(f"\n{'='*50}")
    if any_change:
        warn("Post-update fix concluido COM correcoes.")
    else:
        ok("Post-update fix concluido — tudo em ordem.")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()