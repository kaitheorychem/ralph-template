# Ralph ループ（自律研究ループ）

同じ手順書（[PROMPT.md](PROMPT.md)）を、毎回まっさらな文脈のエージェントに渡すだけで理論研究が前に進む仕組み。エージェントの記憶には頼らず、目標・バックログ・進捗・教訓をすべてこのディレクトリのファイルと git に置く。

このテンプレートは 2026 年 10 月時点の知見とツール（Claude Code のクラウド定期実行・GitHub トリガー・auto mode・サブエージェントなど）に合わせて作り直したもの。何をなぜ変えたかは末尾の「設計の根拠」にまとめた。

## 1イテレーションの流れ

```
preflight ─▶ 状況把握 ─▶ 完了判定 ─▶ タスク選択 ─▶ 実行 ─▶ 検証・査読 ─▶ 記録 ─▶ コミット / PR
（止める？）  （検算と lint   （監査まで  （1つだけ）           （tools/ と     （PLAN・claims・
              で健全性確認）   済んだか）                      referee）       NOTES・journal）
```

- **1回1タスク**。続きは次回。状態はファイルにしか残らない。
- **書き手と査読者を分ける**。theory/ に結果を足したら、読み取り専用の `referee` サブエージェントが新しい文脈で導出・記号・極限・検算を点検する。
- **機械的な関門**。検算（`tools/check_all.sh`）と台帳・journal の点検（`ralph/bin/lint.py`）を、エージェント自身と CI の両方が走らせる。エージェントの自己申告だけでは先に進めない。

## ファイル構成

パスはリポジトリルートからの相対。

| パス | 役割 | 書く人 |
|---|---|---|
| [ralph/PROMPT.md](PROMPT.md) | 1イテレーションの手順（ループ本体） | 人間 |
| [ralph/RULES.md](RULES.md) | 研究・執筆・検証・査読・Git の規約 | 人間 |
| [ralph/GOAL.md](GOAL.md) | 目標・問い（Q1…）・検証の基準・完了条件 | 人間 |
| [ralph/config.env](config.env) | ベースブランチ・マージ方針・1日の上限 | 人間 |
| [ralph/PLAN.md](PLAN.md) | タスクバックログ（「最優先（人間）」節は人間が書く） | エージェント |
| [ralph/QUESTIONS.md](QUESTIONS.md) | エージェントから人間への質問と回答 | 両方 |
| [ralph/NOTES.md](NOTES.md) | 教訓（駄目だったやり方・落とし穴）。毎回読む | エージェント |
| [ralph/claims.json](claims.json) | 主張台帳（主要な結果と検証状態） | エージェント |
| `ralph/journal/` | イテレーションごとの記録（1回1ファイル、追記のみ） | エージェント |
| `ralph/reviews/` | 査読レポート（追記のみ） | エージェント |
| `ralph/bin/` | preflight.sh（実行前チェック）、lint.py（機械チェック）、session-start.sh | 人間 |
| [ralph/loop.sh](loop.sh) | ローカル／HPC 用の連続実行スクリプト | 人間 |
| `theory/` | 確定した理論（成果物）。`theory/CONVENTIONS.md` に単位・符号の約束 | エージェント |
| `idea/` | 下書き・途中計算・没案 | エージェント |
| `refs/` | 先行研究（`refs/notes/` の要約ノートだけはエージェントも書く） | 人間 |
| `tools/` | 数値検算。各トピックの `check.sh` と全体の `check_all.sh` | エージェント（check_all.sh は人間） |
| `AGENTS.md` / `CLAUDE.md` | エージェントの入口（CLAUDE.md は AGENTS.md を読み込む） | 人間 |
| `.claude/` | referee サブエージェント、/ralph-handoff スキル、SessionStart フック | 人間 |
| `.github/workflows/ralph-ci.yml` | CI（検算と機械チェック） | 人間 |

「人間」のファイルはループの外から方向を制御するためのもの。エージェントがこれらを変えると lint と CI が止める。

## 新しいリポジトリを作るとき

未記入の箇所には `TODO(human)` が入っている。`grep -rn 'TODO(human)' .` で一覧できる。

