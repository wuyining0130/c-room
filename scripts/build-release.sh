#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/skills"
RELEASE_DIR="${ROOT_DIR}/skills-release"

if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: skills/ directory not found." >&2
    exit 1
fi

mkdir -p "$RELEASE_DIR"
rsync -a --delete \
    --exclude='evals/' \
    --exclude='test_*.py' \
    --exclude='.DS_Store' \
    "${SOURCE_DIR}/" "${RELEASE_DIR}/"

if find "$RELEASE_DIR" \( -type d -name evals -o -type f -name 'test_*.py' -o -type f -name '.DS_Store' \) | grep -q .; then
    echo "Error: development-only files leaked into skills-release/." >&2
    exit 1
fi

echo "Built clean distribution: ${RELEASE_DIR}"
