#!/usr/bin/env bash
# ローカル／HPC 用の Ralph ループ。
# 1回ごとに新しい claude プロセス（まっさらなコンテキスト）で ralph/PROMPT.md の1イテレーションを実行する。
# ローカルモードでは PR を作らず、今いる作業ブランチにコミットしていく。upstream があれば各回の後に push する。
#
# 使い方:
#   git switch -c ralph/local-run      # 作業用ブランチで回す（ベースブランチ上では動かない）
#   ralph/loop.sh [最大回数]            # 既定 10 回
# 止める:   touch ralph/STOP           # 次の回の開始前に止まる（実行中の回は最後まで走る）
# 調整:     RALPH_CLAUDE_ARGS="--model <モデル> --max-budget-usd 5" ralph/loop.sh 20
# 長時間:   tmux new -s ralph 'ralph/loop.sh 50'   # 切断しても回り続ける
#
# 各回のログ: .ralph/logs/loop-*.jsonl（stream-json。tail -f で様子を見られる）
set -u

root=$(git rev-parse --show-toplevel) || exit 1
cd "$root" || exit 1

RALPH_BASE=main
# shellcheck disable=SC1091
[ -f ralph/config.env ] && . ralph/config.env

max=${1:-10}
branch=$(git branch --show-current)
if [ -z "$branch" ] || [ "$branch" = "$RALPH_BASE" ]; then
  echo "作業用ブランチに切り替えてから実行する（例: git switch -c ralph/local-run）。今: ${branch:-detached HEAD}" >&2
  exit 1
fi
command -v claude >/dev/null 2>&1 || { echo "claude コマンドが見つからない" >&2; exit 1; }

read -r -a extra <<<"${RALPH_CLAUDE_ARGS:-}"
prompt='ralph/PROMPT.md を読んで、その手順に従って自律研究ループを1イテレーション実行してください。モード: ローカル'
mkdir -p .ralph/logs
fails=0

for i in $(seq 1 "$max"); do
  if [ -e ralph/STOP ]; then
    echo "ralph/STOP があるので停止する"
    break
  fi
  log=".ralph/logs/loop-$(date +%Y%m%d-%H%M%S)-${i}.jsonl"
  echo "[$i/$max] $(date '+%F %T') 開始  ログ: $log"

  claude -p "$prompt" \
    --permission-mode auto --permission-prompts none \
    --output-format stream-json --verbose \
    ${extra[@]+"${extra[@]}"} >"$log" 2>&1
  rc=$?

  # 最後の result イベントから最終報告の1行目を取り出す
  result=$(python3 - "$log" <<'PY'
import json, sys
last = None
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if isinstance(ev, dict) and ev.get("type") == "result":
        last = ev
text = (last or {}).get("result") or ""
lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
print(lines[0] if lines else "(最終報告なし)")
PY
)
  echo "  → 終了コード $rc: $result"

  # upstream があれば push して、GitHub から進み具合を見られるようにする
  if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
    git push -q 2>&1 | tail -n 2 | sed 's/^/  push: /'
  fi

  case "$result" in
    SKIP*|COMPLETE*) echo "ループを終える（$result）"; break ;;
  esac
  if [ "$rc" -ne 0 ]; then
    fails=$((fails + 1))
    if [ "$fails" -ge 2 ]; then
      echo "2回続けて異常終了したので止める。ログを確認すること: $log"
      exit 1
    fi
  else
    fails=0
  fi
done
