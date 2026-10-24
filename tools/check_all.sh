#!/usr/bin/env bash
# 検算をまとめて走らせる。各トピックの tools/<topic>/check.sh が終了コード 0 なら PASS。
#
# 使い方: tools/check_all.sh            # 全トピック
#         tools/check_all.sh 01-foo     # 指定トピックだけ
#         CHECK_FAST=1 tools/check_all.sh   # 重い検算を縮小版で（各 check.sh が対応していれば）
#
# 出力は1トピック1行に抑え、詳細は .ralph/logs/check-<topic>.log に残す（エージェントの文脈を汚さないため）。
# 終了コード: 全 PASS なら 0、1つでも FAIL なら 1。
set -u
cd "$(dirname "$0")/.." || exit 1
mkdir -p .ralph/logs

if [ "$#" -gt 0 ]; then
  scripts=()
  for t in "$@"; do scripts+=("tools/${t%/}/check.sh"); done
else
  scripts=(tools/*/check.sh)
fi

fail=0
n=0
for c in "${scripts[@]}"; do
  if [ ! -e "$c" ]; then
    [ "$#" -gt 0 ] && { echo "FAIL $(basename "$(dirname "$c")")  （$c が無い）"; fail=1; }
    continue
  fi
  n=$((n + 1))
  topic=$(basename "$(dirname "$c")")
  log=".ralph/logs/check-${topic}.log"
  start=$(date +%s)
  if (cd "$(dirname "$c")" && bash ./check.sh) >"$log" 2>&1; then
    echo "PASS ${topic}  ($(( $(date +%s) - start ))s)"
  else
    echo "FAIL ${topic}  ($(( $(date +%s) - start ))s, 詳細: ${log})"
    tail -n 5 "$log" | sed 's/^/    /'
    fail=1
  fi
done

[ "$n" -eq 0 ] && [ "$fail" -eq 0 ] && echo "検算はまだ無い（tools/*/check.sh が 0 件）"
exit "$fail"
