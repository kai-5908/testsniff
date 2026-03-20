# TS002 Comments-only Test Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-20
- Source Issue: [#4](https://github.com/kai-5908/testsniff/issues/4)
- Completed: 2026-03-20

## 問題設定

Issue #4 は、実行文を持たずコメントまたは docstring のみを持つ test を `TS002` として検出することを求めている。

ただし、現状の repository には次の衝突がある。

- `docs/product-specs/rule-catalog-scope.md` では `comments-only test` を `TS001` と別の Python rule として扱わず、v1.0.0 の対象外と明記している
- `src/testsniff/rules/checks/empty_test.py` の `TS001` は docstring-only test を既に empty として検出している
- Python 構文上、comment だけで関数本体を構成するコードは成立しないため、`comment-only` をそのまま AST rule として切り出せない

このため、Issue #4 をそのまま実装対象へ落とし込む前に、`TS001` との差分、`TS002` の正確な検出単位、関連 spec の更新方針を固定する必要がある。

## 現状認識

- `ModuleContext` は AST と token を両方保持しているため、必要なら token 情報を使った補助判定は可能
- `TS001` は `module.index.test_targets` を走査し、先頭 docstring を除去したあと本文が空、または `pass` のみなら finding を返す
- docstring-only test は現状でも `TS001` の positive fixture と unit test が存在する
- `human` / `json` 出力は `src/testsniff/docs/rule_metadata.py` の canonical metadata を参照している

## 目的

- Issue #4 を実装可能な形へ分解し、`TS001` との境界を明確にする
- `TS002` を追加する場合に必要な code / tests / docs の変更範囲を事前に固定する
- 受け入れ条件を、現行実装と矛盾しない検証項目へ写像する

## スコープ

今回の計画で実装対象として見込むもの:

- `TS002` の semantics を明文化するための spec / plan 更新
- `TS002` metadata の追加
- `TS002` rule 実装
- positive / negative fixture、unit test、integration test の追加
- 必要最小限の reporting / catalog ドキュメント更新

今回の計画で含めないもの:

- auto-fix
- `TS001` の headline や severity / confidence の変更
- test target 判定基盤の再設計
- v1.0.0 rule catalog 全体の再議論

## 主要な仮定

- `TS001` の既存挙動は維持し、docstring-only test は引き続き `TS001` の責務として扱う
- `TS002` は `TS001` と重複しないよう、comment を含む placeholder intent を source token から補助的に検出する方向を優先する
- Python 文法上の制約により、純粋な `comment-only function` ではなく、`docstring + comment` のような「非実行テキストしかない test」を主な検出候補として扱う

## 未解決事項

- Issue #4 の「コメントまたは docstring のみ」を厳密に実装する場合、docstring-only を `TS001` と `TS002` のどちらに帰属させるか
- `comments-only test` を v1.0.0 の対象へ昇格させるため、`docs/product-specs/rule-catalog-scope.md` をどう改訂するか
- `TS002` の最小成立条件を「comment を少なくとも 1 つ含む placeholder test」とするか、それとも Issue 文言を先に修正するか

## 推奨方針

承認後の実装では、まず Issue #4 を次の実装可能な解釈へ正規化して進める。

- `TS001` は変更しない
- `TS002` は comment を伴う placeholder test を対象とする
- docstring-only は引き続き `TS001`
- `rule-catalog-scope.md` の対象外記述は、この方針に合わせて同一変更で更新する

この方針なら、既存挙動の回帰を避けつつ `TS002` の独立した metadata と finding を追加できる。

## 受け入れ条件の写像

Issue #4 の受け入れ条件を、承認後の実装では次の形に写像する。

- comment を伴う placeholder test で `TS002` finding が返る
- 実行文を持つ test では `TS002` が返らない
- docstring-only test は従来どおり `TS001` として扱われ、`TS002` へ移らない
- `human` と `json` 出力に `TS002` metadata が含まれる

Issue 文言を厳密優先する場合は、この写像を見直してから着手する。

## 作業流れ

### 1. Semantics 固定

- Issue #4、`rule-catalog-scope.md`、既存 `TS001` 実装の差分を確定する
- `TS002` が扱う source shape を文章と fixture 名で固定する
- `TS001` との非重複条件を明文化する

### 2. Metadata / Docs 更新

- `src/testsniff/docs/rule_metadata.py` に `TS002` metadata を追加する
- `docs/product-specs/rule-catalog-scope.md` を実装方針に合わせて更新する
- 必要なら関連 execution plan や設計文書の参照先を補う

### 3. Rule 実装

- token と AST を併用して `TS002` の判定ロジックを追加する
- 既存 registry に接続する
- canonical `Finding` の shape を維持する

### 4. テスト

- `TS002` positive / negative fixture を追加する
- rule 単体テストで `TS001` との非重複を確認する
- CLI integration test で `human` 出力を確認する
- `json` 出力に `TS002` metadata が出ることを確認する

### 5. 検証

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`
- 対象 fixture に対する `testsniff scan` 実行

## 変更候補ファイル

- `src/testsniff/rules/checks/`
- `src/testsniff/docs/rule_metadata.py`
- `src/testsniff/rules/registry.py`
- `tests/fixtures/`
- `tests/unit/`
- `tests/integration/test_cli.py`
- `docs/product-specs/rule-catalog-scope.md`

## 完了条件

- `TS002` の検出条件が文章とテストで固定されている
- `TS001` と `TS002` の責務分担が docs と実装で矛盾しない
- `TS002` metadata、rule、fixtures、tests が追加されている
- CLI と JSON 出力の両方で `TS002` を確認できる
- 関連ドキュメントが同一変更で更新されている

## 意思決定ログ

- 2026-03-20: Issue #4 の要求は、現行の `TS001` semantics と `rule-catalog-scope.md` の対象外定義に衝突しているため、実装前に plan で差分を固定する
- 2026-03-20: Python 文法上 `comment-only function` は成立しないため、`TS002` は token を伴う placeholder test へ要件を正規化しないと実装不能
- 2026-03-20: 既存回帰を避けるため、docstring-only は `TS001` に残す案を推奨方針とする

## リスク

- Issue 文言を厳密に解釈すると、`TS001` 非変更という非ゴールと両立しない
- token 依存の判定を雑に追加すると、`TS001` と `TS002` の差分が説明しづらくなる
- rule catalog を更新せずに実装だけ先行すると、採用済み spec と実装が再び乖離する

## 承認後の着手方針

承認後は、まず `TS002` の検出対象を fixture で固定し、その後に metadata、rule 実装、CLI / JSON 検証、docs 更新の順で進める。
