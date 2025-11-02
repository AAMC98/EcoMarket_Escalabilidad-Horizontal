#!/bin/sh
# Wait-for-RabbitMQ script
# Usage: set env RABBIT_HOST and RABBIT_PORT (defaults: rabbitmq:5672)
set -e

HOST=${RABBIT_HOST:-rabbitmq}
PORT=${RABBIT_PORT:-5672}
MAX_RETRIES=${WAIT_MAX_RETRIES:-20}
SLEEP_SECONDS=${WAIT_SLEEP_SECONDS:-1}

echo "[wait-for-rabbit] Waiting for RabbitMQ at ${HOST}:${PORT} (max ${MAX_RETRIES} attempts)"
i=0
while true; do
  i=$((i+1))
  python - <<PY 2>/dev/null
import os, socket, sys
host=os.environ.get('RABBIT_HOST','rabbitmq')
port=int(os.environ.get('RABBIT_PORT','5672'))
try:
    s=socket.socket()
    s.settimeout(2)
    s.connect((host, port))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    echo "[wait-for-rabbit] RabbitMQ reachable"
    break
  fi
  if [ "$i" -ge "$MAX_RETRIES" ]; then
    echo "[wait-for-rabbit] Timeout waiting for RabbitMQ after ${i} attempts" >&2
    exit 1
  fi
  sleep ${SLEEP_SECONDS}
done

echo "[wait-for-rabbit] Starting: $@"
exec "$@"
