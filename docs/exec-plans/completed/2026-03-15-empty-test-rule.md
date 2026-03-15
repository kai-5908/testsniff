# Empty Test Rule Execution Plan

## Status

- Status: Completed
- Owner: 現在の実装作業
- Started: 2026-03-15
- Completed: 2026-03-15

## 問題設定

リポジトリには静的解析用のスキャフォールドができていますが、まだ smell rule が1件も実装されていません。

次の一歩としては、以下を満たす最小の rule でアーキテクチャ全体を end-to-end で検証するべきです。
- 現在の static-only スコープに収まる
- high confidence の意味付けがしやすい
- 安定した source location を返せる
- rule metadata、reporting、registry wiring、tests を一通り通せる

## 最初の対象ルール

最初に実装する rule は `Empty Test` とします。

この rule を最初の対象にする理由:
- static-only で完結する
- Python AST 上で判定ロジックが単純
- 位置情報が安定している
- `severity` と `confidence` の初期値を説明しやすい
- 高度な parser helper を追加せずに、parsed module から formatted finding までの全経路を検証できる

## 想定するルール定義

初期の rule shape:
- Rule ID: `TS001`
- Headline: `Test body is empty`
- Default severity: `error`
- Default confidence: `high`
- Engine: `static`

初期の検出ルール:
- 実行可能な本文が実質空である test function を検出する

version 1 の empty-body 定義:
- 本文が `pass` のみ
- 本文が docstring のみ
- 先頭 docstring を除くと実行文が存在しない

今回の初回実装で対象外とするもの:
- `assert True` のような意味的に空に近いケース
- fixture だけを呼ぶ test
- comments-only detection
  ただし parser と token model の流れで自然に扱えるなら別

## スコープ

今回含めるもの:
- `src/testsniff/rules/checks/` 配下への具体 rule 実装
- rule metadata の追加
- registry への接続
- 安定した location を持つ finding の生成
- positive / negative fixture
- 既存 reporting test または新規 snapshot による formatter 確認

今回含めないもの:
- 複数 rule の同時実装
- auto-fix
- 新しい output format
- rule catalog 全体の確定
- 明白な範囲を超える性能最適化

## 設計メモ

実装は現在のアーキテクチャに従う:
- `parser` が `ModuleContext` を提供する
- `rules` が `ModuleContext` を解析する
- `reporting` が `Finding` を描画する
- `services.scan` が orchestration boundary を維持する

想定する AST 戦略:
- `ModuleContext.index.functions` から test function を列挙する
- 関数名の `test_` prefix で test function を判定する
- 対象関数ごとに先頭 docstring expression を取り除く
- 残りの本文が空、または `ast.Pass` だけなら finding を出す

初期 location 戦略:
- 関数定義の行と列を報告する

## 作業流れ

### 1. Rule Semantics

- v1 の正確な判定条件を定義する
- 除外条件と非ゴールを明文化する
- `severity=error` と `confidence=high` を固定する

### 2. Rule Metadata

- `TS001` の canonical metadata を追加する
- `WHY`、`FIX`、`EXAMPLE` を用意する
- references は最初は repo-local placeholder でもよいので必ず持たせる

### 3. Rule Implementation

- 具体的な rule module を追加する
- rule registry に登録する
- canonical `Finding` だけを返す

### 4. Test Coverage

- positive fixture を追加する
- negative fixture を追加する
- rule 単体テストを追加する
- CLI から finding が出ることを示す integration test を追加または更新する

### 5. Documentation Sync

- 実装で意味が明確になった箇所は rule-catalog や architecture docs に反映する
- 曖昧さが残る場合は debt か follow-up として記録する

## 検証計画

最低限の検証:
- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q`

挙動検証:
- `pass` のみを持つ test function が報告される
- docstring のみを持つ test function が報告される
- `pass` を持つ非 test helper function は報告されない
- 実際の assertion を持つ test function は報告されない
- JSON 出力に期待どおりの `TS001`、severity、confidence が含まれる

## 完了条件

以下を満たしたらこの plan は完了とする:
- `TS001` が実装され、デフォルトで有効になっている
- CLI で少なくとも1件の integration test から rule を確認できる
- metadata と examples が揃っている
- positive / negative test が通る
- ローカル品質ゲートが通る

## 意思決定ログ

- 2026-03-15: 最初の rule として `Empty Test` を選定。理由は、高 confidence の static smell として最も単純で、追加の高度な解析なしにアーキテクチャ全体を検証できるため。
- 2026-03-15: `TS001` を `test_` prefix を持つ関数に限定して実装。v1 では `pass` のみ、docstring のみ、docstring を除いた本文が空のケースを empty とみなす。

## リスク

- Python の test discovery 慣習は `test_` 命名以外もありうる
- docstring-only function を empty とみなすことについて、ユーザー側で認識差が出る可能性がある
- 最初の rule 実装によって rule metadata 保存方式の不足が露呈する可能性がある

## 次の候補

`Empty Test` の次に有力な候補:
- comments-only test
- missing assertion
- disabled / ignored test
