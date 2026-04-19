# TS006 Magic Number Test Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-04-19
- Completed: 2026-04-19
- Source Issue: [#8](https://github.com/kai-5908/testsniff/issues/8)
- Worktree: `/home/aoi_takanashi/testsniff/worktrees/feat-issue-8-plan`
- Approval: Approved

## 問題設定

Issue #8 は、説明のない数値リテラルを期待値や重要な引数に埋め込む test を `TS006` として検出する rule の追加を求めている。

一方で、現行の採用済み product spec [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) では `Magic Number Test` が v1.0.0 の対象外として明示されている。そのため、この task は rule 実装だけでは成立せず、v1 catalog の境界更新と high-confidence を維持できる静的判定範囲の再定義を同じ change で固定する必要がある。

## 目的

- `TS006` を static かつ explainable な v1 rule として成立する最小スコープを定義する
- `warning` severity を採る理由と、`high` confidence を維持できる境界を docs と実装で一致させる
- false positive が出やすい数値リテラル利用を非ゴールまたは除外対象として明文化する
- metadata、fixture、tests、CLI 出力、関連 docs を一貫して更新できる実装計画を確定する

## 受け入れ条件の写像

Issue #8 の受け入れ条件は、実装と検証で次のように具体化する。

- 対象と定義した magic number pattern で `TS006` finding が返る
- 除外対象として定義した数値リテラル利用では `TS006` が返らない
- `TS006` finding の `severity` と `confidence` が仕様どおりに出力される
- `TS006` finding には stable な位置情報と `WHY` / `FIX` / `EXAMPLE` を支える metadata が含まれる
- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) と実装の scope が一致している

## スコープ

今回含めるもの:

- `TS006` を v1 catalog に追加するための scope 更新
- `TS006` の対象 pattern、除外 pattern、reported location の定義
- `TS006` rule 実装と registry 接続
- `src/testsniff/docs/rule_metadata.py` への `TS006` metadata 追加
- representative fixture、unit test、integration test 追加
- rule catalog と必要な関連 docs の同期

今回含めないもの:

- test 内のあらゆる数値リテラルを広く拾う包括検出
- runtime 情報や型推論を要する「重要な引数」判定
- project 固有の定数命名規約や domain knowledge を前提にした判断
- auto-fix
- `high` confidence を崩してまで拾う曖昧な heuristic

## 現状認識

- 現行実装では `TS001` から `TS005` までが registry と metadata に接続済みである
- 既存 rule 群は standardized test target を `module.index.test_targets` から取得している
- Issue #8 の依存関係である「test 関数判定ルールが固まっていること」は、現行 main の基盤で満たされている
- 現行 catalog では `Magic Number Test` が明示的に除外されているため、scope 更新なしの実装先行は source of truth の分裂を招く

## 依存関係の整理

- test target 判定は既存基盤を再利用できる
- `TS006` の対象文脈を assertion 系に寄せる場合、既存の assertion 認識ロジックや AST 走査の共有可能性を確認する必要がある
- `warning` severity と `high` confidence を両立させるには、一般的な test data literal と区別できる明示的文脈だけに絞る必要がある

## 仮定

- `TS006` も既存 rule と同じ standardized test target を対象にする
- 初回実装では、説明責任を保ちやすい assertion / expectation 近傍の数値リテラルに限定する
- reported location は既存 rule と同様に test 定義行、または十分に安定している場合のみ literal 行を採用する
- severity は issue 記載どおり `warning` を第一候補とする
- confidence は、対象 pattern と除外 pattern を十分に狭く定義できる場合のみ `high` を維持する

## 未解決事項

- 現時点の plan では追加の未解決事項はない
- 実装中に `warning` / `high` を維持できない pattern が出た場合は、その pattern を初回スコープから外して plan と docs に追記する

## 確定方針

- 初回スコープは assertion / expectation 文脈に現れる裸の数値リテラルに限定する
- v1 では「重要な引数」一般は対象に含めない
- 対象の代表例は `assert x == 200`、`assert count >= 3`、`self.assertEqual(x, 10)` のような expectation を直接表す文脈とする
- 一般の test data 構築、loop 回数、入力データ、単なる list / dict literal、一般の function call 引数は初回スコープ外に置く
- 初回の除外数値は `0`、`1`、`-1` に限定する
- `200` や `404` などの HTTP status code 相当の数値は一律除外しない
- reported location は test 定義行ではなく、対象の数値リテラル行・列を採用する
- `TS006` は `warning` / `high` を基本案とし、high confidence を支えられない pattern は次回以降へ送る

