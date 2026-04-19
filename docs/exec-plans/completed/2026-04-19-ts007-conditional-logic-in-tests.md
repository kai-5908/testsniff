# TS007 Conditional Logic In Tests Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-04-19
- Completed: 2026-04-19
- Source Issue: [#9](https://github.com/kai-5908/testsniff/issues/9)
- Worktree: `/home/aoi_takanashi/testsniff/worktrees/issue-9-plan`
- Approval: Approved

## 問題設定

Issue #9 は、`if` などの条件分岐を含む test を `TS007` として検出する rule の追加を求めている。

ただし現行の採用済み product spec [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/worktrees/issue-9-plan/docs/product-specs/rule-catalog-scope.md) には `TS007` がまだ含まれていない。そのため、この task は rule 実装だけでは完結せず、v1 catalog への追加、対象にする分岐構文、初期 severity を同じ change で固定する必要がある。

## 目的

- `TS007` を static かつ explainable な v1 rule として成立する範囲で定義する
- 条件分岐として何を検出対象にするかを AST ベースで明文化する
- 既存の standardized test target 判定と整合する実装計画を確定する
- metadata、fixture、tests、CLI 出力、product docs を一貫して更新できる変更範囲を固定する

## 受け入れ条件の写像

Issue #9 の受け入れ条件は、実装と検証で次のように具体化する。

- v1 で対象にすると合意した条件分岐構文を含む standardized test target で `TS007` finding が返る
- 条件分岐を持たない test では `TS007` が返らない
- nested helper や対象外構文に由来する false positive を抑えた conservative な仕様になっている
- `TS007` finding には stable な位置情報と `WHY` / `FIX` / `EXAMPLE` を支える metadata が含まれる
- CLI の human 表示と json 表示の双方で `TS007` が既存 rule と同じ契約で出力される
- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/worktrees/issue-9-plan/docs/product-specs/rule-catalog-scope.md) に `TS007` の対象構文、初期 severity、confidence、非ゴールが反映される

## スコープ

今回含めるもの:

- `TS007` の対象構文を v1 用に定義する作業
- rule 実装と registry 接続
- `src/testsniff/docs/rule_metadata.py` への `TS007` metadata 追加
- positive / negative fixture と unit / integration test 追加
- product spec と関連 docs の同期

今回含めないもの:

- runtime 情報が必要な path-sensitive 解析
- 条件式の意味的複雑度や cyclomatic complexity の総合評価
- helper 関数の内部や別ファイル先まで追跡する解析
- auto-fix
- confidence を落として広く拾う曖昧なヒューリスティック

## 現状認識

- 既存 catalog の ratified v1 rule は `TS001` から `TS005` までで、`TS007` は未掲載
- `ModuleContext.index.test_targets` により standardized test target の列挙基盤はすでに存在する
- 既存 rule は `src/testsniff/rules/checks/` に個別 module として実装され、`src/testsniff/rules/registry.py` で有効化されている
- user-facing explanation は `src/testsniff/docs/rule_metadata.py` を source of truth として管理されている
- `TS004` と `TS005` は control-flow を保守的に扱う既存例になっており、`TS007` でも false positive を抑える設計が必要になる

## 依存関係の整理

- issue にある「test 関数判定ルールが固まっていること」は、現行 main の test target 基盤により満たされている
- `TS007` の仕様確定では、statement-level の明示的分岐に絞って high confidence を維持する
- severity は `warning` として catalog 追加時に rationale を明文化する

## 仮定

- `TS007` も既存 rule と同じ standardized test target を対象にする
- 初回実装では high confidence を維持するため、AST 上で明示的に分岐と説明できる `ast.If` のみを対象にする
- nested function / class / lambda の内部は既存 rule と同様に対象外とする
- reported location は既存 rule 群との一貫性を優先し、test 定義行にそろえる
- default severity は `warning` とし、catalog 反映時に rationale を文章で固定する
- `elif` は `ast.If` の連鎖として初回スコープに含める
- `ast.IfExp`、`ast.Match`、comprehension / generator expression の `if` clause は初回スコープから外す

## 仕様固定事項

- v1 の対象構文は statement-level の `ast.If` のみとし、`elif` は `ast.If` の連鎖として含める
- `ast.IfExp`、`ast.Match`、list comprehension / generator expression の `if` clause は初回スコープから外す
- finding location は test 定義行に統一する
- default severity は `warning`、confidence は `high` とする

