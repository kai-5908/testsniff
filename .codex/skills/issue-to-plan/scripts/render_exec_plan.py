from __future__ import annotations

import json
import pathlib
import sys
from typing import Any


def _label_names(issue: dict[str, Any]) -> str:
    labels = issue.get("labels", [])
    names = [label["name"] for label in labels if isinstance(label, dict) and "name" in label]
    return ", ".join(names) if names else "なし"


def main() -> int:
    if len(sys.argv) != 2:
        print(
            (
                "usage: python "
                ".codex/skills/issue-to-plan/scripts/render_exec_plan.py "
                "<issue-json-path>"
            ),
            file=sys.stderr,
        )
        return 1

    issue_path = pathlib.Path(sys.argv[1])
    issue = json.loads(issue_path.read_text(encoding="utf-8"))

    number = issue["number"]
    title = issue["title"]
    body = (issue.get("body") or "").strip()
    url = issue.get("url", "")

    markdown = f"""# Issue #{number} 実行計画

## Status

- Status: Draft
- Source Issue: #{number}
- Source URL: {url}

## 問題設定

Issue `#{number} {title}` を起点として、実装または文書変更に入る前の計画を整理します。

issue の要約:

{body or "- issue 本文は未記入です。"}

## issue メタ情報

- labels: {_label_names(issue)}

## スコープ

- [ここにこの作業で含める範囲を書く]

## 非ゴール

- [ここにこの作業で扱わないことを書く]

## 仮定と未解決事項

- [issue から推定した前提]
- [確認したい点]

## 作業流れ

### 1. 調査・仕様確認

- [必要な確認作業]

### 2. 実装または文書変更

- [主要な変更内容]

### 3. 検証

- [テスト・確認内容]

## 検証計画

- [実行するコマンドやレビュー内容]

## 完了条件

- [この plan が完了と見なせる条件]
"""

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