1. このテンプレートからリポジトリを作る。
2. [GOAL.md](GOAL.md) の `TODO(human)` をすべて埋める。**1つでも残っているとループは何もせずに終わる**。いちばん効くのは「検証の基準」：既知の極限、参照値、独立な計算手段。エージェントが自分の進み具合を判定できるかどうかはここで決まる。
3. [theory/CONVENTIONS.md](../theory/CONVENTIONS.md) に単位系と符号の約束を書く（エージェントは教科書の慣習に引き戻されやすいので、違うものほど明記する）。
4. [config.env](config.env) を確認する（ベースブランチ、マージ方針、1日の上限）。
5. 必要なら [RULES.md](RULES.md) の「プロジェクト固有の規約」に書き足す。
6. 先行研究を `refs/` に置き、GOAL.md の背景からリンクする。クラウド環境の既定のネットワーク設定では arXiv などに届かないことがあるので、読ませたい論文はファイルで置くのが確実。
7. 検算に使うパッケージを `requirements.txt` に書く（既定は numpy・scipy・sympy・mpmath）。
8. （任意）[PLAN.md](PLAN.md) の「必須」に最初のタスクを書く。空なら初回が GOAL から分解する。
9. ルートの README.md の `TODO(human)` を埋める。

## 動かし方

### A. クラウドの定期実行（基本形）

Claude Code の **Scheduled tasks**（旧称 Routines）で回す。PC を閉じていても動き、各回が新しいクラウドセッション（まっさらな文脈・リポジトリの新しいクローン）になるので Ralph ループと相性がよい。

