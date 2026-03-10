#!/bin/bash
set -e

echo "DeerFlow backend starting on Railway..."

# ── Persistent volume setup (/data) ─────────────────────────────────────────
mkdir -p /data/.deer-flow

# ── Symlink /mnt/skills → /app/skills so skill scripts work with hardcoded /mnt paths ──
mkdir -p /app/skills
ln -sfn /app/skills /mnt/skills
[ -f /data/memory.json ] || echo '{}' > /data/memory.json
rm -f /app/backend/.deer-flow && ln -sf /data/.deer-flow /app/backend/.deer-flow
rm -f /app/backend/memory.json && ln -sf /data/memory.json /app/backend/memory.json

# ── Fetch skills from GitHub ─────────────────────────────────────────────────
# Skills are Markdown files that define agent capabilities (image-gen, video-gen, etc.)
SKILLS_DIR="/app/skills"
SKILLS_STAMP="$SKILLS_DIR/.fetched"

if [ ! -f "$SKILLS_STAMP" ]; then
  echo "Fetching skills from bytedance/deer-flow..."
  TMPDIR=$(mktemp -d)

  # Full shallow clone (sparse-checkout is unreliable for subdirectory file content)
  if git clone --depth=1 "https://github.com/bytedance/deer-flow.git" "$TMPDIR/df" 2>&1; then
    if [ -d "$TMPDIR/df/skills" ]; then
      mkdir -p "$SKILLS_DIR"
      cp -r "$TMPDIR/df/skills/." "$SKILLS_DIR/"
      touch "$SKILLS_STAMP"
      echo "Skills ready: $(ls $SKILLS_DIR/public 2>/dev/null | wc -l) built-in skill(s)"
      ls "$SKILLS_DIR/public" 2>/dev/null
    else
      echo "Warning: skills directory not found in repo"
      mkdir -p "$SKILLS_DIR/public" "$SKILLS_DIR/custom"
    fi
  else
    echo "Warning: could not clone skills repo — agent will work without built-in skill templates"
    mkdir -p "$SKILLS_DIR/public" "$SKILLS_DIR/custom"
  fi
  rm -rf "$TMPDIR"
else
  echo "Skills already present: $(ls $SKILLS_DIR/public 2>/dev/null | wc -l) skill(s)"
fi

echo "  Gateway:   http://0.0.0.0:8001"
echo "  LangGraph: http://0.0.0.0:2024"
echo "  Config:    ${DEER_FLOW_CONFIG_PATH:-/app/config.yaml}"

exec supervisord -n
