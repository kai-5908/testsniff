# TS004 Disabled / Ignored Test Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-20
- Completed: 2026-03-22
- Source Issue: [#6](https://github.com/kai-5908/testsniff/issues/6)
- Worktree: `/home/aoi_takanashi/testsniff/worktrees/issue-6-plan`
- Approval: Approved

## 問題設定

Issue #6 は、skip / skipif / disabled 相当で通常実行から外される test を `TS004` として検出する rule の追加を求めている。

現行の採用済み product spec [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) には `Disabled / Ignored Test` が v1.0.0 スコープとして既に入っているが、rule ID は「follow-up implementation issue で割り当てる」となっており、repository 上の rule 実装・metadata・tests はまだ存在しない。

この task では、単に rule を足すだけでなく、次の 2 点を同時に満たす必要がある。

- `TS004` の静的判定境界を high confidence のまま説明できる形で固定する
- 既存の test target 判定基盤と reporting 経路に沿って、docs / metadata / tests を含めて source of truth を同期させる

## 目的

- `TS004` の対象を explicit かつ static-only な skip / ignore シグナルに限定して定義する
- `pytest` と `unittest` の採用対象 decorator を rule と tests に落とし込む
- human / compact / json の各出力で `TS004` metadata を確認できる状態にする

## 受け入れ条件の写像

Issue #6 の受け入れ条件は、実装と検証へ次の形で落とし込む。

- 採用した `pytest.mark.skip` / `pytest.mark.skipif` / `unittest.skip` 系 decorator を持つ standardized test target で `TS004` finding が返る
- 無関係な decorator や、採用対象外として明示した構文では `TS004` が返らない
- default scan および `--select TS004` の両方で `TS004` が実行される
- human / compact / json の各出力で `TS004` の metadata が欠落しない

## スコープ

今回含めるもの:

- standardized test target に対する explicit decorator ベースの disabled / ignored 検出
- `TS004` metadata の追加
- rule module 追加と registry wiring
- positive / negative fixture、unit test、integration test の追加
- rule catalog を含む docs 更新

今回含めないもの:

- test 本文内の `pytest.skip()` や runtime 条件分岐による skip 判定
- skip reason や skip 条件式の妥当性評価
- CI / OS / env 依存で skip が正当かどうかの判断
- project 固有 decorator や re-export された wrapper の推測的判定
- auto-fix

## 現状認識

- `src/testsniff/parser/ast_index.py` の `ModuleContext.index.test_targets` により、Issue の依存関係である test target 判定基盤は main 上で利用可能
- `src/testsniff/rules/registry.py` は `TS001` から `TS003` までのみを登録しており、`TS004` の default scan 経路は未接続
- `src/testsniff/docs/rule_metadata.py` に `TS004` metadata は存在しない
- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) は `Disabled / Ignored Test` を採用済みだが、rule ID と具体的な静的シグナルはこの task で確定する余地がある

## 仮定

- `TS004` は既存の standardized test target だけを対象にし、helper 関数や非 test 関数は対象外とする
- 初回実装の `pytest` 対応は、`pytest` モジュール alias 経由の `pytest.mark.skip` / `pytest.mark.skipif` に限定し、`from pytest import mark` 系の direct import alias は対象外とする
- 初回実装の `unittest` 対応は、`unittest.skip` / `skipIf` / `skipUnless` など skip 系 decorator の明示 import / module alias で説明できる範囲へ限定する
- finding は affected test target 単位で返し、severity / confidence は issue と product spec に合わせて `warning` / `high` を維持する
- class-level decorator を検出した場合も、影響を受ける各 test method に finding を展開して返す
- reported location は decorator 行ではなく、test 関数 / method 定義行に置く
- `expectedFailure` のような「disabled ではないが通常成功基準を変える decorator」は初回実装の非ゴールとして明示する
- class-level decorator 起因で method ごとに展開した finding でも、headline / WHY / FIX は追加情報なしの共通文面を使う

## 確定した判定方針

- `pytest` は `import pytest` または `import pytest as <alias>` による `pytest.mark.skip` / `pytest.mark.skipif` だけを対象にする
- `from pytest import mark` や `from pytest import mark as pt_mark` のような direct import の `mark` 系は、初回実装では許可しない
- `unittest` は `skip` / `skipIf` / `skipUnless` を初回スコープに含め、同系統で静的に説明しにくい decorator は今回は含めない
- class-level decorator は class 単位で 1 件に集約せず、配下の standardized test method ごとに finding を返す
- finding の reported location は decorator 行ではなく、対象 test の定義行に固定する
- `expectedFailure` は disabled / ignored test とみなさず、初回実装では明示的に非ゴールへ置く
- class-level decorator 起因の finding でも、method-level decorator の finding と同じ headline / WHY / FIX を使う
- `unittest.skip` 系の採用一覧は docs と tests の両方で詳細に列挙し、少なくとも `skip` / `skipIf` / `skipUnless` の個別名と対象内であることを明記する

