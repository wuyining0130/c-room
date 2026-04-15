#!/bin/bash
# GitHub Traffic 日报：拉取 clone 和 view 数据，合并到一个 CSV
# 用法：bash github-traffic.sh
# 建议每天跑一次（cron 或手动），GitHub 只保留 14 天数据

REPO="wuyining0130/c-room"
TOKEN="${GITHUB_TOKEN:?请先设置 GITHUB_TOKEN 环境变量（需要 repo 权限的 classic token）}"
DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)/traffic-data"
mkdir -p "$DATA_DIR"

TRAFFIC_CSV="$DATA_DIR/traffic.csv"

# 初始化 CSV 表头
[ ! -f "$TRAFFIC_CSV" ] && echo "日期(Date),克隆次数(Clones),独立克隆用户(Unique Cloners),页面浏览量(Views),独立访客(Unique Visitors)" > "$TRAFFIC_CSV"

# 拉取数据
CLONES_JSON=$(curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/traffic/clones")
VIEWS_JSON=$(curl -s -H "Authorization: token $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/$REPO/traffic/views")

# 合并两个 JSON 写入 CSV（跳过已存在的日期）
_CLONES="$CLONES_JSON" _VIEWS="$VIEWS_JSON" _CSV="$TRAFFIC_CSV" \
python3 -c '
import json, os

clones = json.loads(os.environ["_CLONES"])
views  = json.loads(os.environ["_VIEWS"])
csv_path = os.environ["_CSV"]

# 读取已有数据，去掉合计行
lines = []
existing = set()
try:
    with open(csv_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("合计"):
                continue
            lines.append(line)
            if not line.startswith("日期"):
                existing.add(line.split(",")[0])
except FileNotFoundError:
    pass

# 追加新日期
clone_map = {c["timestamp"][:10]: c for c in clones.get("clones", [])}
view_map  = {v["timestamp"][:10]: v for v in views.get("views", [])}
all_dates = sorted(set(list(clone_map.keys()) + list(view_map.keys())))

for date in all_dates:
    if date in existing:
        continue
    c = clone_map.get(date, {"count": 0, "uniques": 0})
    v = view_map.get(date, {"count": 0, "uniques": 0})
    lines.append(",".join([date, str(c["count"]), str(c["uniques"]), str(v["count"]), str(v["uniques"])]))

# 计算合计（跳过表头）
totals = [0, 0, 0, 0]
for line in lines:
    if line.startswith("日期"):
        continue
    parts = line.split(",")
    for i in range(4):
        totals[i] += int(parts[i + 1])
lines.append(",".join(["合计(Total)", str(totals[0]), str(totals[1]), str(totals[2]), str(totals[3])]))

# 重写文件
with open(csv_path, "w") as f:
    f.write("\n".join(lines) + "\n")
'

# 输出日报
echo ""
echo "=== C-ROOM GitHub Traffic 日报 ==="
echo ""
printf "%-12s %10s %14s %10s %10s\n" "日期" "克隆次数" "独立克隆用户" "页面浏览量" "独立访客"
echo "--------------------------------------------------------------"
grep -v "^日期" "$TRAFFIC_CSV" | grep -v "^合计" | while IFS=',' read -r date clones uniq_c views uniq_v; do
  printf "%-12s %10s %14s %10s %10s\n" "$date" "$clones" "$uniq_c" "$views" "$uniq_v"
done

TOTAL_C=$(grep -v "^日期" "$TRAFFIC_CSV" | grep -v "^合计" | awk -F',' '{s+=$2}END{print s}')
TOTAL_UC=$(grep -v "^日期" "$TRAFFIC_CSV" | grep -v "^合计" | awk -F',' '{s+=$3}END{print s}')
TOTAL_V=$(grep -v "^日期" "$TRAFFIC_CSV" | grep -v "^合计" | awk -F',' '{s+=$4}END{print s}')
TOTAL_UV=$(grep -v "^日期" "$TRAFFIC_CSV" | grep -v "^合计" | awk -F',' '{s+=$5}END{print s}')
echo "--------------------------------------------------------------"
printf "%-12s %10s %14s %10s %10s\n" "合计" "$TOTAL_C" "$TOTAL_UC" "$TOTAL_V" "$TOTAL_UV"
echo ""
