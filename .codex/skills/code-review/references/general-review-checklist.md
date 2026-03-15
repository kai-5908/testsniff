# General Review Checklist

## Goal

変更を一般的なソフトウェアエンジニアリング観点で評価し、バグ、回帰、設計劣化、検証不足を見つける。

## Pass 1: Contract And Behavior

- 公開 API、CLI 振る舞い、設定契約、データ形式が変わっていないか
- 呼び出し側や既存テストと矛盾していないか
- 失敗時の挙動、戻り値、エラーメッセージ、exit code が意図せず変化していないか

## Pass 2: Correctness And Edge Cases

- 正常系だけでなく、空入力、異常入力、境界値、欠損データを扱えているか
- 前提条件チェックや例外処理が抜けていないか
- 条件分岐、初期値、ループ、状態更新に破綻がないか

## Pass 3: Design Fit

- 既存の責務境界に沿っているか
- 共通化や抽象化が早すぎず、逆に重複を放置していないか
- 短期の convenience のために将来の変更容易性を壊していないか

## Pass 4: Integration Completeness

- 実装に対応する tests、docs、config、fixtures、migration が追随しているか
- happy path だけでなく failure path や互換性影響が確認されているか
- 変更の影響範囲がコード上で閉じているという思い込みがないか

## Pass 5: Validation Quality

- テストが本当に契約を守れているか
- テストが実装詳細に過剰依存して brittle になっていないか
- 実施していない検証を実施済みのように扱っていないか

## Pass 6: Explanation Integrity

- コメント、docstring、説明文、PR 説明がコードと一致しているか
- 命名が実際の責務や副作用を隠していないか
- 将来の保守者を誤誘導する説明が残っていないか

## Severity Guide

- High: 契約破壊、明確なバグ、重大な回帰、危険な検証不足
- Medium: 将来の破綻可能性が高い設計劣化、統合漏れ、テスト妥当性の弱さ
- Low: すぐ修正できる明確性不足、軽微な docs 不整合

## Output Reminder

```text
Findings
1. [severity] path:line - concise title
   Evidence: 何が起きているか
   Why: なぜ問題か
   Impact: 何が壊れるか
   Fix: どう直すか

Open Questions
- 追加確認が必要な点

Summary
- findings が無い場合はその旨
- 未確認範囲、confidence、残留リスク
```