## 作業流れ

### 1. 判定境界の固定

- `pytest.mark.skip` / `pytest.mark.skipif` と `unittest.skip` 系の採用一覧を文章で固定する
- `unittest.skip` / `skipIf` / `skipUnless` を docs と tests に個別名で明記し、初回スコープ外の decorator との差を分かるようにする
- direct import の `pytest.mark` 系を非ゴールとして明記する
- test target 単位での報告粒度と reported location を docs に反映する
- `TS004` を stable rule ID として docs に反映する

### 2. Rule 実装

- `src/testsniff/docs/rule_metadata.py` に `TS004` metadata を追加する
- decorator 解析 helper と `TS004` rule module を追加する
- `src/testsniff/rules/registry.py` に接続し、default scan で有効化する

### 3. テスト追加

- positive fixture: `pytest.mark.skip`、`pytest.mark.skipif`、`unittest.skip` / `skipIf` / `skipUnless`、class-level decorator の代表例
- negative fixture: 無関係な decorator、`from pytest import mark` 系、対象外とした runtime skip パターン、`expectedFailure`
- unit test: decorator 解決境界、reported location、class-level 展開時も message が共通文面であること
- integration test: CLI `scan` と `--format json` で `TS004` が描画されること

### 4. ドキュメント同期

- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/docs/product-specs/rule-catalog-scope.md) で `TS004` の stable ID と static signal を同期する
- `unittest.skip` 系の採用 decorator 名を docs 上で詳細に列挙し、`skip` / `skipIf` / `skipUnless` を個別に読める形にする
- rule metadata と docs の説明差分を解消する
- 採用しない direct import alias と `expectedFailure` を非ゴールとして明記する

## 変更候補ファイル

- `src/testsniff/rules/checks/`
- `src/testsniff/rules/registry.py`
- `src/testsniff/docs/rule_metadata.py`
- `tests/fixtures/`
- `tests/unit/`
- `tests/integration/test_cli.py`
- `docs/product-specs/rule-catalog-scope.md`
- 必要に応じて `docs/exec-plans/tech-debt-tracker.md`

## 検証計画

最低限の検証:

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`

挙動検証:

- `uv run testsniff scan <fixture-dir> --select TS004` で skip decorator 付き fixture から `TS004` が返る
- 無関係な decorator、`from pytest import mark` 系、`expectedFailure`、対象外パターンでは `TS004` が返らない
- `uv run testsniff scan <fixture-dir> --select TS004 --format json` で `rule_id=TS004` と metadata が保持される

## 完了条件

以下を満たしたら完了とする。

- `TS004` の判定境界が docs、tests、実装で一致している
- `TS004` が default scan 経路で実行される
- positive / negative / integration coverage が揃っている
- quality gate と representative CLI 確認が通る
- Issue #6 の受け入れ条件がレビュー可能な形で満たされている

## 意思決定ログ

- 2026-03-20: Issue #6 を取得し、`TS004 Disabled / Ignored Test` の実行計画作成を開始
- 2026-03-20: 依存関係として挙げられた test target 判定基盤は、現行 `ModuleContext.index.test_targets` と関連 unit test により main 上で満たされていると整理
- 2026-03-20: product spec には smell 自体が採用済みのため、この task では rule ID `TS004` の確定と静的シグナルの具体化を同じ change で扱う方針を採る
- 2026-03-22: `pytest` の direct import `mark` 系は初回実装で非ゴールとし、`unittest.skipIf` / `skipUnless` は初回スコープへ含める方針に更新
- 2026-03-22: class-level decorator は各 test method へ展開し、finding location は test 定義行に置く方針に更新
- 2026-03-22: class-level decorator 起因の finding でも、headline / WHY / FIX は追加情報なしの共通文面を使う方針に更新
- 2026-03-22: `unittest.skip` 系の採用一覧は docs と tests の両方で詳細に列挙する方針に更新
- 2026-03-22: `TS004` を rule / metadata / fixtures / integration tests / rule catalog へ実装し、`uv run ruff check src tests`、`uv run ty check src`、`uv run pytest -q` を通過

## リスク

- alias 解決を広げすぎると false positive / false negative の説明責任が崩れる
- class-level decorator の扱いを曖昧にすると reported finding 数と location が不安定になる
- runtime skip を期待するユーザーが出ると、static-only 境界の説明が必要になる
- `pytest` と `unittest` の差分整理が甘いと fixture は通っても docs と実装が乖離する

## 実施結果

- `TS004` rule を追加し、default scan と `--select TS004` の両方で実行できるようにした
- `pytest.mark.skip` / `pytest.mark.skipif` と `unittest.skip` / `skipIf` / `skipUnless` の採用境界を docs と tests に反映した
- class-level decorator は各 test method へ展開しつつ、共通 headline / WHY / FIX を使う挙動を unit / integration test で固定した
