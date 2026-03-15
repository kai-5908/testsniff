# Git 操作 skill 導入計画

## Status

- Status: Completed
- Owner: 現在の実装作業
- Started: 2026-03-15
- Completed: 2026-03-15

## 問題設定

このリポジトリでは trunk-based development、Issue / PR template、実装前 plan 承認という運用が整ってきましたが、`git pull`、`git commit`、`git push` の進め方はまだ repo-local な skill として明文化されていません。

そのため、Git 操作のたびに同じ判断を毎回やり直す必要があります。

特に次を repo 運用と揃える必要があります。
- `main` へ直接 push しない
- commit メッセージが現在の運用と一致する
- push 時に PR template と Issue 関連付けを確認する
- stale branch の更新は merge-based に行う

## スコープ

今回含めるもの:
- `pull` skill の追加
- `commit` skill の追加
- `push` skill の追加
- これら 3 skill の利用ルール文書追加
- `AGENTS.md` と関連 index への反映

今回含めないもの:
- GitHub Actions による強制
- git alias や shell function の配布
- rebase 運用への変更

## 目標状態

目標とする運用:
1. branch 更新が必要なときは `pull` skill を使う
2. commit 作成時は `commit` skill を使う
3. push と PR 更新時は `push` skill を使う
4. Git 操作が repo の branch / PR / docs ルールと矛盾しない

## 作業流れ

### 1. 参照 skill の読み替え

- Symphony の `pull` / `commit` / `push` skill を読む
- この repo に不要な手順を落とす
- repo 固有ルールを追加する

### 2. skill 本体作成

- `.codex/skills/pull/SKILL.md`
- `.codex/skills/commit/SKILL.md`
- `.codex/skills/push/SKILL.md`

### 3. 利用ルール文書

- Git 操作時に skill を使う条件を定義する
- branch / PR / issue 運用との整合を明文化する

### 4. 入口更新

- `AGENTS.md` と design docs index から辿れるようにする

## 検証計画

最低限の確認:
- 各 skill が具体的な利用場面と禁止事項を持っている
- push skill が `.github/pull_request_template.md` を前提にしている
- branch ルールと矛盾しない

## 完了条件

- `pull` / `commit` / `push` の repo-local skill が追加されている
- 利用ルール文書が追加されている
- `AGENTS.md` と index から参照できる

## 意思決定ログ

- 2026-03-15: Git 操作は汎用手順ではなく、この repo の trunk-based / Issue / PR 運用に合わせた repo-local skill に寄せる方針を採用。

## リスク

- skill に書いた運用と実際の GitHub 側設定がずれる可能性がある
- `pull` の merge-based 更新は、rebase を好むユーザーの期待と異なる可能性がある
