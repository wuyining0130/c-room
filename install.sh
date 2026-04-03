#!/usr/bin/env bash
set -euo pipefail

# c-room installer
# Copies all skills to ~/.claude/skills/
# Use --dev to create symlinks instead (changes take effect immediately)

DEV_MODE=false
if [ "${1:-}" = "--dev" ]; then
    DEV_MODE=true
fi

SKILLS_DIR="${HOME}/.claude/skills"
REPO_SKILLS_DIR="$(cd "$(dirname "$0")" && pwd)/skills"

# Support remote one-liner: curl | bash
if [ ! -d "$REPO_SKILLS_DIR" ]; then
    if [ "$DEV_MODE" = true ]; then
        echo "Error: --dev requires a local clone."
        exit 1
    fi
    TMPDIR=$(mktemp -d)
    trap 'rm -rf "$TMPDIR"' EXIT
    echo "Cloning c-room..."
    git clone --depth 1 https://github.com/anthropics/c-room.git "$TMPDIR" 2>/dev/null
    REPO_SKILLS_DIR="$TMPDIR/skills"
fi

mkdir -p "$SKILLS_DIR"

count=0
for skill_dir in "$REPO_SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    rm -rf "${SKILLS_DIR}/${skill_name}"
    if [ "$DEV_MODE" = true ]; then
        ln -s "$skill_dir" "${SKILLS_DIR}/${skill_name}"
        echo "  Linked: $skill_name"
    else
        cp -r "$skill_dir" "${SKILLS_DIR}/${skill_name}"
        echo "  Installing: $skill_name"
    fi
    count=$((count + 1))
done

echo ""
if [ "$DEV_MODE" = true ]; then
    echo "Done! Linked ${count} skills to ${SKILLS_DIR} (dev mode)"
    echo "Changes in skills/ will take effect immediately."
else
    echo "Done! Installed ${count} skills to ${SKILLS_DIR}"
    echo "Use /skill-name in Claude Code to invoke them."
fi
