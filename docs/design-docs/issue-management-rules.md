# Issue Management Rules

- Status: Adopted
- Validation: Conceptual

## Goal

GitHub Issue を、着手判断・実装・受け入れ確認に使える一貫した作業単位として扱うためのルールを定義します。

## Core Rules

### Rule 1: 1 Issue = 1 Task

1つの Issue は、1つの完了可能なタスクに対応させます。

1つの Issue に複数の独立タスクを混在させてはいけません。

### Rule 2: 依存関係は最小化する

Issue は、可能な限り他 Issue への hard dependency を持たないように分割します。

依存が必要な場合は、その依存がなぜ避けられないかを明記します。

### Rule 3: 全 Issue はテンプレートを使う

リポジトリで管理する実装・文書・運用タスクは、GitHub Issue Template を使って起票します。

必須項目:
- なぜやるか
- DoR
- DoD
- 受け入れ条件

### Rule 4: 受け入れ条件は検証可能であること

受け入れ条件は、レビューまたはコマンド実行によって満たされたか判断できる文で書きます。

曖昧な表現は避けます。

避ける例:
- だいたい動く
- 必要そうなドキュメントを更新する

望ましい例:
- `testsniff scan --format json` で `rule_id=TS003` を含む finding が返る
- negative fixture では finding が返らない

### Rule 5: DoR と DoD は issue ごとに具体化する

テンプレートのチェック項目をそのまま使ってよいですが、必要に応じて対象タスク向けに具体化します。

最低限:
- DoR は「着手に必要な前提が揃っているか」を示す
- DoD は「完了時に満たすべき成果」を示す

### Rule 6: 実装 Issue は検証方法を持つ

コードや設定を変更する Issue には、最低1つ以上の検証方法を記載します。

通常は以下のいずれか、または複数を含めます。
- unit test
- integration test
- snapshot test
- CLI 実行確認
- Ruff / ty / pytest

### Rule 7: 実装前に issue-to-plan workflow を通す

Issue を起点として実装に進む場合は、[docs/design-docs/issue-to-plan-workflow.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-to-plan-workflow.md) に従い、issue を取得して実行計画を作成し、人間承認後に着手します。

## Recommended Structure

Issue では、以下の順で情報を並べることを推奨します。

1. 概要
2. なぜやるか
3. スコープ
4. 非ゴール
5. 依存関係
6. DoR
7. DoD
8. 受け入れ条件
9. 検証方法
10. 参考資料

## Related Docs

- [docs/PLANS.md](/home/aoi_takanashi/testsniff/docs/PLANS.md)
- [docs/design-docs/issue-to-plan-workflow.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-to-plan-workflow.md)
- [docs/design-docs/pull-request-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/pull-request-rules.md)
- [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md)
- [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md)
