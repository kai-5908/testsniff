---
name: ai-coding-antipattern-review
description: Review code, design docs, tests, or change sets for anti-patterns common in AI-assisted coding. Use when asked to assess whether an implementation or design shows signs such as contract drift, shallow abstractions, partial integration, misleading tests, hallucinated rationale, silent fallbacks, or other low-rigor changes often introduced by LLM-assisted development. Prioritize general engineering judgment first, then apply repository-specific constraints as secondary checks.
---

# AI Coding Antipattern Review

AI 支援で作られた変更にありがちなアンチパターンを、設計・実装・テスト・文書の横断でレビューするための skill です。

「AI が書いたかどうか」を当てるのではなく、変更の質と整合性をレビューします。

## Review Stance

- 一般的な設計品質、変更品質、検証品質を最初に見る
- repo 固有ルールやローカル作法は二次チェックとして扱う
- 見た目や文体ではなく、契約、責務、証拠、検証の有無で判断する
- 所見は必ず根拠付きで出す
- 根拠が弱い推測を「AI 的」と断定しない

## Standard Flow

### 1. 最小限の前提を読む

- レビュー対象の差分、関連ファイル、要求や契約を確認する
- 必要なら architecture、spec、README、設計文書を最小限だけ読む
- 既存の公開インターフェース、設定契約、テスト方針を先に把握する

### 2. 一般観点で一次レビューする

- `references/anti-pattern-catalog.md` を使ってアンチパターンの有無を確認する
- まずは契約逸脱、責務崩れ、部分実装、検証不備、説明の不整合を優先して見る
- repo 固有の命名やレイアウトの違いだけで問題扱いしない

### 3. 統合の完了度を確認する

- 実装だけでなく tests、docs、config、運用影響が追随しているか確認する
- happy path だけ成立していて失敗系や移行影響が抜けていないか確認する
- 変更理由の説明がコードと一致しているか確認する

### 4. repo 固有制約を追加で確認する

- 一般観点での所見を作った後に、その repo のルールや方針との差分を確認する
- repo 固有ルールに適合していても、一般観点で不自然なら所見として残す
- repo 固有ルール違反しかない場合は、その前提を明示して所見を出す

### 5. findings first で報告する

- 重大度順に findings を並べる
- 各 finding に、証拠、問題の理由、影響、修正方向を含める
- findings が無い場合も、その旨と残余リスクや未確認点を明示する

詳細な進め方と出力形式は `references/review-flow.md` を参照します。

## Review Priorities

優先度の高い順に、次を重点的に見ます。

1. 契約や振る舞いの破壊
2. security / reliability に関わる危険な近道
3. 部分実装や統合漏れ
4. テストの見せかけの妥当性
5. 保守性を下げる空疎な抽象化
6. コメントや文書のもっともらしい不整合

## Evidence Rules

- ファイルと行番号を示す
- 「何が起きているか」と「なぜ問題か」を分けて書く
- 推測しかない場合は、断定せず open question として分離する
- 実際に未検証なら、未検証と明記する

## Boundaries

- スタイルの好みをアンチパターンとして扱わない
- AI らしい冗長表現だけで問題認定しない
- repo 固有の癖に過剰適合しない
- security 問題を見つけたら通常の finding として報告するが、深掘りが必要なら `security-review` など別 skill の利用も検討する

## Resources

- アンチパターンの判定軸: `references/anti-pattern-catalog.md`
- レビュー手順と出力形式: `references/review-flow.md`
