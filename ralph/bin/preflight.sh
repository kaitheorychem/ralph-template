#!/usr/bin/env bash
# イテレーション開始前のチェック（ralph/PROMPT.md 手順0）。
#
# 使い方: bash ralph/bin/preflight.sh [--local]
#   --local  ローカルモード（未マージ PR の確認とベースブランチへの同期をしない）
#
# 出力は1行ずつ OK: / NOTE: / WARN: / SKIP: で始まる。
# 終了コード: 0 = 続行してよい / 3 = SKIP（研究せずに終了する）/ 1 = このスクリプト自体の異常
set -u

local_mode=0
[ "${1:-}" = "--local" ] && local_mode=1

root=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "WARN: git リポジトリの外で実行された"; exit 1; }
cd "$root" || exit 1

RALPH_BASE=main
RALPH_MAX_PER_DAY=0
if [ -f ralph/config.env ]; then
  # shellcheck disable=SC1091
  . ralph/config.env
fi
base=$RALPH_BASE
skip=0

# 1. 人間による停止
if [ -e ralph/STOP ]; then
  echo "SKIP: ralph/STOP がある（人間による停止）。再開するにはこのファイルを消す"
  skip=1
fi

# 2. 目標が未記入
n_todo=$(grep -c 'TODO(human)' ralph/GOAL.md 2>/dev/null)
if [ "${n_todo:-0}" -gt 0 ]; then
  echo "SKIP: ralph/GOAL.md に TODO(human) が ${n_todo} 箇所残っている（人間が目標を書くまで作業しない）"
  skip=1
fi

# 3. 1日の上限
today=$(date +%F)
n_today=$(find ralph/journal -maxdepth 1 -name "[0-9][0-9][0-9][0-9]-${today}.md" 2>/dev/null | wc -l)
if [ "${RALPH_MAX_PER_DAY:-0}" -gt 0 ] && [ "$n_today" -ge "$RALPH_MAX_PER_DAY" ]; then
  echo "SKIP: 今日（${today}）のイテレーションが上限 ${RALPH_MAX_PER_DAY} 回に達した（ralph/config.env）"
  skip=1
fi

# 4. 未マージの [ralph] PR（PR モードのみ）。gh の REST API を使う（GraphQL はクラウド環境で拒否される）
if [ "$local_mode" -eq 0 ] && [ "$skip" -eq 0 ]; then
  url=$(git remote get-url origin 2>/dev/null)
  slug=$(printf '%s' "$url" | sed -E 's#\.git$##; s#/+$##' | awk -F'[/:]' '{ if (NF >= 2) print $(NF-1) "/" $NF }')
  if ! command -v gh >/dev/null 2>&1; then
    echo "WARN: gh が無いので未マージ PR を確認できない。GitHub ツールで ${slug:-このリポジトリ} の open な PR を見て、タイトルが [ralph] で始まるものがあれば終了すること"
  elif [ -z "$slug" ]; then
    echo "WARN: origin の URL からリポジトリ名を読み取れない（$url）。GitHub ツールで未マージの [ralph] PR を確認すること"
  elif open_prs=$(gh api "repos/${slug}/pulls?state=open&per_page=100" \
        --jq '.[] | select(.title | startswith("[ralph]")) | "#\(.number) \(.title)"' 2>&1); then
    if [ -n "$open_prs" ]; then
      echo "SKIP: 未マージの [ralph] PR がある（マージか却下を待つ）: $(printf '%s' "$open_prs" | head -3 | tr '\n' ' ')"
      skip=1
    else
      echo "OK: 未マージの [ralph] PR なし（${slug}）"
    fi
  else
    echo "WARN: gh api で PR 一覧を取れなかった: $(printf '%s' "$open_prs" | head -1)。GitHub ツールで未マージの [ralph] PR を確認すること"
  fi
fi

[ "$skip" -eq 1 ] && exit 3

# 5. 最新のベースブランチから始める（PR モードのみ）。
#    GitHub の PR イベントで起動した実行は PR の head から始まるため、ここで揃える。
if [ "$local_mode" -eq 0 ]; then
  if ! git fetch -q origin "$base" 2>/dev/null; then
    echo "WARN: git fetch origin ${base} に失敗。最新のベースブランチかどうか確認できない"
  elif git merge-base --is-ancestor "origin/${base}" HEAD 2>/dev/null; then
    echo "OK: HEAD は origin/${base} を含む"
  else
    clean=0
    [ -z "$(git status --porcelain --untracked-files=no)" ] && clean=1
    unique=$(git rev-list HEAD --not --remotes 2>/dev/null | head -1)
    branch=$(git branch --show-current)
    if [ "$clean" -eq 1 ] && [ -z "$unique" ]; then
      if [ -n "$branch" ]; then
        git checkout -q -B "$branch" "origin/${base}" && echo "NOTE: ブランチ ${branch} を origin/${base} に合わせた"
      else
        git checkout -q --detach "origin/${base}" && echo "NOTE: origin/${base} に切り替えた（detached HEAD。コミット前にブランチを作ること）"
      fi
    else
      echo "WARN: HEAD が origin/${base} の最新を含んでいない（未コミットか未プッシュの変更がある）。今回まだ何も変更していないなら次を実行してから始める: git checkout -B \"${branch:-ralph-work}\" origin/${base}"
    fi
  fi
fi

echo "OK: 続行してよい（今日の記録済みイテレーション: ${n_today} 回）"
exit 0
