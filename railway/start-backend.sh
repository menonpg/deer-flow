#!/bin/bash
set -e

echo "DeerFlow backend starting on Railway..."

# ── Persistent volume setup (/data) ─────────────────────────────────────────
mkdir -p /data/.deer-flow
[ -f /data/memory.json ] || echo '{}' > /data/memory.json
rm -f /app/backend/.deer-flow && ln -sf /data/.deer-flow /app/backend/.deer-flow
rm -f /app/backend/memory.json && ln -sf /data/memory.json /app/backend/memory.json

# ── Fetch skills from GitHub (excluded from Docker build context) ────────────
# Skills are Markdown files that define agent capabilities.
SKILLS_DIR="/app/skills"
if [ ! -d "$SKILLS_DIR/public" ]; then
  echo "Fetching skills from GitHub..."
  TMPDIR=$(mktemp -d)
  git clone --depth=1 --filter=blob:none --sparse \
    "https://github.com/bytedance/deer-flow.git" "$TMPDIR/df" 2>/dev/null || \
    git clone --depth=1 "https://github.com/bytedance/deer-flow.git" "$TMPDIR/df" 2>/dev/null
  if [ -d "$TMPDIR/df/skills" ]; then
    cp -r "$TMPDIR/df/skills" "$SKILLS_DIR"
    echo "Skills ready: $(ls $SKILLS_DIR/public 2>/dev/null | wc -l) built-in skill(s)"
  else
    echo "Warning: could not fetch skills — agent will work without built-in skill templates"
    mkdir -p "$SKILLS_DIR/public" "$SKILLS_DIR/custom"
  fi
  rm -rf "$TMPDIR"
else
  echo "Skills already present at $SKILLS_DIR"
fi

echo "  Gateway:   http://0.0.0.0:8001"
echo "  LangGraph: http://0.0.0.0:2024"
echo "  Config:    ${DEER_FLOW_CONFIG_PATH:-/app/config.yaml}"

exec supervisord -n
