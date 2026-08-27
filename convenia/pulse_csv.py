#!/usr/bin/env python3
"""
Gerenciador de CSV temporario de participacao do Pulse.
Uso:
  python3 pulses_csv.py create                  → cria CSV vazio, define $PULSE_PATH_USERS
  python3 pulses_csv.py register <id_usuario>   → adiciona linha ao CSV
  python3 pulses_csv.py check <id_usuario>      → verifica se usuario ja respondeu
  python3 pulses_csv.py export-and-clean        → envia CSV no Slack #people-hr, exclui arquivo
"""
import csv, os, sys, json, subprocess
from datetime import datetime

PULSE_PATH = os.environ.get("PULSE_PATH_USERS", "")
PULSE_DIR = "/opt/data/convenia_data/pulse"

# Fallback: ler do .env se a env var nao estiver setada no processo
if not PULSE_PATH:
    try:
        with open("/opt/data/.env") as f:
            for line in f:
                if line.startswith("PULSE_PATH_USERS="):
                    PULSE_PATH = line.strip().split("=", 1)[1].strip('"').strip("'")
                    os.environ["PULSE_PATH_USERS"] = PULSE_PATH
                    break
    except:
        pass

def create():
    if PULSE_PATH and os.path.exists(PULSE_PATH):
        print(f"ERRO: CSV ja existe em {PULSE_PATH}")
        sys.exit(1)

    os.makedirs(PULSE_DIR, exist_ok=True)
    path = os.path.join(PULSE_DIR, f"pulses_{datetime.now():%Y-%m}.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id_usuario", "respondido", "created_at"])

    # Set env var
    with open("/opt/data/.env", "a") as f:
        f.write(f"\nPULSE_PATH_USERS={path}\n")

    os.environ["PULSE_PATH_USERS"] = path
    print(f"PULSE_PATH_USERS={path}")


def register(id_usuario):
    if not PULSE_PATH or not os.path.exists(PULSE_PATH):
        print("ERRO: $PULSE_PATH_USERS nao definido ou arquivo nao encontrado")
        sys.exit(1)

    # Check if already exists
    with open(PULSE_PATH, "r") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if row and row[0] == id_usuario and row[1] == "true":
                print("JA_RESPONDEU")
                return

    with open(PULSE_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([id_usuario, "true", datetime.now().isoformat()])
    print("REGISTERED")


def check(id_usuario):
    if not PULSE_PATH or not os.path.exists(PULSE_PATH):
        print("NOT_OPEN")
        sys.exit(1)

    with open(PULSE_PATH, "r") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row and row[0] == id_usuario and row[1] == "true":
                print("TRUE")
                return
    print("FALSE")


def export_and_clean():
    if not PULSE_PATH or not os.path.exists(PULSE_PATH):
        print("ERRO: $PULSE_PATH_USERS nao definido ou arquivo nao encontrado")
        sys.exit(1)

    # Upload to Slack
    token = ""
    with open("/opt/data/.env") as f:
        for line in f:
            if line.startswith("SLACK_BOT_TOKEN="):
                token = line.strip().split("=", 1)[1].strip('"').strip("'")

    if token:
        r = subprocess.run([
            "curl", "-s", "-X", "POST", "https://slack.com/api/files.upload",
            "-H", f"Authorization: Bearer {token}",
            "-F", f"file=@{PULSE_PATH}",
            "-F", "channels=C0BJLA3H16F",
            "-F", "title=Pulses Participacao",
            "-F", "initial_comment=📊 *Pulses encerrado!* Arquivo de participação anexo."
        ], capture_output=True, text=True, timeout=30)
        print(f"SLACK: {r.stdout[:100]}")

    # Delete CSV
    os.remove(PULSE_PATH)
    print(f"DELETED: {PULSE_PATH}")

    # Clear env var
    with open("/opt/data/.env", "r") as f:
        lines = f.readlines()
    with open("/opt/data/.env", "w") as f:
        for line in lines:
            if not line.startswith("PULSE_PATH_USERS="):
                f.write(line)
    print("ENV_CLEARED")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: pulses_csv.py [create|register <id>|check <id>|export-and-clean]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "create":
        create()
    elif cmd == "register" and len(sys.argv) >= 3:
        register(sys.argv[2])
    elif cmd == "check" and len(sys.argv) >= 3:
        check(sys.argv[2])
    elif cmd == "export-and-clean":
        export_and_clean()
    else:
        print("Comando invalido")