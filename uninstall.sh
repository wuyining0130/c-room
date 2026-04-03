#!/usr/bin/env bash
set -euo pipefail

# c-room uninstaller
# Removes skills installed by this project from ~/.claude/skills/

SKILLS_DIR="${HOME}/.claude/skills"

# Skills managed by this project
SKILLS=(
    code-gen
    code-review
    coding-knowledge-init
    conventions
    knowledge-init
    prd-draft
    prd-review
    project-import
    proto-gen
    tapd-sync
    tech-design
)

count=0
for skill_name in "${SKILLS[@]}"; do
    if [ -d "${SKILLS_DIR}/${skill_name}" ]; then
        echo "  Removing: $skill_name"
        rm -rf "${SKILLS_DIR}/${skill_name}"
        count=$((count + 1))
    fi
done

echo ""
if [ "$count" -eq 0 ]; then
    echo "No skills found to remove."
else
    echo "Done! Removed ${count} skills from ${SKILLS_DIR}"
fi
