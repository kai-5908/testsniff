---
name: issue-to-plan
description: Use when work starts from a GitHub Issue and the team wants a Japanese execution plan reviewed and approved before implementation. Fetch the issue, draft or update an execution plan under docs/exec-plans/active, summarize assumptions and questions, and stop for human approval before making implementation changes.
---

# Issue To Plan

GitHub Issue を起点に実装する前に、issue を取得して日本語の実行計画を作成し、人間承認を待つための workflow です。

この skill は、実装前の段階で使います。

## 使う場面

次のいずれかに当てはまるときはこの skill を使います。

- ユーザーが Issue 番号や Issue URL を指定して実装や調査を依頼した
- ユーザーが「issue を見て plan を作ってから進めたい」と依頼した
- Issue 起点で code / docs / config の変更を伴う作業に入る

## やること

1. `main` からリポジトリ直下の `worktrees/<topic>/` に task 専用の `git worktree` を作成する
2. `gh issue view` で issue を取得する
3. issue の目的、スコープ、DoR、DoD、受け入れ条件、依存関係を整理する
4. task worktree 上の `docs/exec-plans/active/` に日本語の実行計画を作成または更新する
5. 計画の要点、仮定、未解決事項をユーザーに共有する
6. 承認が出るまで実装に入らない

## やってはいけないこと

- issue を見ただけでコード実装に入ること
- plan を作らずに「そのまま進める」こと
- 承認前に user-facing behavior を変更すること

軽微な質問への回答だけで終わる場合はこの限りではありません。実装や文書変更に進むときは plan を起こします。

## 標準手順

### 1. task worktree を作る

この skill を始める前に、`main` を起点にリポジトリ直下の `worktrees/<topic>/` へ task 専用 worktree を用意しておきます。

例:

```bash
git worktree add worktrees/<topic> -b <topic-branch> main
```

その worktree に移動してから、以降の issue 取得と plan 作成を進めます。

### 2. issue を取得する

最小の取得例:

```bash
gh issue view <number> --json number,title,body,url,labels,assignees
```

繰り返し使う場合は、必要に応じて次を使ってください。

```bash
bash .codex/skills/issue-to-plan/scripts/fetch_issue_context.sh <number>
```

`gh` 実行に承認や認証が必要なら、その旨を踏まえて許可を求めます。

### 3. plan 草案を作る

issue 取得後は、次のどちらかで plan 草案を作ります。

- 手で `docs/exec-plans/active/` に書く
- 補助スクリプトで草案を出し、それを編集する

補助スクリプト例:

```bash
bash .codex/skills/issue-to-plan/scripts/fetch_issue_context.sh <number> > /tmp/issue-<number>.json
python .codex/skills/issue-to-plan/scripts/render_exec_plan.py /tmp/issue-<number>.json
```

## plan の必須内容

plan には最低限次を含めます。

- 問題設定
- source issue
- スコープ
- 非ゴール
- 仮定と未解決事項
- 作業流れ
- 検証計画
- 完了条件

plan 本文は日本語で書きます。

## 承認待ちの出し方

plan を作成したら、実装に進む前に次をユーザーへ共有します。

- どの issue を起点にしたか
- plan の要点
- 仮定や確認したい点
- 承認後に着手する旨

この skill のゴールは、承認可能な plan を作るところまでです。ユーザーが明示的に承認するまでは実装へ進みません。
