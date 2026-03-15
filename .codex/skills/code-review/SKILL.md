---
name: code-review
description: Review code, tests, docs, configuration, or diffs from a general software engineering perspective, then apply this repository's architecture, quality, security, and review rules. Use when the user asks for a code review, PR review, change review, design review, or wants bugs, regressions, and missing validation prioritized with concrete evidence.
---

# Code Review

一般的なソフトウェアエンジニアリング観点で一次レビューし、その後でこの repo 固有の制約と運用ルールを重ねてレビューするための skill です。

repo ローカルの作法だけに閉じず、まず correctness、契約、設計適合、テスト妥当性を確認します。そのうえで `testsniff` 固有の境界、静的解析の制約、文書同期、PR 検証ルールを追加で確認します。

## Review Stance

- まず一般原則で評価し、その後で repo 固有ルールを確認する
- findings は好みではなく、バグ、回帰、保守性悪化、検証不足のリスクに結び付ける
- 事実と推測を分ける。断定できない点は open question に分離する
- 変更差分だけで閉じず、接続先の契約、呼び出し側、関連 docs まで最小限読む
- findings がなければ、その旨を明記し、未確認範囲や残留リスクを書く

## Standard Workflow

### 1. 対象と契約を特定する

- diff、対象ファイル、関連テスト、要求文書を読む
- 何の振る舞い、インターフェース、設定契約が変わるかを整理する
- 差分だけでは判断できないときは、接続する呼び出し元や利用側を最小限読む

### 2. 一般的なコードレビューを行う

- まず `references/general-review-checklist.md` を使って一次レビューする
- correctness、behavior regression、境界条件、設計適合、テスト妥当性を優先する
- 単なるスタイル差分ではなく、変更の品質と統合の完了度を見る

### 3. この repo 固有の観点を追加する

- 一次レビューの後で `references/testsniff-review-checklist.md` を使う
- layer 境界、静的解析の非実行原則、rule 実装の完了条件、docs 同期、PR 検証を確認する
- repo 固有ルールに適合していても、一般観点で危険なら finding として残す

### 4. 証拠を固める

- 各 finding に file/line を付ける
- `何が起きているか` と `なぜ問題か` を分ける
- 未実施テストや未確認前提があれば明記する

### 5. findings first で報告する

- 重大度順に findings を並べる
- 1 件ごとに Evidence、Why、Impact、Fix を含める
- findings がない場合も、見た範囲、未確認範囲、confidence を残す

## Review Priorities

1. 契約や振る舞いの破壊
2. 高リスクな correctness / reliability / security 問題
3. 境界違反や責務崩れ
4. テスト、検証、docs の統合漏れ
5. 将来の変更耐性を下げる設計劣化

## Output Contract

- findings を先に出す
- 各 finding は `severity`, `path:line`, `title`, `Evidence`, `Why`, `Impact`, `Fix` を含める
- 推測しかない場合は `Open Questions` に分離する
- finding がない場合でも、残余リスクや testing gap を書く

## Boundaries

- 好みの命名や書式だけで finding を作らない
- repo ローカル最適で一般的な欠陥を見逃さない
- security が主題なら `security-review` の利用も検討する
- AI 支援変更特有の品質崩れを重点確認したい場合は `ai-coding-antipattern-review` の利用も検討する

## Resources

- 一般的なレビュー観点: `references/general-review-checklist.md`
- repo 固有のレビュー観点: `references/testsniff-review-checklist.md`
