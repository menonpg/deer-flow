#!/bin/bash
set -e

# Ensure persistent data dirs exist (Railway volume at /data)
mkdir -p /data/.deer-flow
[ -f /data/memory.json ] || echo '{}' > /data/memory.json

# Re-create symlinks in case the container was rebuilt
rm -f /app/backend/.deer-flow && ln -sf /data/.deer-flow /app/backend/.deer-flow
rm -f /app/backend/memory.json && ln -sf /data/memory.json /app/backend/memory.json

echo "DeerFlow backend starting..."
echo "  Gateway:   http://0.0.0.0:8001"
echo "  LangGraph: http://0.0.0.0:2024"
echo "  Config:    ${DEER_FLOW_CONFIG_PATH:-/app/config.yaml}"

# supervisord -n runs in foreground; reads /etc/supervisor/conf.d/*.conf automatically
exec supervisord -n
