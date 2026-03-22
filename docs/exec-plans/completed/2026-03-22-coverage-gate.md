# Coverage Gate Execution Plan

## Status

- Status: Completed
- Owner: Codex
- Started: 2026-03-22
- Completed: 2026-03-22
- Worktree: `/home/aoi_takanashi/testsniff/worktrees/feat-coverage-gate-plan`
- Approval: Approved

## 問題設定

現状の品質ゲートは `ruff`、`ty`、`pytest` までであり、`src/testsniff` に対するテストカバレッジは測定も強制もされていない。

この状態では、テストが通っていても未実行コードが残っている可能性があり、回帰防止の強さを CI 上で担保できない。

今回の要求は次の 4 点を同時に満たす必要がある。

- coverage 測定ツールを導入する
- テストカバレッジが 100% でない場合は CI を失敗させる
- local の hook 運用と整合する位置に coverage チェックを組み込む
- 導入によって不足が見えた箇所には補完テストを追加する

## 目的

- `src/testsniff` 全体に対する coverage を定量化し、共有品質ゲートにする
- CI と local hook の判定条件を可能な限り同一化し、運用ドリフトを避ける
- coverage 導入後も `pre-commit` の負担を過度に悪化させず、日常開発で回る設計にする
- 100% 要件を満たすまで不足テストを補完し、緑の状態で完了させる

## スコープ

今回含めるもの:

- 開発依存への coverage 計測ツール追加
- `pytest` 実行時に coverage を測定し、100% 未満を失敗させる設定
- GitHub Actions CI の verify job への反映
- `.githooks/pre-push` への coverage 関連チェック追加
- coverage 未達で hook が失敗した際に、無意味なテスト水増しではなく、ドメイン理解とユースケース理解に基づく意味のある test 追加を促すメッセージ
- coverage 導入で露出した未カバー箇所への unit / integration test 追加
- hook / 品質ゲート関連ドキュメントの更新

今回含めないもの:

- branch coverage 100% の強制
- coverage HTML レポート配布や外部サービス連携
- `pre-commit` framework の導入
- `src/testsniff` 外の fixture ファイル群を coverage 対象に含めること

## 現状認識

- 現在の CI verify job は `uv run ruff check src tests`、`uv run ty check src`、`uv run pytest -q`、`uv build` で構成されている
- `.githooks/pre-push` も CI とほぼ同じく `uv run pytest -q` を実行している
- `.githooks/pre-commit` は staged diff check と staged Python files への Ruff に限定されている
- 現行テストスイートは `uv run pytest -q` で `63 passed` を確認済み
- 既存テストの直接カバー範囲は rule 実装、config loader、reporting、CLI が中心であり、`cli.arguments`、`compat/ruff_style.py`、`docs/rule_metadata.py`、`reporting/exit_codes.py`、`rules/registry.py`、`services/scan.py` などは coverage 導入後に不足候補として出る可能性が高い
- ルート checkout の `main` は現時点で `origin/main` に 1 commit 遅れているため、実装着手時は最新化要否を確認する

## 仮定

- 今回の「coverage 100%」は、まず `src/testsniff` に対する statement coverage 100% を意味するものとして扱う
- coverage policy は `pytest` 側の共有設定に寄せ、CI / hook からは同じ `uv run pytest -q` 系コマンドを使う
- `pytest-cov` は shared gate entrypoints から明示的に有効化し、focused local runs の `pytest` 契約は変えない
- coverage レポートは `term-missing` のみとし、XML 出力は今回の非スコープとする
- branch coverage は今回の強制対象に含めず、将来拡張できるよう設定追加の余地だけ残す
- coverage 導入後に露出した未カバー箇所のテスト補完は、この change の中で完結させる
- coverage 未達時のメッセージは、数値達成だけを目的にした無意味な test 追加を避け、対象コードの責務、想定利用、失敗モードを理解して test を設計するよう促す

## 方針

- `pytest-cov` を導入し、`src/testsniff` を coverage 対象に固定する
- coverage 閾値は単発の CLI 引数ではなく共有設定に寄せ、CI・hook・ローカル手動実行で判定差が出ないようにする
- `pre-push` は CI 最小ゲートと揃えるため、既存と同じ `ruff` -> `ty` -> `pytest` の順で実行し、最後の `pytest` を coverage gate にする
- `pre-commit` は既存どおり高速な静的チェックに留め、coverage gate は追加しない
- coverage レポートは `term-missing` のみとし、読みやすさと実装の単純さを優先する
- branch coverage は今回は導入せず、line coverage 100% を先に強制する
- coverage 未達時は、hook の失敗メッセージで「表面的な水増しではなく、ドメインとユースケースを理解した意味のある test を追加すること」を明示する
- coverage 導入後に不足が出た箇所は、この change の中で分岐や異常系を含む unit test を優先して補完し、必要なら CLI integration test を追加する

