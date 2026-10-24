# AGENTS.md

このリポジトリは Ralph ループ（自律研究ループ）で理論研究を進めている。どのコーディングエージェントもここから入る。

- 研究・執筆・検算をする前に、必ず [ralph/RULES.md](ralph/RULES.md)（規約）と [ralph/GOAL.md](ralph/GOAL.md)（目標）を読む。
- ループの1イテレーションを頼まれたら [ralph/PROMPT.md](ralph/PROMPT.md) に従う。
- 対話セッションで研究を進めたら、終える前に PLAN.md・claims.json・journal を更新してループに引き継ぐ（RULES.md「対話セッションからの引き継ぎ」）。
- 仕組み・セットアップ・運用は [ralph/README.md](ralph/README.md)。

## よく使うコマンド

- 全トピックの検算：`tools/check_all.sh`（1トピックだけなら `tools/check_all.sh 01-foo`、軽量版は `CHECK_FAST=1` を前に付ける）
- 台帳・journal などの機械チェック：`python3 ralph/bin/lint.py`（ループの PR では `--base origin/main --loop`）
- イテレーション開始前のチェック：`bash ralph/bin/preflight.sh`

## 守ること（詳細は RULES.md）

- 「検証した」と書くのは、実行したコマンドと結果を示せるときだけ。数値や図を合わせるために式や許容誤差をいじらない。
- 人間が管理するファイル（このファイル、CLAUDE.md、README.md、ralph/{PROMPT,RULES,GOAL,README}.md、ralph/config.env、ralph/loop.sh、ralph/bin/、ralph/ci/、.claude/、.github/、tools/check_all.sh、refs/）は変更しない。変えたいときは ralph/QUESTIONS.md で提案する。
