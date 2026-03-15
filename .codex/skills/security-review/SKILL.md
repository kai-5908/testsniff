---
name: security-review
description: Review code, configuration, architecture changes, and dependency choices from a security perspective. Use when the user asks for a security review, threat-oriented code review, secure design review, secret exposure check, trust-boundary analysis, or wants findings prioritized by severity with concrete evidence and remediation guidance.
---

# Security Review

## Overview

一般的な攻撃者視点でコード、設定、設計変更をレビューし、重大度順に findings を返す。

最初に汎用的な脅威観点で確認し、その後で repository や system 固有の境界、運用、制約を重ねる。特定 repo の事情に引きずられて基本的な観点を落とさない。

## Review Posture

- 事実と推測を分ける。確認できた内容だけを断定する。
- 実装の意図ではなく、悪用可能性、影響、境界違反を見る。
- 単なる品質懸念と security finding を混同しない。攻撃経路や権限境界に結び付くものを優先する。
- 「このプロジェクトでは通常こう使う」という前提を安全性の根拠にしない。
- finding がなければ、その旨を明記し、未検証範囲と残留リスクを書く。

## Standard Workflow

1. レビュー対象を特定する。

- 変更ファイル、周辺設定、依存追加、実行境界、外部入出力を把握する。
- 差分レビューなら、変更部分だけでなく、その変更が接続する trust boundary まで読む。

2. trust boundary と attack surface を整理する。

- 入力源、認証状態、権限、ファイルシステム、ネットワーク、外部サービス、秘密情報の流れを特定する。
- user input と internal input を区別する。

3. 汎用 security カテゴリで点検する。

- まず [review-categories.md](./references/review-categories.md) を使って横断的に確認する。
- repository に security doc や architecture doc がある場合は、その後で最小限読む。

4. exploitability と impact を評価する。

- 攻撃前提、必要権限、到達条件、データ影響、可用性影響、横展開可能性を整理する。
- 実害の薄い懸念は低優先度として分離する。

5. findings-first で報告する。

- 出力形式は [reporting-format.md](./references/reporting-format.md) に従う。
- 重大度順に並べ、各 finding に根拠と修正方針を付ける。

## Review Depth

- まず high-severity になり得る点を先に潰す。
- 時間が限られる場合でも、認証/認可、任意コード実行、秘密情報漏えい、path/file 操作、危険な外部通信、依存追加は必ず確認する。
- 詳細設計レビューまで求められていない場合も、公開 API や CLI entrypoint、config loader、plugin/script execution の境界は明示的に見る。

## Repo Adaptation

- repository 固有文書は補助として使う。
- security 原則、architecture、deployment、secrets 運用などの文書があるなら、最小限だけ読む。
- repo 固有の前提が一般的な安全原則と衝突する場合は、その衝突自体を finding または risk として扱う。

## Minimal Closeout

- findings がある場合は、最優先の remediation を短く添える。
- findings がない場合は、何を見て、何を見ていないかを書く。
- テスト不足や未読の重要ファイルがある場合は、 confidence を下げて明記する。
