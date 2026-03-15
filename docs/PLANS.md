# PLANS

## Purpose

このリポジトリにおける計画成果物の作成、更新、完了の扱いを定義します。

## Planning Model

- 軽微な作業は、タスクスレッド内の簡潔な計画でよいです。
- 複数ステップにまたがる作業や横断的な作業は、`docs/exec-plans/active/` に実行計画を作成します。
- 完了した実行計画は `docs/exec-plans/completed/` に移動します。
- 直ちに着手しない課題は [docs/exec-plans/tech-debt-tracker.md](/home/aoi_takanashi/testsniff/docs/exec-plans/tech-debt-tracker.md) に記録します。

計画運用は [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md) で定義されたブランチ戦略と整合している必要があります。

## Plan Language Rule

- 実行計画の本文は日本語で記述します。
- 見出し、説明文、判断理由、リスク、検証方針は日本語を正とします。
- ルール ID、コマンド、ファイルパス、コード識別子などは必要に応じて英語のままで構いません。

## Execution Plan Minimum Contents

- 問題設定
- スコープと非ゴール
- マイルストーンまたは作業流れ
- 意思決定ログ
- 検証計画
- 完了条件

## Current State

実行計画は `docs/exec-plans/active/` と `docs/exec-plans/completed/` で管理します。

当面の重要な計画対象:
- 対応する rule catalog の具体化
- 個別ルールの段階的実装
- 出力契約と rule metadata の整備
