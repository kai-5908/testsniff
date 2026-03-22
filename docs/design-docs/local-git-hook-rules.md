# Local Git Hook Rules

- Status: Adopted
- Validation: Partially verified

## Goal

ローカル環境での commit / push 前に、CI と整合する最小品質ゲートを実行し、明らかな失敗を早期に止めるための hook ルールを定義します。

## Core Rules

### Rule 1: repo 管理の hooks を使う

このリポジトリでは `.githooks/` 配下の hook を使います。

有効化は次で行います。

```bash
bash .githooks/install.sh
```

### Rule 2: `pre-commit` は高速であること

`pre-commit` は、commit ごとに実行しても負担が大きすぎない内容に限定します。

現時点の対象:
- staged diff の `git diff --cached --check`
- staged Python file に対する `uv run ruff check`

### Rule 3: `pre-push` は CI 最小ゲートに揃える

`pre-push` は、CI の verify job と概ね同じ最小品質ゲートを実行します。

現時点の対象:
- `uv run ruff check src tests`
- `uv run ty check src`
- coverage 100% gate を含む `uv run pytest -q`

coverage 未達で `pre-push` が失敗した場合は、数値だけを満たすための表面的な test 水増しではなく、対象コードの責務、ドメイン、ユースケース、失敗モードを理解した上で意味のある test を追加するよう促すメッセージを表示します。

### Rule 4: `main` への直接 push を hook でも止める

`main` への直接 push は branch policy と矛盾するため、`pre-push` で拒否します。

### Rule 5: hooks は CI の代替ではない

local hook は早期フィードバックのためのものであり、CI を置き換えません。

GitHub Actions の CI が最終的な共有品質ゲートです。

## Non-Goals

- `pre-commit` framework の導入
- commit message lint
- server-side hook の管理

## Related Docs

- [docs/design-docs/git-operation-skill-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/git-operation-skill-rules.md)
- [docs/design-docs/branch-and-release-rules.md](/home/aoi_takanashi/testsniff/docs/design-docs/branch-and-release-rules.md)
- [.github/workflows/ci.yml](/home/aoi_takanashi/testsniff/.github/workflows/ci.yml)
