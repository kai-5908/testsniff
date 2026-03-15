# local git hooks 導入計画

## Status

- Status: Completed
- Owner: 現在の実装作業
- Started: 2026-03-15
- Completed: 2026-03-15

## 問題設定

CI は整備されていますが、開発者のローカル環境で commit / push 前に最低限の品質ゲートを実行する仕組みがありません。

そのため、明らかな lint error や test failure を push してから気づく可能性があります。

このリポジトリでは trunk-based development と topic branch 運用を採用しているため、ローカルでも次を早めに止めるべきです。
- staged Python への基本 lint violation
- merge conflict marker の持ち込み
- `main` への直接 push
- push 前の必須品質ゲート未実行

## スコープ

今回含めるもの:
- `.githooks/pre-commit` の追加
- `.githooks/pre-push` の追加
- hooks 導入用スクリプト追加
- hook 運用ルール文書追加
- 関連 skill / docs の更新

今回含めないもの:
- `pre-commit` framework の導入
- commit-msg hook
- server-side hook

## 方針

- `pre-commit` は高速に保つ
- `pre-push` は CI の最小ゲートに揃える
- hook は repo 管理し、`git config core.hooksPath .githooks` で有効化する

## 作業流れ

### 1. hook ルール定義

- pre-commit で止めるものを定義する
- pre-push で止めるものを定義する
- CI との責務分担を整理する

### 2. hook 実装

- `.githooks/pre-commit`
- `.githooks/pre-push`
- `.githooks/install.sh`

### 3. 文書反映

- hook 運用ルールの設計文書追加
- git skill と AGENTS 更新

## 検証計画

- hook script が shell syntax error を持たない
- install script で `core.hooksPath` を設定できる
- pre-commit / pre-push の意図が文書で説明されている

## 完了条件

- repo 管理の git hooks が追加されている
- install 手順がある
- hook 運用ルールが文書化されている
- git skill と整合している
