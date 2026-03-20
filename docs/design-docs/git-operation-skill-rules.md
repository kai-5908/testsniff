# Git Operation Skill Rules

- Status: Adopted
- Validation: Conceptual

## Goal

このリポジトリでの `git pull`、`git commit`、`git push` を、repo-local skill を通じて一貫したやり方で行うためのルールを定義します。

## Core Rules

### Rule 1: Git 操作は対応する skill を使う

次の操作を行うときは、対応する repo-local skill を使います。

- branch 更新: [pull skill](/home/aoi_takanashi/testsniff/.codex/skills/pull/SKILL.md)
- commit 作成: [commit skill](/home/aoi_takanashi/testsniff/.codex/skills/commit/SKILL.md)
- push / PR 更新: [push skill](/home/aoi_takanashi/testsniff/.codex/skills/push/SKILL.md)

### Rule 2: 並行作業は `git worktree` を前提にする

複数タスクを並行して進める場合は、task ごとに専用の `git worktree` を作成します。

新しい task を始めるときは、`main` を起点にリポジトリ直下の `worktrees/<topic>/` へ topic branch 用の worktree を切り、その worktree 内で code / docs / plan を作業します。

### Rule 3: `main` へ直接 push しない

通常の開発作業では、`main` へ直接 push しません。

push は topic branch に対して行い、PR を通して `main` にマージします。

### Rule 4: pull は merge-based に行う

branch 同期は、既定では rebase ではなく merge-based に行います。

この repo の trunk-based workflow では、`origin/main` を current topic branch に merge して追従します。

### Rule 5: commit は実際の差分と一致していなければならない

commit message は staged diff と一致していなければなりません。

unrelated change をまとめたり、実行していない validation を書いたりしてはいけません。

### Rule 6: push 時は PR template と Issue を同期する

push / PR 更新時は `.github/pull_request_template.md` を基準に PR body を埋め、関連 Issue を明示します。

### Rule 7: Git 操作は repo の品質ゲートに従う

少なくとも次の validation を基準にします。

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`

変更内容によっては追加の確認が必要です。

### Rule 8: local hooks と矛盾する操作をしない

`pre-commit` と `pre-push` の local hook は、日常運用の標準ゲートとして扱います。

hook が失敗した場合は、原則として原因を解消してから commit / push を再実行します。

## Related Docs

- [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md)
- [docs/design-docs/local-git-hook-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/local-git-hook-rules.md)
- [docs/design-docs/pull-request-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/pull-request-rules.md)
- [docs/design-docs/issue-management-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-management-rules.md)
