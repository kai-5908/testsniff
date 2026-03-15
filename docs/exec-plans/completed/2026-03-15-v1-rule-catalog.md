# v1.0.0 対象 Rule Catalog 実行計画

## Status

- Status: Completed
- Owner: 現在の文書更新タスク
- Started: 2026-03-15
- Completed: 2026-03-15
- Source issue: `#2 [v1.0.0] v1.0.0対象 rule catalog を確定する`
- Source URL: `https://github.com/kai-5908/testsniff/issues/2`
- Related debt: `TD-003`

## 問題設定

現状の repository では static-only の設計方針、reporting contract、`TS001` の初回実装までは揃っていますが、v1.0.0 で正式にサポートする smell rule の集合はまだ ratify されていません。

この状態のまま個別 rule の追加を進めると、次のぶれが発生します。

- 実装対象の優先順位が人によって変わる
- `severity` / `confidence` の初期値が場当たり的になる
- product spec と実装済み rule の整合が崩れる
- static-only で扱わない smell 群の境界が曖昧なまま残る

Issue #2 は、この曖昧さを `docs/product-specs/rule-catalog-scope.md` を中核に解消し、v1.0.0 の rule scope を文書として固定するための作業です。

## ゴール

- v1.0.0 で対象とする rule を明文化する
- v1.0.0 で対象外とする smell 群と除外理由を明文化する
- 対象 rule ごとの初期 `severity` / `confidence` 方針を揃える
- 関連ドキュメントを同期し、rule catalog を今後の Issue の基準にできる状態にする

## スコープ

今回含めるもの:

- `docs/product-specs/rule-catalog-scope.md` の更新
- v1.0.0 対象 rule 一覧の整理
- v1.0.0 対象外 rule / smell 群の整理と除外理由の記述
- 各対象 rule の初期 `severity` / `confidence` 方針の明文化
- 必要に応じた関連ドキュメントの同期
- `TD-003` の状態更新

今回含めないもの:

- 各 rule の実装
- auto-fix 方針の設計
- runtime 情報や機械学習を使う smell の対応
- editor integration や出力 format の追加
- 個別 rule の着手順そのものの実装計画化

## 仮定と判断

### 仮定

- v1.0.0 の product scope は引き続き static-only である
- `severity` は `error` / `warning` / `info`、`confidence` は `high` / `medium` を使う
- 既に実装済みの `TS001` (`Empty Test`) は v1.0.0 対象に含める前提で整理する
- catalog は「実装済み rule の一覧」ではなく、「v1.0.0 でサポートする予定の rule 定義」を表す

### 判断

- 未実装 rule の stable rule ID は、この issue では確定せず、follow-up 実装 issue で確定する
- `Long Test` のような threshold 依存 rule は v1.0.0 catalog から外し、`medium` confidence の根拠整理は今回扱わない
- 対象外の smell 群は、まず単純な一覧として明文化する

## 初期候補の扱い

現時点で repository 内の docs / plans / code から観測できる rule 候補は次です。

- `Empty Test`
- comments-only test
- missing assertion
- disabled / ignored test
- `Magic Number Test`
- `Long Test`

この一覧は final catalog ではなく、今回の issue で inclusion / exclusion を判断するための初期棚卸し対象として扱います。

## 作業流れ

### 1. Baseline 整理

- `docs/DESIGN.md`、`docs/product-specs/rule-catalog-scope.md`、`docs/design-docs/reporting-contract.md`、既存 plan を読み、static-only 境界と `severity` / `confidence` の制約を再確認する
- Issue #2 の DoR を plan 上で満たしているか確認する
- 実装済み rule と docs 上の例示 rule を分離して整理する

### 2. Rule 候補棚卸し

- 現在の docs / plans / implementation に現れている smell 候補を列挙する
- 各候補について「static-only で判定可能か」「安定した source location を返せるか」「説明と remediation を具体化できるか」を確認する
- 候補ごとに included / excluded / undecided を仮置きする

### 3. Catalog 本文更新

- `docs/product-specs/rule-catalog-scope.md` を v1.0.0 の authoritative catalog として再構成する
- 対象 rule は少なくとも以下の列を持つ表または同等の構造で記述する
  - rule 名
  - rule ID または ID 方針
  - 検出シグナルの要約
  - 初期 `severity`
  - 初期 `confidence`
  - 採用理由
- 対象外 rule / smell 群については除外理由を明記する

### 4. 関連ドキュメント同期

- `docs/design-docs/reporting-contract.md` と catalog の `severity` / `confidence` 例が矛盾しないか確認する
- 必要なら `docs/DESIGN.md` の scope 表現を catalog に合わせて補強する
- `docs/exec-plans/tech-debt-tracker.md` の `TD-003` を resolved へ更新する

### 5. レビュー準備

- Issue #2 の DoD と受け入れ条件を checklist 化して自己確認する
- 変更後の document 間で rule 名、scope 境界、`severity` / `confidence` の語彙が一致しているか確認する
- 次の individual rule issue がこの catalog を前提に起票できる状態か確認する

## 検証計画

この issue は docs-centered task なので、主検証は document review と整合確認で行います。

- `docs/product-specs/rule-catalog-scope.md` に v1.0.0 対象 rule が明記されていることを確認する
- 対象 rule ごとに初期 `severity` / `confidence` が記載されていることを確認する
- 対象外 smell 群と除外理由が追跡可能であることを確認する
- `TS001` の catalog 記述が現行実装と矛盾しないことを確認する
- `docs/design-docs/reporting-contract.md` の enum と example が catalog と整合することを確認する

## 完了条件

以下を満たしたらこの plan は完了とする:

- `docs/product-specs/rule-catalog-scope.md` に v1.0.0 対象 rule 一覧がある
- 対象 rule ごとの初期 `severity` / `confidence` 方針がある
- 対象外 rule / smell 群と除外理由が文書化されている
- 関連ドキュメントの整合が確認されている
- `TD-003` が open ではなくなっている

## 意思決定ログ

- 2026-03-15: Issue #2 を起点に、rule catalog の確定を docs 主体の作業として扱うことを決定。
- 2026-03-15: 既実装の `TS001` は catalog から除外せず、v1.0.0 対象 rule の基準例として扱う方針を仮置き。
- 2026-03-15: 未実装 rule の stable rule ID は catalog では固定せず、follow-up 実装 issue で確定する方針にした。
- 2026-03-15: v1.0.0 の対象 rule は `Empty Test` と `Disabled / Ignored Test` に絞り、他候補は precision または scope の理由で対象外とした。

## リスク

- smell 候補の母集団が docs 内の断片的な例示に寄っており、catalog が過少定義になる可能性がある
- 未実装 rule の ID 方針が未確定だと、catalog の安定性が不十分になる可能性がある
- `medium` confidence を含む rule を採用する場合、根拠説明が弱いと v1.0.0 の信頼性期待を損ねる可能性がある