## 作業流れ

### 1. coverage policy の導入

- `pytest-cov` を dev dependencies に追加する
- shared gate entrypoints に coverage 対象、`term-missing`、fail-under 100 を明示する
- 手元の focused run と shared gate を分離しつつ、CI と `pre-push` では同じコマンドを使う

### 2. CI と hook の統一

- `.github/workflows/ci.yml` の `Pytest` step が coverage failure を拾うことを確認する
- `.githooks/pre-push` を CI と同等の coverage gate に揃え、`ruff` -> `ty` -> coverage 付き `pytest` の順序を維持する
- coverage failure の際に、意味のある test 設計を促すメッセージを `pre-push` に追加する
- `pre-commit` は現行の軽量ゲート維持とし、coverage を `pre-push` に集約する理由を docs に明記する
- `docs/design-docs/local-git-hook-rules.md` などの関連文書を更新する

### 3. baseline coverage 計測

- coverage 導入直後の測定結果を確認する
- どの module / path が 100% を阻害しているかを洗い出す
- テスト追加対象を unit / integration / config path に分類する

### 4. 不足テストの補完

- 直接未カバーになった public behavior から順に test を追加する
- 条件分岐、例外系、formatter 分岐、config 分岐などの未到達行を埋める
- 必要なら fixture を追加して scan flow の負パスや境界条件を検証する

### 5. 最終検証

- `ruff`、`ty`、coverage 付き `pytest`、`uv build` を通す
- hook script の shell syntax と対象判定を確認する
- docs と実装のコマンド差分がないことを確認する

## 変更候補ファイル

- `pyproject.toml`
- `.github/workflows/ci.yml`
- `.githooks/pre-push`
- `tests/unit/`
- `tests/integration/test_cli.py`
- 必要に応じて `tests/fixtures/`
- `docs/design-docs/local-git-hook-rules.md`
- 必要に応じて `docs/design-docs/branch-and-release-rules.md`
- 必要に応じて `README.md`

## 検証計画

最低限の検証:

- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q --cov=testsniff --cov-report=term-missing --cov-fail-under=100`
- `uv build`

coverage 導入後の確認:

- shared gate command で coverage 測定と fail-under 100 が有効になる
- CI の verify job が coverage 未達で失敗する
- `.githooks/pre-push` が coverage 未達を検知して push を止める
- `.githooks/pre-push` の coverage failure message が、無意味な test 水増しを避け、ドメイン理解とユースケース理解に基づく test 追加を促す
- `pre-commit` は従来の高速チェックのままで、coverage gate が混入していない

## 完了条件

以下を満たしたら完了とする。

- `src/testsniff` の coverage が 100% である
- coverage 100% 未満では CI が fail する
- coverage gate が `pre-push` に組み込まれている
- coverage 未達時に、意味のある test 追加を促すメッセージが `pre-push` に実装されている
- `pre-commit` は高速チェック専用のまま維持され、hook ポリシーと docs が整合している
- 不足していた箇所に対応するテストが追加されている
- 関連ドキュメントが更新されている

## 意思決定ログ

- 2026-03-22: coverage 導入は単なる dependency 追加ではなく、CI・hook・テスト補完・docs 更新を伴う横断タスクとして plan 化
- 2026-03-22: shared command を保つため、coverage policy は `pytest` 側に寄せる前提を採用
- 2026-03-22: `pre-commit` は高速性優先を維持し、coverage gate は `pre-push` と CI に集約する方針へ更新
- 2026-03-22: coverage レポートは `term-missing` のみとし、branch coverage は将来拡張事項に留める
- 2026-03-23: review 指摘を受け、coverage gate は global `pytest` defaults ではなく shared gate entrypoints に限定する方針へ修正
- 2026-03-22: `pre-push` の実行順は既存の `ruff` -> `ty` -> `pytest` を維持し、順序変更は行わない
- 2026-03-22: coverage failure message は、数値達成のための無意味な test 水増しではなく、ドメイン理解に基づく test 設計を促す内容を必須とする

## リスク

- 100% 閾値は小さな未到達分岐でも失敗するため、想定以上に test 追加が必要になる可能性がある
- `pre-push` に coverage gate を集約するため、push 前の待ち時間は増える
- coverage 設定を複数箇所に重複定義すると、CI と local の挙動がずれる
- `origin/main` との差分があるため、実装前に最新化しないと競合や再調整が発生しうる

## 承認後の着手方針

承認後は、まず coverage 設定と shared command を導入して baseline を測定し、その結果に基づいて不足テストを追加し、最後に hook / docs の整合を取る順で進める。
