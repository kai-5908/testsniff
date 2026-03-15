# Test Target Classification Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-15
- Completed: 2026-03-15
- Source Issue: [#3](https://github.com/kai-5908/testsniff/issues/3)

## 問題設定

現在の `TS001` 実装は `src/testsniff/rules/checks/empty_test.py` で `module.index.functions` を全走査し、`name.startswith("test_")` だけで検出対象を決めています。

この実装だと、rule ごとに独自の test 判定が増えやすく、Issue #3 が指摘している「判定ルールのぶれ」を防げません。特に、次の不足があります。

- `unittest.TestCase` の test method を共通基盤として扱えていない
- helper 関数や将来の nested function を除外する基準が rule 実装に埋もれる
- 以後の rule が `TS001` と別の test 判定を持つ余地が残る

version 1 の rule 基盤を安定させるため、rule から再利用できる test target 判定ロジックを標準化し、`pytest` / `unittest` の静的に説明可能な範囲を先に固定する。

## 目的

- `pytest` スタイルの test function を共通の検出対象として扱えるようにする
- `unittest.TestCase` 配下の test method を共通の検出対象として扱えるようにする
- helper 関数や非 test 関数を検出対象から除外する基準を 1 箇所に集約する
- `TS001` をその共通判定ロジックへ移行し、以後の rule 実装の前提を揃える

## スコープ

今回含めるもの:

- 現在の parser / index / rule 基盤のうち、test target 判定に必要なデータ構造の整理
- `pytest` 形式の top-level test function 判定
- `unittest.TestCase` 形式の test method 判定
- helper 関数除外ルールの明文化と unit test
- `TS001` の共通判定ロジックへの置き換え
- 関連ドキュメント更新

今回含めないもの:

- smell rule の追加実装
- 動的解析や実行時 import 解決
- `pytest` class-based tests など Issue #3 に明示されていない discovery 互換性の拡張
- 全 rule catalog の確定

## 受け入れ条件の写像

Issue #3 の受け入れ条件を、実装と検証に次の形で落とし込む。

- `pytest` スタイルの test 関数を検出対象にできる
  - top-level の `test_*` 関数と `async def test_*` を共通 target として列挙できる
- `unittest.TestCase` の test メソッドを検出対象にできる
  - `TestCase` 継承 class 配下の `test_*` method を共通 target として列挙できる
- helper 関数や非 test 関数には rule が適用されない
  - top-level helper、class helper、nested function を誤って対象化しない unit test を持つ
  - `TS001` が共通 target のみを評価することを回帰テストで確認する

## 現状認識

- `src/testsniff/parser/ast_index.py` は `ast.walk()` で全 `FunctionDef` / `AsyncFunctionDef` を平坦に集めている
- 親子関係や「top-level function か」「class method か」を index が保持していない
- `src/testsniff/rules/checks/empty_test.py` は `test_` prefix を直接参照しており、共通判定ロジックが存在しない
- 既存の `tests/unit/test_empty_test_rule.py` は `pytest` 風 top-level function だけを前提にしている

## 仮定

- version 1 は静的 rule-based のみを対象とするため、`unittest.TestCase` 判定は AST 上で説明可能な継承表現に限定する
- `pytest` 対象は top-level の `test_*` function / async function を基本とし、helper 判定は「名前ではなく構造」で除外する
- nested function は `test_` という名前でも rule 対象外とする
- `TS001` は source location の報告方式を大きく変えず、対象列挙だけを共通化する

## 未解決事項

- `unittest.TestCase` 判定でどこまで alias import を追うか
  - 最小案は `TestCase` / `unittest.TestCase` の静的に明白なケースのみ対応
- `pytest` class-based tests を version 1 の共通 target に含めるか
  - Issue #3 の明示スコープ外なので、必要なら follow-up issue に切り出す
- 共通判定ロジックの配置先
  - `parser` index に test target 一覧を持たせるか、`rules` 基盤 helper に寄せるかを実装前に確定する

## 作業流れ

### 1. 対象定義の固定

- Issue #3 の対象 test style を current implementation に即して整理する
- helper / nested / non-test の除外ルールを文章とテストケースで固定する
- `unittest.TestCase` の静的判定境界を明文化する

### 2. 共通判定基盤の設計

- 親 class や top-level 所属を判別できる index 情報を追加する
- rule が再利用しやすい test target 表現を決める
- ルール本体が命名規約や継承判定を直接持たない構造に整える

### 3. 実装

- parser / index 側に共通 test target 判定ロジックを追加する
- `TS001` を共通 target のみ解析する実装へ切り替える
- 将来ルールからも同じ判定を呼べる形に整える

### 4. テスト

- `pytest` top-level function の positive / negative を追加する
- `unittest.TestCase` method の positive / negative を追加する
- helper、nested function、non-TestCase class method の negative を追加する
- `TS001` の既存回帰テストを共通 target 判定に合わせて補強する

### 5. ドキュメント同期

- 判定境界を architecture / design doc のうち必要最小限に反映する
- 今回扱わない discovery pattern は非ゴールまたは follow-up として残す

## 変更候補ファイル

実装時に主に触る可能性が高い場所:

- `src/testsniff/parser/ast_index.py`
- `src/testsniff/parser/module_context.py`
- `src/testsniff/rules/checks/empty_test.py`
- `tests/unit/test_empty_test_rule.py`
- 追加の parser / rule fixture
- 必要に応じて `ARCHITECTURE.md` または `docs/design-docs/application-architecture.md`

## 検証計画

最低限の検証:

- `uv run pytest -q`

可能なら合わせて確認:

- `uv run ruff check src tests`
- 追加した共通 test 判定ロジックの unit test

挙動検証:

- top-level `test_*` function が検出対象に入る
- `unittest.TestCase` 配下の `test_*` method が検出対象に入る
- helper function / helper method が対象外になる
- nested function が対象外になる
- `TS001` が共通 target に対してのみ finding を出す

## 完了条件

以下を満たしたら完了とする。

- 共通の test 判定ロジックが 1 箇所に実装されている
- `pytest` function と `unittest.TestCase` method の双方を unit test で検証している
- helper / non-test / nested function の negative coverage がある
- `TS001` が新しい共通判定ロジックを利用している
- 必要な関連ドキュメントが更新されている

## 意思決定ログ

- 2026-03-15: Issue #3 を起点に、rule 個別実装の前に test target 判定基盤を標準化する方針を採用
- 2026-03-15: 現状の `name.startswith("test_")` を rule 固有ロジックとして増やさず、共通基盤へ寄せる前提で plan を作成
- 2026-03-15: 共通判定ロジックは `parser.ast_index` に配置し、`ModuleContext.index.test_targets` から rule が再利用する構成に確定
- 2026-03-15: `unittest.TestCase` 判定は `import unittest` / `from unittest import TestCase` の静的に明白な import と、同一 module 内の派生 class までを対象にした
- 2026-03-15: `pytest` class-based tests は v1 スコープ外のままとし、top-level `test_*` function / async function のみに限定

## リスク

- `unittest.TestCase` の静的判定範囲を広げすぎると explainability が落ちる
- index 変更の仕方によっては、今後の rule 実装前提まで過度に固定してしまう
- `pytest` の discovery 全互換を目指すと Issue #3 のスコープを超えやすい

## 承認後の着手方針

承認後は、まず test target の定義と fixture を固め、その後に parser/index と `TS001` を順に更新する。