## 作業流れ

### 1. 仕様境界の確定

- Issue #9 の DoR を満たすため、対象構文、severity、fixture 方針、検証方法を文章で固定する
- high confidence を維持できる最小スコープを優先し、対象外パターンを docs に明記する
- v1 catalog に `TS007` を追加する前提で product spec の更新内容を確定する

### 2. 条件分岐判定設計

- test target の executable body を走査し、statement-level の `ast.If` のみを保守的に検出する
- nested helper を除外しつつ、対象構文だけを検出する helper 設計を決める
- false positive を避けるため、expression-level branch や decorator-level branch を対象外として明文化する
- reported location を test 定義行に固定し、fixture と unit test で保証する

### 3. Rule 実装

- `TS007` rule module を `src/testsniff/rules/checks/` に追加する
- registry と scan 経路へ接続し、default scan と `--select TS007` の両方で利用可能にする
- metadata を追加して formatter 契約を満たす

### 4. テスト

- positive fixture: `if` / `elif` を含む top-level pytest test
- positive fixture: `if` を含む `unittest.TestCase` method
- negative fixture: 分岐を持たない test
- negative fixture: nested helper 内だけに分岐がある test
- negative fixture: `ast.IfExp`、`ast.Match`、comprehension clause を含むが初回スコープ外の test
- unit test: `ast.If` の検出境界、reported location、対象外ケースの保守性
- integration test: CLI `scan` と `--format json` の回帰確認

### 5. ドキュメント同期

- rule catalog に `TS007` を追加し、`ast.If` ベースの対象構文、`warning` severity、非ゴールを明記する
- `rule_metadata` の explanation と example を整備する
- 初回スコープから外した構文は follow-up 候補として記録する

## 変更候補ファイル

- `src/testsniff/rules/checks/`
- `src/testsniff/rules/registry.py`
- `src/testsniff/docs/rule_metadata.py`
- `tests/fixtures/`
- `tests/unit/`
- `tests/integration/test_cli.py`
- `docs/product-specs/rule-catalog-scope.md`
- 必要に応じて関連 docs

## 検証計画

最低限の検証:

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`

挙動検証:

- `uv run testsniff scan <fixture-dir> --select TS007` で条件分岐 fixture から `TS007` が返る
- 分岐を持たない test や対象外 fixture では `TS007` が返らない
- `--format json` で `rule_id=TS007` と explanation fields が保持される

## 完了条件

以下を満たしたら完了とする。

- `TS007` の対象構文が docs、fixtures、tests で一致している
- Issue #9 の DoR にある対象構文、warning 方針、fixture 方針、検証方法が解消されている
- `TS007` が default scan 経路または合意した選択経路で実行できる
- metadata、unit / integration tests、CLI 確認が揃っている
- product spec と実装の整合が取れている

## 意思決定ログ

- 2026-04-19: Issue #9 を起点に plan を作成開始
- 2026-04-19: 既存の ratified catalog に `TS007` が未掲載のため、rule 実装と同じ change で catalog 更新が必要と整理
- 2026-04-19: high confidence を維持するには、初回実装を明示的な AST 分岐構文に絞る方針が妥当と整理
- 2026-04-19: 初回スコープは statement-level の `ast.If` のみ、`elif` は包含、`ast.IfExp` / `ast.Match` / comprehension clause は対象外とする方針で固定
- 2026-04-19: severity は `warning`、reported location は test 定義行、confidence は `high` とする方針で固定

## リスク

- 対象構文を広げすぎると expression-level の曖昧な条件まで拾って false positive が増える
- 対象構文を狭めすぎると、ユーザーが直感的に条件分岐と捉える test を取り逃がす
- finding location の決め方次第で、既存 rule との一貫性と局所的な分かりやすさが衝突する
- catalog 更新を伴うため、実装だけの小変更では済まず docs 同期が必須になる

## 実施結果

- `TS007` rule を追加し、statement-level の `ast.If` / `elif` を検出対象として default scan 経路へ接続した
- `ast.IfExp`、`ast.Match`、comprehension filter clause は初回スコープ外として fixtures と tests で固定した
- rule metadata、product spec、unit test、integration test を同期した
- 検証として `uv run ruff check src tests`、`uv run ty check src`、`uv run pytest -q` を通した
