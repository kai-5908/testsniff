# Reporting Format

セキュリティレビューでは overview より findings を先に返す。要約は findings の後に短く付ける。

## Findings-First Rule

- 重大度順に列挙する。
- 各 finding は根拠のあるものだけを出す。
- 推測が混じる場合は、断定せず条件付きで書く。
- 単なる style 指摘や一般論だけで finding を埋めない。

## Per-Finding Template

各 finding には最低限次を含める。

1. Title
2. Severity
3. Location
4. Problem
5. Impact
6. Evidence
7. Remediation

短い書式例:

```md
1. High: Untrusted path reaches filesystem write
Location: path/to/file.py:42
Problem: User-controlled input is joined to a writable base path without canonical boundary validation.
Impact: An attacker may overwrite files outside the intended workspace.
Evidence: `target = base / user_path` is written without resolving and re-checking containment.
Remediation: Resolve the path, reject escapes outside the allowed root, and treat symlink traversal explicitly.
```

## No-Finding Case

finding がない場合でも、次は書く。

- 見た範囲
- 高リスク領域で未確認のもの
- confidence
- 残留リスク

短い書式例:

```md
No concrete security findings in the reviewed diff.
Reviewed: CLI argument handling, config loading, and filesystem writes.
Not reviewed: release workflow secrets handling and downstream deployment configuration.
Confidence: Medium.
Residual risk: Future plugin execution or network-enabled features would change the trust boundary.
```
