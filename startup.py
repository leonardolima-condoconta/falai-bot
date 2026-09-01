#!/usr/bin/env python3
"""Startup — carrega .env antes de iniciar gateway."""

import os, sys

HERMES_BIN = "/opt/hermes/.venv/bin/hermes"

def load_dotenv(path='/opt/data/.env'):
    """Carrega variáveis do .env para o ambiente do processo."""
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

if __name__ == "__main__":
    load_dotenv()
    print("[startup] .env carregado, iniciando gateway...")
    os.execv(HERMES_BIN, [HERMES_BIN, "gateway", "run"])