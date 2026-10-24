# TODO(human) 研究テーマ名

TODO(human)：この研究の概要を数行で書く。

## 構成

| パス | 内容 |
|---|---|
| `theory/` | 確定した理論（トピックごとのディレクトリ）。`theory/CONVENTIONS.md` に単位・符号・記号の約束 |
| `idea/` | 下書き・途中計算・没案 |
| `refs/` | 先行研究 |
| `tools/` | 数値検算。`tools/check_all.sh` で全部走る |
| `ralph/` | 自律研究ループの運用ファイル → [ralph/README.md](ralph/README.md) |

## 進み具合

- 主要な結果とその検証状態：[ralph/claims.json](ralph/claims.json)（`python3 ralph/bin/lint.py` で問いごとに集計）
- イテレーションの記録：[ralph/journal/](ralph/journal/)
- 人間への質問：[ralph/QUESTIONS.md](ralph/QUESTIONS.md)
