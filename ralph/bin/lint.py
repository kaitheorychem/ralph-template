#!/usr/bin/env python3
"""Ralph ループの機械チェック。エージェントのコミット前と CI で使う。

使い方:
  python3 ralph/bin/lint.py
      作業ツリーを点検する（主張台帳・journal・査読レポート・theory/ の書きかけ・tools/ の構成）。
  python3 ralph/bin/lint.py --base origin/main --loop
      ループの PR として、ベースとの差分も点検する（人間が管理するファイルの変更、
      既存の journal・査読レポートの書き換え、主張の削除、journal の追加漏れ）。

終了コード: 0 = エラーなし（警告はあってよい）/ 1 = エラーあり
標準ライブラリだけで動く。
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

STATUSES = ("draft", "checked", "refereed", "refuted")
JOURNAL_RE = re.compile(r"^(\d{4})-(\d{4}-\d{2}-\d{2})\.md$")
REVIEW_RE = re.compile(r"^(\d{4})-[A-Za-z0-9_.-]+\.md$")
VERDICT_RE = re.compile(r"^判定[:：]\s*(PASS|NEEDS_WORK)\s*$", re.M)
MARKER_RE = re.compile(r"\b(TODO|FIXME|WIP|XXX)\b")

# ループ（エージェント）が変更してはいけないパス。refs/notes/ だけは要約ノート置き場として書いてよい。
PROTECTED = [
    "AGENTS.md", "CLAUDE.md", "README.md",
    "ralph/PROMPT.md", "ralph/RULES.md", "ralph/GOAL.md", "ralph/README.md",
    "ralph/config.env", "ralph/loop.sh", "ralph/bin/*", "ralph/ci/*",
    ".claude/*", ".github/*", "tools/check_all.sh", "refs/*",
]
PROTECTED_EXCEPT = ["refs/notes/*", "refs/notes"]

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def repo_root() -> Path:
    try:
        return Path(git("rev-parse", "--show-toplevel").strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parents[2]


def strip_anchor(p: str) -> str:
    return p.split("#", 1)[0]


# ---------------------------------------------------------------- 作業ツリーの点検

def check_journal(root: Path) -> None:
    d = root / "ralph/journal"
    nums: dict[int, str] = {}
    for f in sorted(d.glob("*.md")) if d.is_dir() else []:
        m = JOURNAL_RE.match(f.name)
        if not m:
            err(f"journal のファイル名が NNNN-YYYY-MM-DD.md でない: {f.relative_to(root)}")
            continue
        n = int(m.group(1))
        if n in nums:
            err(f"journal の番号 {n:04d} が重複: {nums[n]} と {f.name}")
        nums[n] = f.name
        text = f.read_text(encoding="utf-8")
        first = text.lstrip().splitlines()[0] if text.strip() else ""
        h = re.match(r"^#\s*イテレーション\s*(\d+)", first)
        if not h:
            warn(f"journal の見出しが「# イテレーションN：…」でない: {f.name}")
        elif int(h.group(1)) != n:
            warn(f"journal の見出しの番号 {h.group(1)} がファイル名の番号 {n} と違う: {f.name}")
        if len(text.splitlines()) > 25:
            warn(f"journal が長い（{len(text.splitlines())} 行。20 行以内が目安）: {f.name}")
    if nums:
        missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
        if missing:
            warn(f"journal の番号に欠番がある: {', '.join(f'{x:04d}' for x in missing[:10])}")


def check_reviews(root: Path) -> None:
    d = root / "ralph/reviews"
    for f in sorted(d.glob("*.md")) if d.is_dir() else []:
        if not REVIEW_RE.match(f.name):
            err(f"査読レポートのファイル名が NNNN-名前.md でない: {f.relative_to(root)}")
        if not VERDICT_RE.search(f.read_text(encoding="utf-8")):
            err(f"査読レポートに「判定: PASS」か「判定: NEEDS_WORK」の行が無い: {f.relative_to(root)}")


def final_verdict(text: str) -> str | None:
    """査読レポートの最終判定。再査読があればレポートに判定が複数並ぶので、最後のものを採る。"""
    found = VERDICT_RE.findall(text)
    return found[-1] if found else None


def load_claims(text: str, where: str) -> list[dict] | None:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        err(f"{where} が JSON として読めない: {e}")
        return None
    claims = data.get("claims") if isinstance(data, dict) else None
    if not isinstance(claims, list):
        err(f"{where} に claims の配列が無い")
        return None
    return claims


def check_claims(root: Path) -> list[dict]:
    path = root / "ralph/claims.json"
    if not path.exists():
        err("ralph/claims.json が無い")
        return []
    claims = load_claims(path.read_text(encoding="utf-8"), "ralph/claims.json") or []
    seen: set[str] = set()
    for i, c in enumerate(claims):
        if not isinstance(c, dict):
            err(f"claims[{i}] がオブジェクトでない")
            continue
        cid = str(c.get("id", ""))
        tag = f"主張 {cid or f'claims[{i}]'}"
        if not re.fullmatch(r"C\d+", cid):
            err(f"{tag}: id は C1, C2, … の形にする")
        if cid in seen:
            err(f"{tag}: id が重複")
        seen.add(cid)
        if not str(c.get("statement", "")).strip():
            err(f"{tag}: statement（主張の一文）が空")
        status = c.get("status")
        if status not in STATUSES:
            err(f"{tag}: status は {'/'.join(STATUSES)} のどれか（今は {status!r}）")
            continue
        if not c.get("question"):
            warn(f"{tag}: question（GOAL.md の問い Q1… との対応）が無い")
        loc = c.get("location")
        if status in ("checked", "refereed"):
            if not loc:
                err(f"{tag}: location（theory/ 内の場所）が無い")
            elif not (root / strip_anchor(loc)).exists():
                err(f"{tag}: location が存在しない: {loc}")
        elif status == "draft" and loc and not (root / strip_anchor(loc)).exists():
            warn(f"{tag}: location がまだ存在しない: {loc}")
        if status in ("checked", "refereed"):
            chk = c.get("check")
            if not chk:
                err(f"{tag}: status={status} なのに check（検算の場所 tools/…）が無い")
            elif not (root / strip_anchor(chk)).exists():
                err(f"{tag}: check が存在しない: {chk}")
        if status == "refereed":
            rev = c.get("review")
            if not rev:
                err(f"{tag}: status=refereed なのに review（査読レポート）が無い")
            elif not (root / rev).exists():
                err(f"{tag}: review が存在しない: {rev}")
            elif final_verdict((root / rev).read_text(encoding="utf-8")) != "PASS":
                err(f"{tag}: status=refereed だが {rev} の最終判定（最後の「判定:」行）が PASS でない")
    return claims


def check_theory(root: Path) -> None:
    d = root / "theory"
    if not d.is_dir():
        return
    for f in sorted(d.rglob("*.md")):
        rel = f.relative_to(root)
        for ln, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if "TODO(human)" in line:
                warn(f"{rel}:{ln}: TODO(human) が残っている（人間の記入待ち）")
                line = line.replace("TODO(human)", "")
            m = MARKER_RE.search(line)
            if m:
                err(f"{rel}:{ln}: theory/ に書きかけの印 {m.group(1)} がある（書きかけは idea/ へ）")
    for sub in sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith(".")):
        if not re.fullmatch(r"\d{2}-[a-z0-9_]+", sub.name):
            warn(f"theory/{sub.name}: トピック名は「2桁番号-英小文字_」にする（例 00-basic_model）")
        if not (sub / "README.md").exists():
            warn(f"theory/{sub.name}/README.md が無い")


def check_tools(root: Path) -> None:
    d = root / "tools"
    if not d.is_dir():
        return
    for sub in sorted(p for p in d.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        if not (sub / "check.sh").exists():
            warn(f"tools/{sub.name}/check.sh が無い（tools/check_all.sh から実行されない）")
        if not (sub / "README.md").exists():
            warn(f"tools/{sub.name}/README.md が無い")


def check_plan(root: Path) -> None:
    p = root / "ralph/PLAN.md"
    if not p.exists():
        err("ralph/PLAN.md が無い")
    elif "## 必須" not in p.read_text(encoding="utf-8"):
        warn("ralph/PLAN.md に「## 必須」節が無い")


# ---------------------------------------------------------------- ベースとの差分の点検

def is_protected(path: str) -> bool:
    if any(fnmatch.fnmatch(path, pat) for pat in PROTECTED_EXCEPT):
        return False
    return any(fnmatch.fnmatch(path, pat) for pat in PROTECTED)


def check_diff(root: Path, base: str, loop: bool, claims: list[dict]) -> None:
    try:
        mb = git("merge-base", base, "HEAD").strip()
    except subprocess.CalledProcessError:
        err(f"ベース {base} と HEAD の共通祖先が見つからない（git fetch したか？）")
        return
    # コミット済みと未コミットの変更（作業ツリー）をまとめて見る。新規の未追跡ファイルも含める。
    changes: list[tuple[str, str]] = []
    for line in git("diff", "--name-status", "--no-renames", mb).splitlines():
        st, _, path = line.partition("\t")
        changes.append((st[0], path))
    for path in git("ls-files", "--others", "--exclude-standard").splitlines():
        changes.append(("A", path))

    if loop:
        for st, path in changes:
            if is_protected(path):
                err(f"人間が管理するファイルを変更している: {path}（必要なら QUESTIONS.md で提案する）")
            if st in ("M", "D") and re.match(r"ralph/(journal|reviews)/.+\.md$", path):
                err(f"既存の journal / 査読レポートを書き換え・削除している: {path}（訂正は新しいファイルで）")
        if not any(st == "A" and re.match(r"ralph/journal/\d{4}-.+\.md$", p) for st, p in changes):
            err("このイテレーションの journal（ralph/journal/ の新しいファイル）が追加されていない")

    try:
        old_text = git("show", f"{mb}:ralph/claims.json")
    except subprocess.CalledProcessError:
        return
    old = load_claims(old_text, f"{base} の ralph/claims.json") or []
    now = {str(c.get("id")) for c in claims if isinstance(c, dict)}
    gone = [str(c.get("id")) for c in old if isinstance(c, dict) and str(c.get("id")) not in now]
    if gone:
        err(f"主張が台帳から消えている: {', '.join(gone)}（誤りなら削除せず status を refuted にする）")


# ---------------------------------------------------------------- 本体

def summarize(claims: list[dict]) -> str:
    by_q: dict[str, dict[str, int]] = {}
    for c in claims:
        if isinstance(c, dict) and c.get("status") in STATUSES:
            q = str(c.get("question") or "?")
            by_q.setdefault(q, dict.fromkeys(STATUSES, 0))[c["status"]] += 1
    if not by_q:
        return "主張台帳: まだ主張なし"
    parts = []
    for q in sorted(by_q):
        s = by_q[q]
        parts.append(f"{q}: " + " ".join(f"{k}={v}" for k, v in s.items() if v))
    return "主張台帳: " + " / ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="比較するベース（例 origin/main）")
    ap.add_argument("--loop", action="store_true", help="ループの PR として差分の規則も点検する")
    a = ap.parse_args()
    root = repo_root()

    check_journal(root)
    check_reviews(root)
    claims = check_claims(root)
    check_theory(root)
    check_tools(root)
    check_plan(root)
    if a.base:
        check_diff(root, a.base, a.loop, claims)
    elif a.loop:
        err("--loop には --base が必要")

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(summarize(claims))
    print(f"lint: エラー {len(errors)} 件、警告 {len(warnings)} 件")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
