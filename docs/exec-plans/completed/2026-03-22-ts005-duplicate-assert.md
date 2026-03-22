# TS005 Duplicate Assert Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-20
- Completed: 2026-03-22
- Source Issue: [#7](https://github.com/kai-5908/testsniff/issues/7)
- Worktree: `/home/aoi_takanashi/testsniff/worktrees/feat-issue-7-plan`
- Approval: Approved

## 問題設定

Issue #7 は、同一 test 内で重複する assertion を `TS005` として検出する rule の追加を求めている。

ただし現行の採用済み product spec [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/worktrees/feat-issue-7-plan/docs/product-specs/rule-catalog-scope.md) には `Duplicate Assert` がまだ含まれていない。そのため、この task は rule 実装に加えて、catalog 追加と high confidence を維持できる重複 assertion の仕様境界を同じ change で固める必要がある。

## 目的

- `TS005` を static かつ explainable な v1 rule として成立する範囲で定義する
- 既存の test target 判定と assertion 認識に整合する重複検出方針を確立する
- bare `assert` と `unittest` assertion call を最低限の対象として実装計画に固定する
- metadata、fixture、tests、CLI 経路、関連 docs を一貫して更新できる実装計画を確定する

## 受け入れ条件の写像

Issue #7 の受け入れ条件は、実装と検証で次のように具体化する。

- 同一 standardized test target 内で、同じ assertion シグナルが重複した場合に `TS005` finding が返る
- 意図や対象が異なる assertion、または正規化結果が一致しない assertion では `TS005` が返らない
- `TS005` finding には stable な位置情報と `WHY` / `FIX` / `EXAMPLE` を支える metadata が含まれる
- CLI の human 表示と json 表示の双方で `TS005` が既存 rule と同じ契約で出力される
- [docs/product-specs/rule-catalog-scope.md](/home/aoi_takanashi/testsniff/worktrees/feat-issue-7-plan/docs/product-specs/rule-catalog-scope.md) に `TS005` が反映され、実装とのズレがない

## スコープ

今回含めるもの:

- `TS005` の判定対象 assertion と重複正規化ルールの定義
- rule 実装と registry 接続
- `src/testsniff/docs/rule_metadata.py` への `TS005` metadata 追加
- positive / negative fixture と unit / integration test 追加
- product spec と関連 docs の同期

今回含めないもの:

- runtime 情報や評価結果が必要な意味的同値判定
- helper 関数の内部を追跡して assertion の同値性を推論する解析
- 複数 test 間の重複検出
- auto-fix
- confidence を落として広く拾う曖昧な正規化

## 現状認識

- `ModuleContext.index.test_targets` により、同一 test target の走査基盤は既存 rule で利用済み
- `TS003` は bare `assert`、`self.assert*`、`pytest.raises(...)` / `pytest.warns(...)` / `pytest.fail(...)` を recognized assertion として扱っている
- ユーザーコメントにより、`TS005` は catalog 追加、`unittest` assertion の対象化、既存実装にそろえた reported location が優先方針として確定した
- 現行 catalog に `TS005` は未掲載のため、実装だけ先行すると repository の source of truth が分裂する

## 依存関係の整理

- issue にある「test 関数判定ルールが固まっていること」は、現行 main の `test_targets` 基盤と `TS001`-`TS003` 実装により満たされている
- 実装時は `TS003` の assertion 認識ロジックと重複定義をどう共有するかが設計上の主要依存になる

## 仮定

- `TS005` も既存 rule と同じ standardized test target を対象にする
- 初回実装では、AST から安定的に正規化できる assertion だけを対象にして `confidence=high` を維持する
- reported location は既存 rule 群に合わせて test 定義行を基本とする
- assertion 認識の基準は `TS003` と不整合を起こさないように、共有 helper 化または同等仕様の再利用を前提にする
- bare `assert` と `unittest` assertion call は初回実装の必須対象とする
- `pytest.raises(...)` は shared helper の再利用で無理なく扱える場合に初回から含め、難しい場合は follow-up に切り出す
- `assert x == 1` と `assert (x == 1)` のような構文上の軽微な差分は正規化で吸収するが、深い意味的同値判定までは踏み込まない

## 実装時の判断

- `pytest.raises(...)` は初回実装から外した
  - bare `assert` と `unittest` assertion call を high-confidence な最小スコープとして先に確定した
  - `pytest.raises(...)` まで含めるには shared helper の抽出と context manager 正規化を追加で詰める必要があり、今回は follow-up 領域に残した
- 分岐や loop をまたぐ重複は保守的に扱った
  - `if` / `try` / `match` は guaranteed path を意識した集合の intersection で後続重複判定に反映した
  - `for` / `while` は loop 実行回数と break の影響で false positive を出しやすいため、初回実装では loop 外への伝播を行わない保守的な設計にした

## 作業流れ

### 1. 仕様境界の確定

- Issue #7 の DoR とユーザーコメントに沿って、重複 assertion の定義と高誤検知ケースを文章で固定する
- bare `assert` と `unittest` assertion call を必須対象として固定する
- `pytest.raises(...)` は stretch goal として扱い、初回スコープに含める条件を shared helper 再利用可否で判断する
- v1 catalog へ `TS005` を追加する前提で docs 更新対象を確定する

### 2. 重複判定設計

- assertion ノードの収集単位を決め、reported location は既存実装にそろえて test 定義行を採用する
- AST ベースで説明可能な正規化キーを定義し、括弧差や軽微な構文差は吸収する
- test 全体を再帰走査して重複候補を集める方針を先に試し、複雑化する場合の縮退条件を明示する
- false positive を避けるため、非ゴールに落とすパターンを docs と tests に明示する

### 3. Rule 実装

- `TS005` rule module を追加する
- 必要なら assertion 認識 helper を `TS003` から抽出して共有化する
- bare `assert` と `unittest` assertion call の重複検出を先に成立させる
- `pytest.raises(...)` は共有化の延長で安全に扱える場合に追加する
- registry と scan 経路へ接続し、既存 formatter で描画できる状態にする

### 4. テスト

- positive fixture: 同一 test 内で bare `assert` または `unittest` assertion が明らかに重複する例
- positive fixture: 括弧差や軽微な構文差を正規化で吸収できる例
- negative fixture: 対象が異なる assertion、意味的には近いが正規化キーが一致しない assertion、非ゴールに置いた framework pattern
- unit test: 正規化ロジック、再帰走査境界、reported location
- integration test: CLI `scan` と `--format json` の回帰確認

### 5. ドキュメント同期

- rule catalog に `TS005` を追加し、初回実装の対象 assertion と非ゴールを明記する
- `rule_metadata` の説明文と examples を整備する
- `pytest.raises(...)` や path-sensitive 重複判定を縮退した場合は debt または別 issue に逃がす

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

- `uv run testsniff scan <fixture-dir> --select TS005` で重複 assertion fixture から `TS005` が返る
- 異なる assertion や非ゴール fixture では `TS005` が返らない
- `--format json` で `rule_id=TS005` と explanation fields が保持される

## 完了条件

以下を満たしたら完了とする。

- `TS005` の重複定義が docs、fixtures、tests で一致している
- Issue #7 の DoR にある定義・高誤検知ケース・fixture 方針・検証方法が解消されている
- `TS005` が default scan 経路または合意した選択経路で実行できる
- `TS005` が少なくとも bare `assert` と `unittest` assertion call の重複を検出できる
- metadata、unit/integration tests、CLI 確認が揃っている
- product spec と実装の整合が取れている

## 意思決定ログ

- 2026-03-20: Issue #7 を起点に plan を作成開始
- 2026-03-20: issue に明記された依存関係である test target 判定基盤は、現行 main の `ModuleContext.index.test_targets` と既存 rule 群により満たされていると整理
- 2026-03-20: `TS005` は採用済み catalog 未掲載のため、実装前に scope 反映の要否を確認事項として plan に昇格
- 2026-03-20: assertion 認識の契約を `TS003` と分岐させると rule 間で user expectation が崩れるため、共有または同等仕様を前提に計画化
- 2026-03-22: ユーザーコメントを受けて、catalog 追加、`unittest` assertion 対応、既存実装準拠の reported location を初回計画の確定事項へ変更
- 2026-03-22: `pytest.raises(...)` は「含めたいが無理はしない」優先度として、shared helper の再利用で自然に実装できる場合のみ初回スコープに含める方針に更新
- 2026-03-22: 分岐や loop をまたぐ重複は test-wide 収集を先に試し、複雑化する場合のみ縮退する段階的方針へ更新
- 2026-03-22: 実装では `bare assert` と `unittest` assertion call を `TS005` の対象として追加し、reported location は既存 rule と同じ test 定義行にそろえた
- 2026-03-22: `if` / `try` / `match` は path-sensitive に、loop は保守的に扱うことで false positive を抑える初回設計に確定した
- 2026-03-22: `pytest.raises(...)` の重複検出は follow-up とし、product spec では初回スコープ外であることを明文化した

## リスク

- 正規化を広げすぎると意味的同値判定へ寄って false positive が増える
- 正規化を狭めすぎると、ユーザーが直感的に重複と感じる assertion を取り逃がす
- `TS003` と assertion 認識がズレると、ある rule では assertion 扱いだが別 rule では非対象になる不整合が出る
- catalog 更新を伴うため、実装だけの小変更では済まず docs 同期が必須になる
- test-wide に重複を集めると、相互排他的な分岐での assertion を重複扱いして false positive を出す可能性がある

## 実施結果

- `TS005` rule を追加し、default scan 経路から利用できるよう registry へ接続した
- bare `assert` と `unittest` assertion call の重複を AST 正規化で検出できるようにした
- 括弧差と keyword 順は正規化で吸収し、reported location は test 定義行に統一した
- rule metadata、fixture、unit test、integration test、product spec を同期した
- 検証として `uv run ruff check src tests`、`uv run ty check src`、`uv run pytest -q` を通した
