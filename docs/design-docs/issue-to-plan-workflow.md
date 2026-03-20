# Issue To Plan Workflow

- Status: Adopted
- Validation: Conceptual

## Goal

GitHub Issue を起点に実装する際、issue の内容を人間が理解・質問・修正・承認できる実行計画へ変換してから作業に入る workflow を定義します。

## Core Rules

### Rule 1: Issue 起点の作業は task 専用 worktree を先に作る

Issue を起点に plan や実装へ進むときは、まず `main` から task 専用の `git worktree` を作成します。

worktree の作成先は、リポジトリ直下の `worktrees/<topic>/` を標準とします。

plan 文書や関連 docs は、その task worktree 内で作成または更新します。

### Rule 2: Issue 起点の実装は plan から始める

GitHub Issue を起点として code / docs / config の変更に着手する場合、実装前に `docs/exec-plans/active/` へ実行計画を作成または更新します。

### Rule 3: issue は先に取得して要約する

plan を書く前に、対象 issue のタイトル・本文・必要なメタ情報を取得し、問題設定と作業範囲を整理します。

### Rule 4: repo-local skill を使う

Issue 起点の plan 作成には、repo-local skill [issue-to-plan](/home/aoi_takanashi/testsniff/.codex/skills/issue-to-plan/SKILL.md) を使います。

skill が参照できない場合でも、同等の手順を手動で再現しなければなりません。

### Rule 5: plan は日本語で書く

Issue から起こす実行計画の本文は日本語で記述します。

必要に応じて rule ID、コマンド、ファイルパス、識別子は英語のままで構いません。

### Rule 6: 承認前は実装に入らない

plan を作成したら、その要点と仮定・未解決事項をユーザーへ共有し、明示的な承認を待ちます。

承認前に実装へ進んではいけません。

### Rule 7: issue の受け入れ条件を plan に写像する

issue に DoR、DoD、受け入れ条件、依存関係がある場合、plan 側にも対応する形で落とし込みます。

不足がある場合は、仮定か未解決事項として明示します。

## Recommended Flow

1. `main` から `worktrees/<topic>/` へ task 専用の `git worktree` を作成する
2. 対象 issue を取得する
3. issue の目的、スコープ、制約、依存関係を整理する
4. `docs/exec-plans/active/` に日本語 plan を作成する
5. 要点をユーザーへ共有し、質問・修正・承認を受ける
6. 承認後に実装する
7. 完了時に plan を `completed/` へ移動する

## Related Docs

- [docs/PLANS.md](/home/aoi_takanashi/testsniff/docs/PLANS.md)
- [docs/design-docs/issue-management-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-management-rules.md)
- [docs/design-docs/pull-request-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/pull-request-rules.md)