## 作業流れ

### 1. 仕様境界の確定

- Issue #8 の DoR / DoD を基に、対象 pattern と除外 pattern を fixtures へ落とせる粒度で固定する
- 現行 catalog の除外理由を見直し、v1 に入れるなら何を狭める必要があるかを文章化する
- `warning` severity の理由と `high` confidence の成立条件を plan と docs に落とし込む

### 2. 検出方針の設計

- どの AST 文脈を magic number と見なすかを assertion / expectation 文脈に限定して定義する
- `0`、`1`、`-1` を除外し、それ以外の expectation 文脈リテラルをどう扱うかを整理する
- reported location は literal 行・列を基準に設計する
- 必要なら既存 helper の共有化ポイントを整理する

### 3. Rule 実装

- `TS006` rule module を追加する
- 必要に応じて assertion / call 文脈判定 helper を抽出または拡張する
- registry と scan 経路へ接続し、既存 formatter で描画できる状態にする

### 4. テスト

- positive fixture: 対象と定義した期待値埋め込みで `TS006` が返る例
- negative fixture: `0`、`1`、`-1` の除外数値では `TS006` が返らない例
- negative fixture: 一般の test data literal や非 assertion 文脈では `TS006` が返らない例
- negative fixture: `timeout=30` のような一般 call 引数では `TS006` が返らない例
- unit test: assertion 文脈判定、除外規則、literal location の reported location
- integration test: CLI `scan` と `--format json` の回帰確認

### 5. ドキュメント同期

- rule catalog から `Magic Number Test` の除外を外し、`TS006` として追加する
- `rule_metadata` の rationale、fix guidance、examples を整備する
- 初回で見送る pattern は non-goal または tech debt として明記する

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

- `uv run testsniff scan <fixture-dir> --select TS006` で対象 fixture から `TS006` が返る
- 除外対象 fixture や非対象文脈では `TS006` が返らない
- `--format json` で `rule_id=TS006`、`severity=warning`、`confidence`、explanation fields が保持される

## 完了条件

以下を満たしたら完了とする。

- `TS006` の対象 pattern と除外 pattern が docs、fixtures、tests で一致している
- Issue #8 の DoR にある warning 方針、除外対象、false positive 代表例、検証方法が解消されている
- `TS006` が合意した静的文脈でのみ finding を返す
- `TS006` が既存 formatter で一貫して出力される
- product spec と実装の整合が取れている

## 意思決定ログ

- 2026-04-19: Issue #8 を起点に plan を作成開始
- 2026-04-19: 現行 catalog が `Magic Number Test` を v1 対象外としているため、rule 実装と同時に scope 更新が必要と整理
- 2026-04-19: 初回スコープは `warning` / `high` を維持できる静的文脈へ絞る方針を採用
- 2026-04-19: 初回スコープは assertion / expectation 文脈の裸の数値リテラルに限定し、「重要な引数」一般は対象外と確定
- 2026-04-19: 除外数値は `0`、`1`、`-1` に限定し、HTTP status code 相当の数値は一律除外しない方針に確定
- 2026-04-19: reported location は test 定義行ではなく、対象 literal の行・列を採用する方針に確定
- 2026-04-19: 実装では bare `assert` 比較、`unittest` の比較 assertion、`assertTrue` / `assertFalse` 条件を `TS006` の初回対象として追加した
- 2026-04-19: broad literal scanning は採らず、比較 operand または直接期待値として渡された裸の数値リテラルだけを finding 対象に絞った

## リスク

- 数値リテラル検出を広げすぎると test data まで大量に拾って false positive が増える
- 逆にスコープを狭めすぎると、ユーザーが期待する magic number を十分に検出できない
- catalog 更新が必要なため、rule 実装だけの局所変更では完結しない
- literal location を採るため、test 定義行ベースの既存 rule と出力位置の性質が揃わない

## 実施結果

- `TS006` rule を追加し、default scan 経路から利用できるよう registry へ接続した
- bare `assert` 比較 operand、`unittest` 比較 assertion、`assertTrue` / `assertFalse` 条件内の数値リテラルを検出できるようにした
- `0`、`1`、`-1` と一般の call 引数、membership assertion、一般 test data literal を初回スコープ外として固定した
- finding location は対象数値リテラルの行・列を返すようにした
- rule metadata、fixture、unit test、integration test、product spec を同期した
- 検証として `uv run ruff check src tests`、`uv run ty check src`、`uv run pytest -q` を通した
