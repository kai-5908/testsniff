# Testsniff Review Checklist

## Goal

`testsniff` repo 固有の設計境界、品質ルール、静的解析プロダクト制約、PR 運用を追加確認する。

## Read Only What You Need

- まず変更差分と関連コードを読む
- 設計境界が関係する場合は `ARCHITECTURE.md` と `docs/design-docs/internal-quality-rules.md`
- PR 完了度が関係する場合は `docs/design-docs/pull-request-rules.md`
- セキュリティ境界が関係する場合は `docs/SECURITY.md`
- docs 同期判断が必要な場合は `AGENTS.md` の `When To Update Docs` を確認する

## Repo-Specific Checks

### 1. Static-Only Boundary

- スキャン中に対象 repository のコードを実行しないか
- 外部ネットワークや不要な filesystem write を default path に持ち込んでいないか
- 入力を trusted code ではなく untrusted text として扱っているか

### 2. Layer Boundaries

- `cli` は user interaction に留まり、orchestration を `services` に委ねているか
- `rules` が file I/O、CLI 依存、global state mutation をしていないか
- `parser` に rule-specific logic を混ぜていないか
- `reporting` が smell 判定や finding 修復をしていないか
- `config` が scan 前に設定正規化を終えているか

### 3. Canonical Contracts

- `ScanConfig`, `ModuleContext`, `Finding`, `ScanResult` の変更に tests と docs が追随しているか
- renderer に不完全な finding を渡していないか
- 共有すべき解析ロジックが ad hoc に rule 側へ重複していないか

### 4. Rule Implementation Completeness

- 新規 rule に metadata があるか
- positive fixture と negative fixture があるか
- 出力形式に影響するなら reporting coverage や snapshot が更新されているか
- bug fix なら regression test が追加されているか

### 5. Documentation Sync

- user-facing detection behavior、rule ID、message format、fix guidance の変更に docs 更新があるか
- package boundary や data flow の変更に architecture/design docs 更新があるか
- planning status、reliability、security assumptions の変更が文書に反映されているか

### 6. PR And Validation Expectations

- 変更が 1 task の境界を壊していないか
- 関連 Issue や受け入れ条件の確認が可能か
- 検証結果が残っているか
- 典型的には `uv run ruff check src tests`, `uv run ty check src`, `uv run pytest -q` のどれを実施したか明確か

## Repo-Specific Findings

- 一般原則でも問題を説明できる場合は、その説明を優先する
- repo 固有ルール違反だけが根拠なら、その前提を明示する
- docs や tests の不足は、影響する契約と合わせて指摘する
