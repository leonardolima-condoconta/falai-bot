#!/bin/bash
# Falai Gateway Watchdog — verifica se o gateway está respondendo
# Se estiver DOWN, escreve arquivo de alerta que o cronjob detecta

ALERT_FILE="/opt/data/session_checkpoints/GATEWAY_DOWN_ALERT"
GATEWAY_PID=$(pgrep -f "hermes.*gateway" 2>/dev/null | head -1)

if [ -z "$GATEWAY_PID" ]; then
    # Gateway não está rodando
    if [ ! -f "$ALERT_FILE" ]; then
        echo "DOWN $(date '+%Y-%m-%d %H:%M:%S')" > "$ALERT_FILE"
        echo "DOWN"
    else
        echo "STILL_DOWN"
    fi
    exit 1
else
    # Gateway está rodando — limpa alerta se existir
    rm -f "$ALERT_FILE"
    echo "UP $(date '+%Y-%m-%d %H:%M:%S') PID=$GATEWAY_PID"
    exit 0
fi