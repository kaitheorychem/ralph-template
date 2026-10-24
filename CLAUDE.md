@AGENTS.md

## Claude Code で使うもの

- 査読：`referee` サブエージェント（[.claude/agents/referee.md](.claude/agents/referee.md)）。theory/ に結果を足した・直したら依頼する。読み取り専用で、新しい文脈から点検する。
- 対話セッションの引き継ぎ：`/ralph-handoff`（[.claude/skills/ralph-handoff/SKILL.md](.claude/skills/ralph-handoff/SKILL.md)）。
- クラウドセッションでは開始時に requirements.txt のパッケージが入る（.claude/settings.json の SessionStart フック）。
- 論文 PDF など大きな資料は、サブエージェントに読ませて要点だけを受け取り、メインの文脈を節約する。
