# Review Flow

## Goal

レビュー対象が AI 支援開発のアンチパターンに陥っていないかを、一般的なエンジニアリング観点で評価する。

## Minimal Context Strategy

1. diff または対象ファイルを読む
2. その変更が依存する契約や設計文書を最小限だけ読む
3. repo 固有ルールは最後に追加確認する

最初から大量の docs を読んで repo ローカル最適に引きずられないようにする。

## Review Passes

### Pass 1: Contract And Behavior

- 何の契約を変える変更かを特定する
- 既存利用者、既存テスト、既存設定への影響を見る
- 契約変更があるのに明示されていない場合は最優先で指摘する

### Pass 2: Design Fit

- 変更が既存責務境界に沿っているかを見る
- 抽象化、分岐、再利用の仕方が局所最適になっていないかを見る
- 必要以上の indirection や複製を探す

### Pass 3: Integration Completeness

- tests、docs、config、migration、運用面が追随しているかを見る
- happy path 以外の取り扱いを見る
- 失敗時の可観測性や復旧戦略が適切かを見る

### Pass 4: Validation Quality

- テストが本当に契約を守れているかを見る
- 実装詳細依存の brittle test になっていないかを見る
- 実施していない検証を実施済みのように扱っていないかを見る

### Pass 5: Explanation Integrity

- コメント、docstring、設計説明、PR 説明がコードと一致しているかを見る
- 断定的な説明に根拠があるかを見る

## Severity Guide

- High: 契約破壊、security/reliability リスク、重大な統合漏れ
- Medium: 保守性低下、テスト妥当性の弱さ、将来高確率で破綻する構造
- Low: 局所的な明確性不足、軽微な docs 不整合、すぐ直せる改善点

## Output Shape

レビュー結果は findings first で出す。

```text
Findings
1. [severity] path:line - concise title
   Evidence: 何が起きているか
   Why: なぜアンチパターンと言えるか
   Impact: 何が壊れるか、何が将来つらいか
   Fix: どう直すべきか

Open Questions
- 断定できない点、追加確認が必要な点

Summary
- findings が無い場合はその旨
- 残余リスクや未確認の検証を明記
```

## Review Heuristics

- finding は「好み」ではなく「リスク」に結びつける
- repo 独自ルールを見つけても、まず一般原則で同じ問題を説明できるか試す
- 一般原則で説明できないものは repo 固有事項として分離する
- 重大な finding があるときは変更要約より先に出す
- findings が無い場合でも、未実施テストや未確認前提は残す
