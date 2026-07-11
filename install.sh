#!/usr/bin/env bash
set -euo pipefail

# c-room installer
# Normal installs copy the clean distribution from skills-release/.
# Use --dev to link the development version in skills/ (including eval assets).

DEV_MODE=false
PLATFORM="claude"
for arg in "$@"; do
    case "$arg" in
        --dev) DEV_MODE=true ;;
        --codex) PLATFORM="codex" ;;
        *) echo "Error: unknown option: $arg" >&2; exit 1 ;;
    esac
done

if [ "$PLATFORM" = "codex" ]; then
    SKILLS_DIR="${CODEX_HOME:-${HOME}/.codex}/skills"
else
    SKILLS_DIR="${HOME}/.claude/skills"
fi
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_SKILLS_DIR="${REPO_ROOT}/skills-release"
if [ "$DEV_MODE" = true ]; then
    REPO_SKILLS_DIR="${REPO_ROOT}/skills"
fi

# Support remote one-liner: curl | bash
if [ ! -d "$REPO_SKILLS_DIR" ]; then
    if [ "$DEV_MODE" = true ]; then
        echo "Error: --dev requires a local clone."
        exit 1
    fi
    TMPDIR=$(mktemp -d)
    trap 'rm -rf "$TMPDIR"' EXIT
    echo "Cloning c-room..."
    git clone --depth 1 https://github.com/wuyining0130/c-room.git "$TMPDIR" 2>/dev/null
    REPO_SKILLS_DIR="$TMPDIR/skills-release"
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
    echo "Skills are ready for ${PLATFORM}."
fi
