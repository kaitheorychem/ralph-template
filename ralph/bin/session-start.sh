#!/usr/bin/env bash
# SessionStart フック（.claude/settings.json から呼ばれる）。
# クラウドセッションでだけ、検算に使う Python パッケージ（requirements.txt）を入れる。ローカルでは何もしない。
[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
[ -f requirements.txt ] || exit 0
grep -qvE '^[[:space:]]*(#|$)' requirements.txt || exit 0   # パッケージが1つも書かれていなければ何もしない

mkdir -p .ralph/logs
if ! python3 -m pip install -q --root-user-action=ignore -r requirements.txt >.ralph/logs/pip.log 2>&1; then
  echo "WARN: requirements.txt のインストールに失敗（.ralph/logs/pip.log）。ネットワーク設定を確認すること"
fi
exit 0
