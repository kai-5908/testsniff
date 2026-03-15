---
name: push
description: Use when asked to push the current branch or create/update a pull request in this repository. Push only topic branches, run the repo validation commands first, and create or refresh the PR so it matches .github/pull_request_template.md and the linked Issue.
---

# Push

この skill は、この repo の branch push と PR 作成・更新の手順です。

## 使う場面

- ユーザーが `pushして` と依頼した
- 現在の branch を origin に公開したい
- PR を新規作成または更新したい

## 前提

- `gh` CLI が使えること
- current branch は `main` ではなく topic branch であること
- 必要な validation がローカルで完了していること
- local hook が有効なら `pre-push` が追加のゲートになること

## 標準手順

1. `git branch --show-current` で branch を確認する
2. `main` なら push を止め、通常は topic branch で作業する
3. `git status --short` で未整理の変更がないことを確認する
4. repo の必須チェックを実行する
5. `git push -u origin HEAD` で push する
6. non-fast-forward なら `pull` skill で branch を同期してから再 push する
7. PR が無ければ作成し、あれば更新する
8. PR body は `.github/pull_request_template.md` に合わせて具体的に埋める
9. PR title / body が最新のスコープと一致しているか確認する

## 最低限の validation

```bash
uv run ruff check src tests
uv run ty check src
uv run pytest -q
```

必要なら追加で:
- `uv build`

local hook が有効な場合、push 時に同じ最小ゲートが再度実行されます。

## PR 作成・更新ルール

- PR は関連 Issue を明記する
- `Closes #...` または `Related #...` を適切に書く
- DoR / DoD / 受け入れ条件の確認欄を実際の内容で埋める
- placeholder を残さない
- branch のスコープが変わったら title / body を更新する

## やってはいけないこと

- `main` へ直接 push すること
- validation なしで PR を更新すること
- stale な PR body をそのまま流用すること
- 通常の失敗時に `--force` を使うこと

`--force-with-lease` は、history を意図的に書き換えた場合に限って最後の手段として使います。

## push 後の応答

- PR URL を共有する
- 実行した validation を要約する
- scope 変更や残課題があれば短く添える
