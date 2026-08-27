#!/bin/bash
# Watchdog script para app.py do Convenia
# ⚠️ USA PADRÃO ANCORADO ($) para evitar falso positivo do pgrep
# Uso: nohup bash watchdog.sh > /dev/null 2>&1 &
#
# Pitfall: pgrep -f "app.py" SEM âncora casa com o próprio watchdog,
# fazendo o watchdog achar que o app está sempre OK.
# Sempre usar: pgrep -f '/opt/data/convenia/app.py$'

LOG="${LOG:-/opt/data/convenia_data/watchdog.log}"
APP_DIR="/opt/data/convenia"
PYTHON_BIN="/opt/data/.venv/bin/python3"
APP_FILE="$APP_DIR/app.py"
APP_LOG="/opt/data/convenia_data/app.log"
PGREP_PATTERN="/opt/data/convenia/app.py$"
LOCKFILE="/tmp/convenia_watchdog.lock"

# ── Lock mechanism: prevent duplicate watchdog instances ──
cleanup_lock() { rm -f "$LOCKFILE"; }
if ! mkdir "$LOCKFILE" 2>/dev/null; then
  # Lock exists — check if the holder is still alive
  LOCK_PID=$(cat "$LOCKFILE/pid" 2>/dev/null)
  if [ -n "$LOCK_PID" ] && kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Watchdog já rodando (PID $LOCK_PID) — saindo" >> "$LOG"
    exit 0
  fi
  # Stale lock — takeover
  rm -rf "$LOCKFILE"
  mkdir "$LOCKFILE"
fi
echo $$ > "$LOCKFILE/pid"
trap cleanup_lock EXIT

while true; do
  if ! pgrep -f "$PGREP_PATTERN" > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ App caído — reiniciando..." >> "$LOG"
    cd "$APP_DIR" && PYTHONPATH="$APP_DIR:$PYTHONPATH" \
      "$PYTHON_BIN" -u "$APP_FILE" >> "$APP_LOG" 2>&1 &
    sleep 3
    if pgrep -f "$PGREP_PATTERN" > /dev/null 2>&1; then
      APP_PID=$(pgrep -f "$PGREP_PATTERN" | head -1)
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ App reiniciado pelo watchdog (PID $APP_PID)" >> "$LOG"
    fi
  else
    APP_PID=$(pgrep -f "$PGREP_PATTERN" | head -1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Watchdog check — app OK (PID $APP_PID)" >> "$LOG"
  fi
  sleep 60
done