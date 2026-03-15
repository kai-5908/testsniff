# Review Categories

この一覧は網羅チェック用の観点集です。すべてを機械的に列挙するのではなく、対象の attack surface に関係するものを優先する。

## 1. Input And Parsing

- 未検証入力がコマンド、SQL、パス、テンプレート、正規表現、HTML、シリアライザに流れていないか確認する。
- 想定外入力、巨大入力、ネスト、エンコーディング差異で壊れないか確認する。

## 2. Authentication And Authorization

- 認証前後の境界が曖昧でないか確認する。
- privilege check の抜け、 ownership check の欠落、 role の取り違えを確認する。
- server-side と client-side の責務分離が崩れていないか確認する。

## 3. Secrets And Sensitive Data

- secret の hardcode、ログ出力、エラーメッセージ露出、test fixture 混入を確認する。
- token、cookie、key、credential の保存先、寿命、マスキングを確認する。

## 4. Code Execution And Process Spawning

- `eval`、`exec`、動的 import、plugin 実行、shell 呼び出し、テンプレート実行を確認する。
- 引数結合、shell interpolation、PATH 依存、作業ディレクトリ依存を確認する。

## 5. Filesystem And Path Handling

- path traversal、symlink、unsafe temp file、上書き、権限過剰を確認する。
- user-controlled path を基準ディレクトリ外へ逃がしていないか確認する。

## 6. Network And External Services

- outbound 通信先、TLS 前提、redirect、webhook、SSRF 的経路を確認する。
- 外部 API 応答を信頼しすぎていないか確認する。

## 7. Serialization And Content Handling

- unsafe deserialization、pickle、YAML loader、template injection、Markdown/HTML rendering を確認する。
- content sniffing、MIME 前提、拡張子だけの信頼を確認する。

## 8. Dependency And Supply Chain

- 新規依存、post-install script、optional extra、外部 action、container base image を確認する。
- pinning、更新性、メンテ状況、権限要求を確認する。

## 9. Data Exposure And Logging

- 内部 path、stack trace、config、tenant data、PII、secret 断片の露出を確認する。
- debug log が production 経路に乗らないか確認する。

## 10. Denial Of Service And Resource Abuse

- 無制限ループ、再帰、巨大メモリ確保、全件読み込み、指数的処理を確認する。
- 攻撃者が安価に高コスト処理を起こせるか確認する。

## 11. Integrity And State Transitions

- 状態遷移の順序、二重実行、rollback 不足、部分失敗を確認する。
- 署名、checksum、version check、compare-and-swap の有無を確認する。

## 12. Environment And Deployment Boundaries

- dev 前提の挙動が production に漏れていないか確認する。
- feature flag、debug mode、test hook、admin endpoint の露出を確認する。
