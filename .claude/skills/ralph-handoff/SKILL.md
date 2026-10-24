---
name: ralph-handoff
description: 対話セッションで進めた研究を Ralph ループに引き継ぐ。PLAN.md・claims.json・NOTES.md を更新し、journal に「（対話）」エントリを追加する。対話セッションを終える前に使う。
disable-model-invocation: true
---

このセッションで行った研究作業を、Ralph ループ（ralph/PROMPT.md）が次のイテレーションで続きから拾えるように記録する。新しい研究はしない。

1. `ralph/RULES.md`（特に「主張台帳」「NOTES.md」「journal」）と `ralph/PLAN.md`・`ralph/claims.json` を読む。
2. この会話で行ったこと・分かったこと・未完のことを整理する。`git status` と `git diff` で実際の変更を確かめ、会話の記憶だけで書かない。
3. 次を更新する：
   - `ralph/PLAN.md`：終わったタスクを「完了」へ、新しく見つかったタスクを適切な節へ。会話で人間が示した方針は「必須」か「発展」のタスクとして書く。
   - `ralph/claims.json`：theory/ に足した・直した結果を登録・更新する。検算や査読をしていないものは `draft` のまま。内容を直した主張は `status` を下げる。
   - `ralph/NOTES.md`：駄目だったやり方とその理由、落とし穴があれば1〜2行で。
   - `ralph/journal/`：新しいファイルを1つ作る。見出しは `# イテレーションN：<内容>（対話）（YYYY-MM-DD）`。
   - 人間の判断待ちの事項があれば `ralph/QUESTIONS.md` に追記する。
4. `tools/check_all.sh` と `python3 ralph/bin/lint.py` を実行し、結果を journal の「検証」に書く。
5. 変更をコミットする（メッセージは `ralph: 対話セッションの引き継ぎ` など）。push と PR は人間の指示に従う。
6. 何を記録したかを3行以内で報告する。