1. [claude.ai/code/routines](https://claude.ai/code/routines) で **New task**（CLI からは `/schedule`）。
2. プロンプト：
   > ralph/PROMPT.md を読んで、その手順に従って自律研究ループを1イテレーション実行してください。
3. リポジトリにこのリポジトリを選び、モデルはいちばん強いものを選ぶ（理論の正しさが要なので）。
4. 環境：既定の Default（Trusted）は PyPI などのパッケージ取得はできるが、arXiv などは許可リストに無いことがある。論文を取得させたいなら環境のネットワーク設定で許可ドメインを足す。
5. トリガー：
   - **Schedule**：1日1〜2回（例 9:07。毎時0分ちょうどは混むので避ける）。最短間隔は1時間。
   - **GitHub event（推奨して併用）**：Pull request の closed、フィルタは「Is merged = true」「Title starts with `[ralph]`」「Base branch = main」。こうすると**PR をマージした直後に次のイテレーションが始まる**。Schedule は取りこぼしの保険になる。GitHub トリガーには Claude GitHub App のインストールが必要。

運用上の注意：

- 実行はクラウドでは auto mode で始まる。分類器が何度も止めた操作があると、その回は承認待ちで止まる。実行履歴からその回を開いて答える。
- 実行履歴の緑色は「セッションが異常なく終わった」という意味で、研究が進んだという意味ではない。中身は PR と journal で確かめる。
- 実行はサブスクリプションの使用量を消費する。`RALPH_MAX_PER_DAY`（config.env）で1日の回数を抑えられる。
- 前回の PR が開いている間は、次の回は何もせずに終わる（preflight）。**PR をマージしないとループは進まない**。

### B. ローカル／HPC で連続実行

検算に大きな計算資源が要るときや、クラウドの制限（4 vCPU・16 GB 程度）を超えるときは、手元や計算ノードで [loop.sh](loop.sh) を回す。毎回新しい `claude -p` プロセス（まっさらな文脈）でイテレーションを実行し、PR は作らずに作業ブランチへコミットしていく。

```bash
git switch -c ralph/local-run
ralph/loop.sh 20                               # 最大 20 回
RALPH_CLAUDE_ARGS="--max-budget-usd 5" ralph/loop.sh 20   # 1回あたりの費用上限など
touch ralph/STOP                               # 次の回の前に止める
```

`tmux` の中で動かせば切断しても続く。SLURM なら例えば：

```bash
#!/bin/bash
#SBATCH --job-name=ralph
#SBATCH --time=48:00:00
#SBATCH --output=ralph_%j.log
cd "$HOME/my-research"        # このリポジトリ
source .venv/bin/activate
ralph/loop.sh 50
```

ブランチに upstream を設定しておけば各回が push するので、GitHub から進み具合を見られる。区切りのよいところで人間が PR にしてマージする。

### C. 対話で集中して進める

人間が一緒に考えたい局面（方針転換、難所の導出）は対話セッションで進め、終わる前に `/ralph-handoff` でループに引き継ぐ。同じセッションで条件を満たすまで回し続けたいときは Claude Code の `/goal` が使える（各ターンの後に別のモデルが条件を判定する）。例：

```text
/goal PLAN.md の「必須」の T3 が完了し、tools/check_all.sh が全 PASS で、claims.json と journal が更新されている。または 15 ターン経過
```

`/goal` の判定役は会話に出た内容しか見ないので、条件は「コマンドの結果で示せるもの」にする。

並列化（Claude Code の Projects やエージェントチーム）は、問いが互いに独立なときにだけ検討する。理論は前の結果に後が依存する一本道になりやすく、直列のほうが壊れにくい。なお Projects のクラウドスレッドは CLAUDE.md（と `.claude/rules/`）しか読まず、`.claude/` のサブエージェント（referee）・スキル・フックが使えないので、このテンプレートでは A か B を使う。

## 人間の関わり方

- **PR を読む**：journal（何をしたか）、reviews（査読の判定）、claims.json の差分（何がどこまで検証されたか）、CI の結果。要の式は自分でも確かめる。referee は専門家の目の代わりにはならない。
- **方向を変える**：PLAN.md の「最優先（人間）」に書く／QUESTIONS.md の回答欄に書く／GOAL.md を直す。エージェントへの指示はすべてファイル経由。
- **PR を却下する**：PR を閉じる前に、理由を PLAN.md の「最優先（人間）」に1行書いておくと同じ失敗を繰り返しにくい。journal だけ残したいときはそのファイルだけベースブランチに入れる。
- **止める**：Scheduled task を一時停止する。どのモードでも `ralph/STOP` を置けば次の回は何もせずに終わる。
- **終わり**：最終報告が `COMPLETE:` になったら完了条件と完了監査を満たしている。以後の回は校閲だけなので、スケジュールを止めてよい。問いを足したいときは GOAL.md のコアに足せば研究に戻る。
- **ときどき見直す**：NOTES.md が長くなっていないか、claims.json の `draft` が溜まっていないか。新しいモデルが出たら、仕組みのどこかを外しても回るか試す（下の「設計の根拠」の最後を参照）。

## 自動マージ（任意）

`RALPH_MERGE=auto` にすると、エージェントは PR を作った後に自動マージを有効にし、CI が通れば GitHub がマージする。GitHub トリガーと組み合わせると、人間を待たずに次々と進む。

- 準備：リポジトリ設定で「Allow auto-merge」を有効にし、ベースブランチのブランチ保護（またはルールセット）で CI のチェック `check`（ralph-ci）を必須にする。必須チェックが無いと自動マージは安全装置にならない。
- 注意：小さな誤りが次の回の前提になって積み上がる。最初は `human` で10回ほど回し、referee と CI が実際に誤りを止めているのを確かめてから切り替える。`RALPH_MAX_PER_DAY` を必ず設定し、毎日 journal と claims に目を通す。

## 旧テンプレートからの移行

旧版（PROMPT/RULES/GOAL/PLAN/QUESTIONS/journal だけの構成）で作ったリポジトリは次の順で移せる。

1. 新しく加わったファイルをコピーする：AGENTS.md、CLAUDE.md、.claude/、.github/、.gitignore、requirements.txt、ralph/{PROMPT,RULES,README,NOTES}.md、ralph/config.env、ralph/claims.json、ralph/bin/、ralph/loop.sh、ralph/reviews/、tools/check_all.sh、theory/CONVENTIONS.md。
2. GOAL.md を新しい書式に合わせる：コアの問いに Q1… を振り、「検証の基準」「範囲外」を書く（旧 RULES.md の「プロジェクト固有の規約」にあった整合チェックはここへ）。完了条件を新しいものに替える。
3. 各 `tools/<topic>/README.md` の「検査の実行」コマンドを `tools/<topic>/check.sh` に移す。
4. PLAN.md に「最優先（人間）」「査読指摘」「完了」の節を足し、「最優先（人間）」に「既存の theory/ の結果を claims.json に棚卸しする（status は検算の有無に応じて draft か checked）」と書く。棚卸しは次のイテレーションがやる。
5. journal と QUESTIONS.md はそのまま使える（QUESTIONS の番号だけ「質問N」に揃える）。

## 設計の根拠（2026 年 10 月時点）

| 知見 | このテンプレートでの対応 |
|---|---|
| 長い会話は文脈が劣化する。状態をファイルに出し、毎回新しい文脈で1つずつ進めるのが堅い〔1〕〔2〕 | 1回1タスク。状態は PLAN・claims・NOTES・journal と git |
| エージェントは自分の成果を甘く採点する。作る役と評価する役を分け、評価役を懐疑的に調整するほうが効く〔3〕〔4〕 | referee サブエージェント（読み取り専用・新しい文脈）。PASS が無いと主張は `refereed` にならない |
| 理論計算では「検証した」と言って確かめていない、図を合わせ込む、慣習の記号に戻る、要の式を別の系から流用する、といった誤りが出る〔5〕 | RULES.md「誠実さ」、CONVENTIONS.md、referee の点検項目（要の式は独立に導き直す） |
| 長時間の自律作業には、進捗を判定する手段（テストオラクル）と、失敗したやり方の記録が欠かせない〔6〕 | GOAL.md「検証の基準」、`tools/<topic>/check.sh`、NOTES.md |
| 完了を早く宣言しがち。基準は既定で未達にしておき、証拠があるときだけ達成にする〔2〕〔7〕 | claims.json の status と lint、完了監査 |
| 規約は守られないことがある。決定的なチェックで止める〔4〕〔8〕 | lint.py と CI（人間管理ファイルの保護、journal の追記のみ、主張の削除禁止、theory/ の書きかけ禁止） |
| 検算の出力が多いと文脈を汚す。時間感覚が無いので重い検算を回し続ける〔8〕 | check_all.sh は1トピック1行、詳細はログへ。`CHECK_FAST` |
| 同じ失敗を繰り返す空回りが起きる〔9〕 | 同じタスクが2回未完なら質問に回して別のタスクへ |
| 新しいモデルは慎重すぎて既知のやり方に留まることがある〔10〕 | 行き詰まったら質的に異なる方針を2つ以上比べる |
| ハーネスの部品はどれも「モデルにはこれができない」という仮定で、モデルが良くなると古くなる〔3〕〔11〕 | 部品を分けておき、モデル更新時に外して試せるようにした（例：差分ごとの査読をやめて完了監査だけにする） |
| クラウド定期実行は GitHub イベントで起動でき、auto mode で走る。クラウドでは `gh` の GraphQL（`gh pr list` など）が使えない〔12〕 | マージ駆動のトリガー、preflight は REST（`gh api`）で PR を確認 |

出典：

1. Geoffrey Huntley「Ralph Wiggum as a "software engineer"」（ghuntley.com/ralph）
2. Anthropic「Effective harnesses for long-running agents」（2025-11）https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
3. Anthropic「Harness design for long-running application development」（2026-03）https://www.anthropic.com/engineering/harness-design-long-running-apps
4. Claude Code ドキュメント「Best practices」（検証の与え方、敵対的レビュー）https://code.claude.com/docs/en/best-practices
5. Matthew Schwartz「Vibe physics: The AI grad student」（2026-03）https://www.anthropic.com/research/vibe-physics
6. Siddharth Mishra-Sharma「Long-running Claude for scientific computing」（2026-03）https://www.anthropic.com/research/long-running-claude
7. anthropics/cwc-long-running-agents（default-FAIL の契約、新しい文脈の評価役、引き継ぎ）https://github.com/anthropics/cwc-long-running-agents
8. Nicholas Carlini「Building a C compiler with a team of parallel Claudes」（2026-02）https://www.anthropic.com/engineering/building-c-compiler
9. Ralph ループの運用上の失敗例をまとめた各種記事（空回り・合わせ込み・誤りの積み上がり）
10. Anthropic「Designing more efficient quantum circuits with Claude」（2026-10）https://www.anthropic.com/research/designing-efficient-quantum-circuits
11. Anthropic「Agent harness design: 3 patterns for harnessing Claude's intelligence」（2026-04）https://claude.com/blog/harnessing-claudes-intelligence
12. Claude Code ドキュメント「Automate work with scheduled tasks」「Configure cloud environments」「Keep Claude working toward a goal」https://code.claude.com/docs/en/routines

## 由来

Ralph loop（Geoffrey Huntley）：同じプロンプトをエージェントに繰り返し与え、状態をリポジトリ内のファイルに外部化する手法。ここではクラウドの定期実行とマージで駆動するので厳密な `while` ループではないが、「状態はファイル、プロンプトは不変、1回1タスク、関門で押し返す」という骨格は同じ。
