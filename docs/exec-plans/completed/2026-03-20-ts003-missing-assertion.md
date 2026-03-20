# TS003 Missing Assertion Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-20
- Completed: 2026-03-20
- Source Issue: [#5](https://github.com/kai-5908/testsniff/issues/5)
- Worktree: `/tmp/testsniff-issue-5`
- Approval: Approved

## 問題設定

Issue #5 は、assertion を持たない test を `TS003` として検出する rule の追加を求めている。

一方で、現行の採用済み product spec [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) では `missing assertion` が v1.0.0 から明示的に除外されており、理由として static-only では `pytest.raises`、間接検証、helper 経由の検証などで false positive が増えやすいと整理されている。

そのため、この task は単なる rule 実装ではなく、次の 2 点を同時に解く必要がある。

- `TS003` を v1.0.0 スコープへ入れるか、どの範囲までなら explainable な static rule として成立するかを確定する
- 既存の rule 基盤に沿って、検出対象 test と assertion 判定の境界を high confidence で説明できる形に落とし込む

## 目的

- `TS003` の仕様境界を明文化し、Issue #5 と採用済み product spec の衝突を解消する
- 共通 `test_targets` 基盤を使って assertion 不在の test を静的に検出できるようにする
- `WHY` / `FIX` / `EXAMPLE` を含む finding を CLI から確認できる状態にする

## 受け入れ条件の写像

Issue #5 の受け入れ条件は、実装と検証へ次の形で落とし込む。

- assertion を持たない standardized test target で `TS003` finding が返る
- bare `assert` または採用した assertion-like 構文を持つ test target では `TS003` が返らない
- human / compact / json の各出力で `TS003` の metadata が欠落しない
- rule の非ゴールに置いたパターンは、docs に明示して過剰な期待を防ぐ

## スコープ

今回含めるもの:

- `TS003` の静的判定境界の定義
- assertion 判定 helper または rule 内部ロジックの実装
- `src/testsniff/docs/rule_metadata.py` への metadata 追加
- registry wiring と CLI 経路での検出確認
- fixture / unit / integration test の追加
- product spec と関連 docs の同期

今回含めないもの:

- framework 固有 matcher の網羅
- helper 関数の内部まで追う interprocedural 解析
- runtime 情報が必要な assertion 判定
- auto-fix
- confidence を動的に下げて広く拾う曖昧な heuristic

## 現状認識

- `src/testsniff/parser/ast_index.py` には `ModuleContext.index.test_targets` があり、Issue #3 の依存関係である test target 判定基盤は main 上で利用可能
- 既存の `TS001` 実装は `test_targets` を再利用しており、新 rule を追加する基本経路は揃っている
- `src/testsniff/docs/rule_metadata.py` は `TS001` のみを持っているため、`TS003` の user-facing explanation は未整備
- 採用済み product spec では `missing assertion` が v1.0.0 除外項目になっているため、doc 更新なしに実装だけ進めると repository source of truth が衝突したまま残る

## 仮定

- Issue #3 由来の test target 判定を `TS003` でもそのまま利用する
- version 1 の `TS003` は、有限個の assertion-like 構文だけを明示的に許可する
- helper 関数へ委譲した検証や副作用ベースの間接検証は、初回実装では非ゴールまたは follow-up に寄せる
- v1.0.0 に含めるなら `confidence=high` を維持できる範囲まで判定対象を絞る

## 未解決事項

- `missing assertion` を v1.0.0 の採用済み catalog へ正式に追加するか
  - 追加する場合、[docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) の除外記述を同じ change で更新する必要がある
- 初期の assertion-like 構文に何を含めるか
  - 最小候補は `assert`
  - false positive を下げる候補は `self.assert*`、`pytest.raises(...)`、`pytest.warns(...)`
- `pytest.fail()` のような明示失敗 API を assertion ありとみなすか
- helper 呼び出しだけの test を初回から許容するか、それとも `TS003` 対象のままにするか

## 作業流れ

### 1. 仕様整合性の確定

- Issue #5 と採用済み catalog の衝突を解消する方針を決める
- `TS003` を v1.0.0 に含めるなら product spec を更新し、含めないなら Issue 側の期待値を調整する
- 初回実装で high confidence を維持できる assertion 境界を文章で固定する

### 2. Assertion Semantics の固定

- AST 上で静的に説明できる assertion-like 構文を列挙する
- negative にすべき valid pattern と、non-goal に逃がす pattern を分ける
- reported location を function 定義行に置くか、最も妥当な assertion 欠如箇所として維持するかを確認する

### 3. Rule 実装

- `TS003` metadata を追加する
- rule module を追加し、`test_targets` ごとに assertion 不在を判定する
- registry と scan 経路へ接続し、既存 formatter で描画可能にする

### 4. テスト

- positive fixture: assertion を持たない top-level / pytest class / unittest method
- negative fixture: `assert`、`self.assert*`、採用した assertion-like 構文を持つ test
- unit test: assertion 判定 helper と rule finding の境界
- integration test: CLI `scan` で `TS003` が表示されること

### 5. ドキュメント同期

- rule catalog と rule metadata の整合を取る
- 非ゴールと false positive リスクを docs に残す
- follow-up が必要な assertion pattern は debt または別 issue に切り出す

## 変更候補ファイル

- `src/testsniff/rules/checks/`
- `src/testsniff/rules/registry.py`
- `src/testsniff/docs/rule_metadata.py`
- `tests/fixtures/`
- `tests/unit/`
- `tests/integration/test_cli.py`
- `docs/product-specs/rule-catalog-scope.md`
- 必要に応じて `docs/design-docs/reporting-contract.md`

## 検証計画

最低限の検証:

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`

挙動検証:

- `uv run testsniff scan <fixture-dir>` で assertion 不在 fixture から `TS003` が返る
- `assert` / `self.assert*` / 採用した assertion-like 構文を含む fixture では `TS003` が返らない
- `--format json` で `rule_id=TS003` と `WHY` / `FIX` / `EXAMPLE` 相当の構造が保持される

## 完了条件

以下を満たしたら完了とする。

- `TS003` の判定境界が docs と tests で一致している
- Issue #5 と product spec の衝突が解消されている
- `TS003` が default scan 経路で実行される
- positive / negative / integration coverage が揃っている
- 品質ゲートと CLI 確認が通る

## 意思決定ログ

- 2026-03-20: Issue #5 を起点に plan を作成開始
- 2026-03-20: 依存関係として挙げられた test target 判定基盤は、Issue #3 の完了内容と現行 `ASTIndex.test_targets` 実装により満たされていると整理
- 2026-03-20: 採用済み catalog が `missing assertion` を v1.0.0 除外としているため、実装前に仕様整合性の確認を必須事項として plan に昇格

## リスク

- assertion-like 構文を狭く取りすぎると false positive が増える
- 逆に許可リストを広げすぎると static explainability が落ちる
- helper 経由の検証を扱わない場合、ユーザー期待と差が出る
- product spec 更新を伴うため、rule 実装だけの小タスクとしては収まりにくい

## 承認後の着手方針

承認後は、まず `TS003` の採用可否と assertion 境界を確定し、その後に metadata、rule 実装、fixtures、CLI 回帰テストの順で進める。
