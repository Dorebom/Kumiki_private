---
id: STD-KMK-LINT-01
title: DocLintルール標準（Kumiki）
version: "1.0"
status: draft
parent: STD-KMK-00_INDEX
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01", "STD-KMK-TRACE-01"]
---

# 1. 目的と適用範囲
Kumiki の文書群に対し、**自動Lint**で守るべき最小～推奨ルールとゲート基準を定める。  
対象: `CR, RS, HLF, FR, NFR, CN, DD, TS, ADR, OPS, STD` の Markdown + YAML FrontMatter（FM）。

# 2. ルール体系と重大度
- **ルールIDの構成**: `LINT-<CAT>-<NNN>`（例: `LINT-FM-001`）。  
  - `CAT`: `FM`（FrontMatter）, `VOC`（語彙）, `TR`（Trace）, `ID`（ID命名）, `REG`（IDレジストリ）, `DOCS`（サイト/MkDocs）
- **重大度**: `error`（ゲートで落とす） / `warn`（許容するが要訂正） / `info`（通知）
- **ゲート方針**: PR=厳しめ（unknown_refs=0 等）/ Nightly=網羅（全系）/ Release=最厳（循環ゼロ・deprecated参照ゼロ）

# 3. 出力形式と終了コード
- 出力: `artifacts/lint/report.json`（JSON Lines 推奨）, `artifacts/lint/report.sarif`（任意）  
- 終了コード: `0=PASS`, `1=WARN許容PASS`, `2+=ERROR`  
- 各項目: `{id, severity, file, line, message, hint, rule_ref}`

# 4. ルール詳細
## 4.1 FM（FrontMatter）系 — 参照: STD-KMK-FM-01
- **LINT-FM-001 (error)**: 必須キー欠落（`id/title/version/status`）。
- **LINT-FM-002 (error)**: ネスト/オブジェクトの使用禁止（FMはフラット）。
- **LINT-FM-003 (error)**: 配列に**ID文字列以外**が含まれる（オブジェクトや空文字）。
- **LINT-FM-004 (warn)**: 空値キーの定義（空なら**キーごと省略**）。
- **LINT-FM-005 (error)**: `status` が定義外値（`draft/review/approved/deprecated` 以外）。
- **LINT-FM-006 (error)**: `parent` が**複数**または欠落（正規親は 1 つ）。
- **LINT-FM-007 (warn)**: `note` が長文（閾値>300文字）。本文に移す。

## 4.2 VOC（語彙）系 — 参照: STD-KMK-VOC-01
- **LINT-VOC-010 (error)**: 語彙外キーの使用（規定表以外のキー）。
- **LINT-VOC-011 (error)**: 別名・同義語の使用（`derives_from/implements/relates_to/...`）。
- **LINT-VOC-012 (error)**: `children`/関係配列に**ID以外**が混在。

## 4.3 TRACE（トレーサビリティ）系 — 参照: STD-KMK-TRACE-01
- **LINT-TR-020 (error)**: 入口トレース欠落（`FR/NFR/DD/TS` が `refines|satisfies` を 1 件も持たない）。
- **LINT-TR-021 (warn|error)**: 出口トレース欠落（`FR/NFR` が **TS に到達不能**）。閾値は設定で選択。
- **LINT-TR-022 (error)**: 孤立ノード（上流/下流どちらにも接続なし）。
- **LINT-TR-023 (error)**: 既知関係の**有向サイクル**（`refines/satisfies/depends_on/constrains`）。
- **LINT-TR-024 (warn)**: 子が親からの関係を**全削除**（inherit+delta 逸脱）。

## 4.4 ID（命名）系 — 参照: STD-KMK-ID-01
- **LINT-ID-030 (error)**: ID形式違反（Regex: `^([A-Z]{2,5})(?:-([A-Z0-9]{2,8}))?(?:-([A-Z]{2,8}))?-([0-9]{2,})(?:\.[0-9]+)*$`）。
- **LINT-ID-031 (error)**: ID重複（レジストリまたは全走査でユニーク性違反）。
- **LINT-ID-032 (warn)**: ID長すぎ（>32 文字）。
- **LINT-ID-033 (error)**: テンプレ用 `xx` を含むIDの使用。

## 4.5 REG（IDレジストリ）系 — `id_registry.yml`
- **LINT-REG-040 (error)**: レジストリ未登録（必須に設定されているのに未登録）。
- **LINT-REG-041 (error)**: パス不一致（`id_registry.yml` の `path` と実ファイルの齟齬）。
- **LINT-REG-042 (warn)**: `status` や `title` の非同期（メタ差分）。

## 4.6 DOCS（サイト/MkDocs）系 — 基本の動作健全性
- **LINT-DOCS-050 (error)**: リンク切れ/行き止まり（相対リンク解析）。
- **LINT-DOCS-051 (warn)**: 日本語検索の辞書未設定（拡張時）。
- **LINT-DOCS-052 (warn)**: 孤立ページ（サイト側の到達不能）。

# 5. 設定スキーマ（例: `tools/docops_cli/config/lint_rules.yml`）
```yaml
version: 1
severity_overrides:
  LINT-TR-021: error     # 出口トレース欠落をエラーに引き上げ
thresholds:
  unknown_refs: 0
  max_note_length: 300
gates:
  pr:
    fail_on: [error]
  nightly:
    fail_on: [error]
  release:
    fail_on: [error, warn]   # リリース時は warn も禁止にする例
ignore:
  - path: "docs/**/drafts/**"
  - id: "RS-EXPERIMENT-**"
```

# 6. CLIインターフェース（想定）
```bash
# 全体Lint（JSON出力）
python tools/ci/doclint.py --root docs --out artifacts/lint/report.json --format json

# しきい値と設定ファイル
python tools/ci/doclint.py --config tools/docops_cli/config/lint_rules.yml

# SARIF 併産
python tools/ci/doclint.py --sarif artifacts/lint/report.sarif
```

# 7. レポート例（JSON Lines）
```json
{"id":"LINT-FM-001","severity":"error","file":"docs/02_requirements/RS-FR-12.md","line":3,"message":"必須キー 'status' がありません","hint":"FMに status: draft を追加してください","rule_ref":"STD-KMK-FM-01"}
{"id":"LINT-TR-021","severity":"warn","file":"docs/02_requirements/RS-NFR-06.md","line":1,"message":"出口トレース（TS到達）がありません","hint":"children に TS-* を 1 つ以上追加","rule_ref":"STD-KMK-TRACE-01"}
```

# 8. 運用・除外
- 除外ファイル: `.doclintignore`（gitignore形式）をルートに置く。  
- `.obsidian/` や生成物ディレクトリはデフォルト除外。  
- 一時的に警告を容認する場合は **設定で severity を下げる**（原則は短期運用）。

# 9. 成果物とゲート
- PR: `unknown_refs=0`, `error=0` を必須。  
- Nightly: すべてのルールを実行し、**差分（delta）**も要確認。  
- Release: `warn=0` のクリーン状態でタグ付け。

# 変更履歴
- 1.0: 初版（FM/VOC/TRACE/ID/REG/DOCS の基準と設定/出力/ゲート運用）。
