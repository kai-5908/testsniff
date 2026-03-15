---
name: pull
description: Use when the current local branch needs to be updated from origin or synced with origin/main in this repository. Follow the repo's trunk-based workflow, prefer merge-based updates over rebase, keep work on the current topic branch, and rerun the repo validation commands after conflict resolution.
---

# Pull

この skill は、この repo の topic branch を安全に更新するための手順です。

## 使う場面

- ユーザーが `pull`、`update branch`、`main を取り込んで` のように依頼した
- push が non-fast-forward で拒否された
- current branch を `origin/main` に追従させたい

## この repo の前提

- 永続ブランチは `main` のみ
- 作業は topic branch 上で行う
- branch 更新は merge-based に行い、rebase を既定にしない
- `main` へ直接作業しない

## 標準手順

1. `git status --short` で作業ツリーを確認する
   未コミット変更がある場合は、commit または stash が必要です。
2. `git branch --show-current` で current branch を確認する
   `main` にいる場合は、通常はそこで pull 作業を進めず、意図を確認します。
3. `git fetch origin` で最新 refs を取得する
4. current branch の remote 更新を先に取り込む
   `git pull --ff-only origin $(git branch --show-current)`
5. `origin/main` を current branch に merge する
   `git -c merge.conflictstyle=zdiff3 merge origin/main`
6. conflict が出たら解消し、`git add ...` 後に merge を完了する
7. merge 後に repo の必須チェックを実行する

## conflict 解消時のルール

- まず `git status` と `git diff --merge` で差分を理解する
- 片側を機械的に採用するのではなく、repo の現在の意図を優先する
- user-facing behavior や docs 契約に関わる conflict は、必要なら根拠を明記してから解消する
- generated file より source file を先に直す

## 最低限の確認コマンド

```bash
uv run ruff check src tests
uv run ty check src
uv run pytest -q
```

## やってはいけないこと

- 既定動作として rebase を使うこと
- `main` に対して無思慮に merge commit を積むこと
- conflict の意味を確認せずに `ours` / `theirs` を濫用すること

## ユーザーに確認すべき最小条件

次のときだけ確認します。

- current branch が意図した branch か分からない
- conflict が product behavior の選択を含み、コードや docs から決められない
- 解消により user-facing contract が変わる可能性がある
