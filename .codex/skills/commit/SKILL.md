---
name: commit
description: Use when asked to create a git commit in this repository. Inspect the actual staged and unstaged changes, follow the repo's conventional-style commit subjects, commit only scoped work, and include validation notes that match what was actually run.
---

# Commit

この skill は、この repo で一貫した commit を作るための手順です。

## 使う場面

- ユーザーが `commitして` と依頼した
- 変更を1つの commit にまとめたい
- PR 前に作業単位を確定したい

## この repo の前提

- 1 PR は原則 1 Task
- commit も PR のスコープを壊さない粒度に寄せる
- commit subject は conventional-style を使う
- `amend` は明示依頼がない限りしない

## commit message の方針

subject 形式:

```text
type: summary
type(scope): summary
```

主な type:
- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `chore`

subject は:
- 命令形または簡潔な現在形
- 72 文字以内を目安
- 末尾に句点を付けない

body には必要に応じて次を含めます。
- Summary: 何を変えたか
- Rationale: なぜ変えたか
- Tests: 実行した確認

## 標準手順

1. セッションの意図と対象タスクを確認する
2. `git status --short` で変更範囲を確認する
3. `git diff` と `git diff --staged` で実際の差分を確認する
4. commit に含めるべき変更だけを stage する
5. スコープ外の変更や生成物が混ざっていないか確認する
6. 変更内容に合う commit message を作る
7. `git commit -F <message-file>` で複数行 message を作る

commit 前に local hook が有効なら、`pre-commit` が次を実行します。
- `git diff --cached --check`
- staged Python file に対する `uv run ruff check`

## やってはいけないこと

- unrelated change をまとめて commit すること
- 実際に走らせていない test を message に書くこと
- repo の運用にない trailer を勝手に付けること
- 明示依頼なく `git commit --amend` すること

## 補足

- 既存運用上、Codex の `Co-authored-by` trailer は必須にしません
- commit 前に docs 同期が必要な変更なら、同じ commit に含めることを検討します
