#!/bin/bash
# GitHub Traffic 日报：拉取 clone 和 view 数据，追加到 CSV
# 用法：bash github-traffic.sh
# 建议每天跑一次（cron 或手动），GitHub 只保留 14 天数据

REPO="wuyining0130/c-room"
TOKEN="${GITHUB_TOKEN:?请先设置 GITHUB_TOKEN 环境变量（需要 repo 权限的 classic token）}"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/traffic-data"
mkdir -p "$DATA_DIR"

CLONES_CSV="$DATA_DIR/clones.csv"
VIEWS_CSV="$DATA_DIR/views.csv"

# 初始化 CSV 表头
[ ! -f "$CLONES_CSV" ] && echo "date,clones,unique_cloners" > "$CLONES_CSV"
[ ! -f "$VIEWS_CSV" ] && echo "date,views,unique_visitors" > "$VIEWS_CSV"

# 拉取 clones 数据
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/traffic/clones" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data.get('clones', []):
    date = c['timestamp'][:10]
    print(f\"{date},{c['count']},{c['uniques']}\")
" | while read -r line; do
  date=$(echo "$line" | cut -d',' -f1)
  grep -q "^$date," "$CLONES_CSV" || echo "$line" >> "$CLONES_CSV"
done

# 拉取 views 数据
curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/traffic/views" | \
  python3 -c "
import json, sys
data = json.load(sys.stdin)
for v in data.get('views', []):
    date = v['timestamp'][:10]
    print(f\"{date},{v['count']},{v['uniques']}\")
" | while read -r line; do
  date=$(echo "$line" | cut -d',' -f1)
  grep -q "^$date," "$VIEWS_CSV" || echo "$line" >> "$VIEWS_CSV"
done

# 输出日报
echo ""
echo "=== C-ROOM GitHub Traffic 日报 ==="
echo ""
echo "📦 Clone 数据（最近 14 天）"
echo "----------------------------"
printf "%-12s %8s %8s\n" "日期" "clone数" "独立用户"
tail -14 "$CLONES_CSV" | grep -v "^date" | while IFS=',' read -r date count uniques; do
  printf "%-12s %8s %8s\n" "$date" "$count" "$uniques"
done

TOTAL_CLONES=$(tail -14 "$CLONES_CSV" | grep -v "^date" | awk -F',' '{s+=$2}END{print s}')
TOTAL_UNIQUE=$(tail -14 "$CLONES_CSV" | grep -v "^date" | awk -F',' '{s+=$3}END{print s}')
echo "----------------------------"
printf "%-12s %8s %8s\n" "合计" "$TOTAL_CLONES" "$TOTAL_UNIQUE"

echo ""
echo "👀 页面访问（最近 14 天）"
echo "----------------------------"
printf "%-12s %8s %8s\n" "日期" "浏览量" "独立访客"
tail -14 "$VIEWS_CSV" | grep -v "^date" | while IFS=',' read -r date count uniques; do
  printf "%-12s %8s %8s\n" "$date" "$count" "$uniques"
done

TOTAL_VIEWS=$(tail -14 "$VIEWS_CSV" | grep -v "^date" | awk -F',' '{s+=$2}END{print s}')
TOTAL_VISITORS=$(tail -14 "$VIEWS_CSV" | grep -v "^date" | awk -F',' '{s+=$3}END{print s}')
echo "----------------------------"
printf "%-12s %8s %8s\n" "合计" "$TOTAL_VIEWS" "$TOTAL_VISITORS"
echo ""
