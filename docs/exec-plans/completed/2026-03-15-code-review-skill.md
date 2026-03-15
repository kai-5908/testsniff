# コードレビュー skill 追加計画

## 問題設定

一般的なソフトウェアエンジニアリング観点と、この repo 固有の設計・品質・運用ルールの両方を使えるコードレビュー用 skill が未整備です。

## スコープ

- `.codex/skills/code-review/` に新しい skill を追加する
- 一般レビュー観点と repo 固有観点を分離して参照資料化する
- AGENTS の導線を更新する

## 非ゴール

- 既存 skill の全面整理
- GitHub Issue 起点の plan workflow 変更
- 自動レビュー実行ツールの追加

## 作業流れ

1. 既存 review skill と repo 方針文書を確認する
2. `code-review` skill 本体を追加する
3. 一般レビュー用 checklist と repo 固有 checklist を追加する
4. `agents/openai.yaml` と AGENTS の導線を更新する
5. 文言整合性を確認する

## 意思決定ログ

- 一般レビュー観点を先に適用し、repo 固有観点は二次チェックにする
- token 消費を抑えるため、詳細な checklist は `references/` に分離する
- 出力は findings-first を前提にする

## 検証方針

- skill 文面が既存 skill と同じ構成になっていることを確認する
- `agents/openai.yaml` は生成スクリプトで作成する
- AGENTS から新 skill へ到達できることを確認する

## 完了条件

- `code-review` skill が trigger 可能な metadata と本文を持つ
- 一般観点と repo 固有観点の両方が参照可能である
- AGENTS に新 skill の導線がある
