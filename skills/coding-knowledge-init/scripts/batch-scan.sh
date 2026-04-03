#!/usr/bin/env bash
#
# batch-scan.sh — 批量扫描所有仓库，输出结构化 JSON
#
# 用法：
#   batch-scan.sh <repos-dir> <output-dir>
#   batch-scan.sh <repo1> <repo2> ... -- <output-dir>
#
# 示例：
#   # 扫描目录下所有子目录
#   batch-scan.sh /path/to/repos /path/to/output
#
#   # 扫描指定仓库列表
#   batch-scan.sh /path/to/repo1 /path/to/repo2 -- /path/to/output
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAN_SCRIPT="${SCRIPT_DIR}/scan-repo.py"

if [ ! -f "$SCAN_SCRIPT" ]; then
    echo "Error: scan-repo.py not found at $SCAN_SCRIPT" >&2
    exit 1
fi

usage() {
    echo "Usage:"
    echo "  $0 <repos-dir> <output-dir>"
    echo "  $0 <repo1> <repo2> ... -- <output-dir>"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

# Parse arguments
REPOS=()
OUTPUT_DIR=""

if [[ "$*" == *" -- "* ]]; then
    # Mode: explicit repo list
    while [ $# -gt 0 ]; do
        if [ "$1" = "--" ]; then
            shift
            OUTPUT_DIR="$1"
            break
        fi
        REPOS+=("$1")
        shift
    done
else
    # Mode: repos-dir + output-dir
    REPOS_DIR="$1"
    OUTPUT_DIR="$2"

    if [ ! -d "$REPOS_DIR" ]; then
        echo "Error: repos directory '$REPOS_DIR' does not exist" >&2
        exit 1
    fi

    # Collect all subdirectories
    for dir in "$REPOS_DIR"/*/; do
        if [ -d "$dir" ]; then
            REPOS+=("${dir%/}")
        fi
    done
fi

if [ -z "$OUTPUT_DIR" ]; then
    echo "Error: output directory not specified" >&2
    usage
fi

mkdir -p "$OUTPUT_DIR"

echo "=== Batch Scan ==="
echo "Repos to scan: ${#REPOS[@]}"
echo "Output dir: $OUTPUT_DIR"
echo ""

TOTAL=${#REPOS[@]}
SUCCESS=0
FAILED=0
START_TIME=$(date +%s)

for i in "${!REPOS[@]}"; do
    repo="${REPOS[$i]}"
    repo_name=$(basename "$repo")
    idx=$((i + 1))

    echo "[$idx/$TOTAL] Scanning $repo_name ..."

    if python3 "$SCAN_SCRIPT" "$repo" --output-dir "$OUTPUT_DIR"; then
        SUCCESS=$((SUCCESS + 1))
        echo "  ✓ Done"
    else
        FAILED=$((FAILED + 1))
        echo "  ✗ Failed"
    fi
done

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "=== Summary ==="
echo "Total: $TOTAL | Success: $SUCCESS | Failed: $FAILED"
echo "Time: ${ELAPSED}s"
echo "Output: $OUTPUT_DIR"

# List output files
echo ""
echo "Generated files:"
ls -la "$OUTPUT_DIR"/*.scan-result.json 2>/dev/null || echo "  (none)"
