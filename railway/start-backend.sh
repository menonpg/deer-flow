#!/bin/bash
set -e

# Ensure persistent data dirs exist (Railway volume at /data)
mkdir -p /data/.deer-flow
[ -f /data/memory.json ] || echo '{}' > /data/memory.json

# Re-create symlinks in case the container was rebuilt
[ -L /app/backend/.deer-flow ] || ln -sf /data/.deer-flow /app/backend/.deer-flow
[ -L /app/backend/memory.json ] || ln -sf /data/memory.json /app/backend/memory.json

echo "DeerFlow backend starting..."
echo "  Gateway:   http://0.0.0.0:8001"
echo "  LangGraph: http://0.0.0.0:2024"
echo "  Config:    $DEER_FLOW_CONFIG_PATH"

exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
