# Pull Request Rules

- Status: Adopted
- Validation: Conceptual

## Goal

Pull Request を、Issue の受け入れ確認とリポジトリ品質の確認を行うための標準的なレビュー単位として扱うためのルールを定義します。

## Core Rules

### Rule 1: PR は Issue に対応づける

原則として、PR は起票済みの Issue に対応づけます。

PR には少なくとも1つの関連 Issue を記載し、可能であれば `Closes #...` を使って完了関係を明示します。

### Rule 2: PR は Issue の受け入れ確認を含む

PR は単なる変更説明ではなく、Issue に記載された受け入れ条件、DoD、検証方法を満たしたかを確認できる内容である必要があります。

### Rule 3: PR は 1 Task の境界を壊さない

Issue が 1 Task であるのと同様に、PR も原則として 1 Task の変更に絞ります。

無関係な変更を混在させてはいけません。

### Rule 4: PR テンプレートを使う

PR 作成時は `.github/pull_request_template.md` を使い、最低限以下を埋めます。

- なぜこの変更を行うか
- 関連 Issue
- DoR 確認
- DoD 確認
- 受け入れ条件の確認
- 検証

### Rule 5: 検証結果を PR に残す

コードや設定を変更する PR では、実行した検証コマンドと結果の要約を PR に記録します。

通常は以下のいずれか、または複数を含めます。
- `uv run ruff check src tests`
- `uv run ty check src`
- `uv run pytest -q --cov=testsniff --cov-report=term-missing --cov-fail-under=100`
- CLI 実行確認
- snapshot / integration test

### Rule 6: ドキュメント同期を PR で確認する

外部仕様、内部設計、運用ルールに影響する変更では、関連ドキュメントが同じ PR に含まれていることを確認します。

## Recommended Review Structure

レビュー時は以下の順で確認することを推奨します。

1. 関連 Issue が明確か
2. PR の変更範囲が 1 Task に収まっているか
3. 受け入れ条件を満たしているか
4. DoD を満たしているか
5. 検証結果が十分か
6. ドキュメント同期が取れているか

## Related Docs

- [docs/design-docs/issue-management-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/issue-management-rules.md)
- [docs/design-docs/git-operation-skill-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/git-operation-skill-rules.md)
- [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md)
- [docs/design-docs/internal-quality-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/internal-quality-rules.md)
