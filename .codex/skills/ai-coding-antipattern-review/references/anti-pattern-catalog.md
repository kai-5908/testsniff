# AI Coding Antipattern Catalog

このカタログは、AI 支援実装で起きやすい低品質変更を一般観点で見抜くための補助資料です。

各項目は「AI 特有」ではなく、人間実装にも起こりうる問題として扱います。

## 1. Hidden Contract Drift

### Signal

- 既存 API、CLI、設定、返却形式、エラー挙動を静かに変えている
- 変更理由が局所実装の都合に寄っている

### Why It Matters

- 呼び出し側や運用フローを壊しやすい
- diff 上では小さく見えても影響範囲が広い

### Typical Evidence

- 関数シグネチャや出力形式だけが変わり、呼び出し側の整合確認がない
- 既存エラーを握りつぶして別の成功扱いにしている

## 2. Hollow Abstraction

### Signal

- 実質 1 回しか使わない wrapper、hook、strategy、manager を増やしている
- 将来拡張を理由に抽象化しているが、現在の制約が表現されていない

### Why It Matters

- 読み手の負荷だけ増え、変更点の局所性が失われる
- 小さな変更に不要な indirection を持ち込む

### Typical Evidence

- pass-through 関数や thin facade だけが追加されている
- 抽象化の結果、重要な前提条件が見えなくなっている

## 3. Patch Stacking Instead Of System Fit

### Signal

- 既存構造に合わせず、その場しのぎの分岐や例外処理を積み上げている
- 同種ロジックが別の場所に複製される

### Why It Matters

- 将来の変更コストとバグ表面積を増やす
- 部分的には動いても全体設計を崩す

### Typical Evidence

- 既存ユーティリティを使わずに似た処理を再実装している
- 特殊ケース対応が本流コードに入り込み責務が曖昧になる

## 4. Partial Integration

### Signal

- 実装だけ入り、tests、docs、config、migrations、telemetry が追随していない
- 正常系だけ通し、失敗系や既存互換性が未確認

### Why It Matters

- マージ直後は動いて見えても、運用や将来変更で壊れる
- 「実装した」ように見えるが製品変更として未完成

### Typical Evidence

- 新しい設定項目が追加されたのに読み込みや説明がない
- ルールや振る舞いを変えたのにメッセージや docs が古いまま

## 5. Test Theatre

### Signal

- テストが実装の表面をなぞるだけで契約を検証していない
- 失敗系、境界条件、回帰ポイントが抜けている

### Why It Matters

- 緑のテストが品質保証ではなく安心感の演出になる
- リファクタや仕様変更で壊れやすい

### Typical Evidence

- モックしすぎて本当に守りたい振る舞いが検証されていない
- 期待値が実装詳細に過度依存している

## 6. Hallucinated Rationale

### Signal

- コメント、docstring、PR 説明、WHY/FIX がコードと一致しない
- 存在しない前提や未確認の効果を断定している

### Why It Matters

- レビューアと将来の保守者を誤誘導する
- 誤った安心感を与える

### Typical Evidence

- 「安全」「後方互換」「高速」などの主張に証拠がない
- 実装が説明した仕様を満たしていない

## 7. Silent Fallback Or Over-Permissive Recovery

### Signal

- エラー時に黙ってデフォルトへ戻す
- 失敗を成功扱いに近い形で吸収する

### Why It Matters

- 監視しづらい不正確な挙動を生む
- security や reliability の問題に発展しやすい

### Typical Evidence

- broad exception を拾って空文字や空配列を返す
- 設定ミスや不正入力が利用者に見えない

## 8. Documentation Lag Hidden By Polished Prose

### Signal

- 文書だけ一見整っているが、実装や現実の手順と噛み合っていない
- 用語や責務境界が古いまま残る

### Why It Matters

- AI 生成文がもっともらしく見えるため見逃しやすい
- docs を信じた利用者や次の実装者を誤らせる

### Typical Evidence

- 新仕様が反映されていないのに文面だけきれい
- 検証済みと仮定が混在している

## 9. Tooling Or Dependency Overreach

### Signal

- 小さな変更のために新規依存や複雑なツール導入をしている
- 標準機能で足りる場面で過剰な仕組みを追加している

### Why It Matters

- 保守コストと攻撃面を不必要に増やす
- 問題の本質より導入コストが大きくなる

### Typical Evidence

- 数行の処理のために重いライブラリを追加している
- 既存の build/test/deploy フローへ新しい不安定要素を持ち込む

## False Positive Guardrails

- 単なるコードスタイル差分を問題化しない
- 明示的な設計判断とトレードオフが記録されているなら、それを先に評価する
- 一時的な制約回避でも、スコープ、リスク、フォローアップが明示されていれば severity を下げてよい
- 「AI っぽい書き方」だけでは finding にしない
