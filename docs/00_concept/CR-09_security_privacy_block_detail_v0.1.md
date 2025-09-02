---
id: CR-KMK-09
title: "CR-09: セキュリティ/機密情報ブロック（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr09, security, pii, secret, dlp]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-09: セキュリティ/機密情報ブロック（詳細仕様）

> **G**: PII/秘密情報を**検知して PR を Fail** し、公開事故を防止する。  
> **O**: 署名/ハッシュ化した**検出レポート**（JSON/MD）、**マスク済み抜粋**、抑止手段（アロウリスト/抑止コメント）、**修正提案**。  
> **AC**: **既知パターン検知 100%、誤検知 ≤ 2%**。

---

## 1. 対象と用語
- **PII**: 個人を特定し得る情報（メール、電話、住所、国民番号系、クレジットカード等）。
- **Secrets**: 資格情報・鍵（API Key/Token、OAuth クライアントシークレット、JWT、Private Key、認証情報を含む URL 等）。
- **Confidential URLs/Links**: 社内限定のリンクや内部ホスト名（例: `*.corp.local`, `confluence`, `jira`, VPN 限定 URL など）。
- **マスク（Redaction）**: 検出スニペットの露出を避けるため、先頭/末尾以外を `•` で置換。  
- **アロウリスト（Allowlist）**: テスト用ダミーや公開済みキーの**明示許可**（期限付き）。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- 規則ベース＋ヒューリスティック（エントロピー/コンテキスト）による検出、マスク化、抑止、CI ゲート、レポート出力。

### 2.2 非スコープ（CR-09段階）
- 機械翻訳/要約における意味的 DLP。バイナリの OCR は**任意**（デフォルト off）。

---

## 3. 入出力
### 3.1 入力
- `docs/**/*.md`, `**/*.yml`, `**/*.json`, 一部コード（`*.py,*.ts,*.js,*.env` 等）。
- ルール: `tools/docops_cli/config/secscan_rules.yml`、アロウリスト: `secscan_allowlist.yml`。

### 3.2 出力
- `artifacts/secscan/<run>/report.json|md`（**マスク済み**）、`findings.csv`、`patches/`（削除/マスクの提案）  
- `artifacts/secscan/<run>/proofs/`（ハッシュ化・切り出し 32 文字程度の**不可逆要約**）。

---

## 4. 検出カテゴリとルール（抜粋）
### 4.1 Secrets（SC*）
- **SC100**: AWS Access Key ID（`AKIA[0-9A-Z]{16}` 等）。
- **SC101**: AWS Secret Access Key（エントロピー + 40 文字 Base64/Hex 近似）。
- **SC110**: Google API Key（`AIza[0-9A-Za-z-_]{35}`）。
- **SC111**: GitHub Token（`gh[pousr]_[0-9A-Za-z]{36,}`）。
- **SC120**: RSA/EC/SSH Private Key ブロック（`-----BEGIN ... PRIVATE KEY-----`）。
- **SC130**: JWT（`^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$` + HS/RS header 検査）。
- **SC140**: Basic 認証情報入り URL（`https://user:pass@host`）。
- **SC150**: OAuth Client Secret / Slack Bot Token / 主要クラウド署名キー（ベンダ別プレフィクス）。

### 4.2 PII（SX*）
- **SX001**: メール（`name@domain`。`example.com/org/net` 等はアロウリスト）。
- **SX002**: 国際/国内電話（E.164 / JP 国内形式）。
- **SX003**: クレジットカード（Luhn 検証必須）。
- **SX004**: 住所の高確度パターン（郵便番号+都道府県+市区町村 近接）。
- **SX010**: マイナンバー候補（12桁 + 近傍語「個人番号」「マイナンバー」 + チェック桁検証）。

### 4.3 Confidential Links（SL*）
- **SL001**: 内部ドメイン/ホスト名の露出（`*.corp.local`, `intranet`, `vpn`, `internal` 等）。
- **SL010**: 社内 Wiki/Issue トラッカの直リンク（`confluence`, `jira`, `redmine` 等）。

---

## 5. ヒューリスティック / スコアリング
- **エントロピー**: `H ≥ 3.5`/byte を疑似秘密値候補。
- **コンテキスト語**: 近接 32 文字に `secret|token|password|apikey|authorization|bearer` で +0.2。
- **ペア検知**: `AKIA...` が 近傍にあれば Secret Access Key のしきい値を -0.1。
- **最終スコア**: `score = 0.6*regex + 0.2*entropy + 0.2*context`。`score ≥ 0.8` を確定、`0.65–0.8` は要確認。

---

## 6. 失敗ポリシーと抑止
- **Fail 条件**: `severity >= high` が 1 件でも → **PR Fail**。`medium` は件数閾値で Fail 可（設定）。
- **抑止コメント（スコープ限定）**:  
  ```md
  <!-- secscan:ignore SC110 until=2025-12-31 reason="公開サンプルキー" scope=line -->
  ```
  - `scope`: `line|block(file)|id:<fingerprint>`。`until` 期限超過で自動失効。  
- **アロウリスト**: `secscan_allowlist.yml` に **fingerprint**（SHA-256の先頭 10–16 桁）で登録。

---

## 7. マスク/証跡（安全なレポート）
- スニペットは `abcdEFGH` → `ab••••••GH` のように**中間マスク**。  
- 詳細レポートは **Artifacts のみ**（PR には件数/規則 ID を短文通知）。  
- レポート内の原文は保存せず、**ハッシュ**を保存して再現性を担保。

---

## 8. CLI I/F（案）
```bash
# スキャン（PRゲート）
docops secscan scan   --rules tools/docops_cli/config/secscan_rules.yml   --allow tools/docops_cli/config/secscan_allowlist.yml   --out artifacts/secscan --format json,md --fail-on-high

# 発見の説明（規則情報）
docops secscan explain --id SC110

# マスク提案パッチを生成
docops secscan suggest --out artifacts/secscan/patches
```

---

## 9. 設定（secscan_rules.yml 概要）
- 対象パス、除外、OCR の有無、しきい値・Fail ポリシー、ベンダ別プレフィクス、内部ドメイン一覧、PR コメント出力の詳細度。

---

## 10. 受入基準（AC）
- **AC-01**: 既知パターン（ゴールドセット）に対する**検知率 100%**。  
- **AC-02**: **誤検知 ≤ 2%**（アロウリスト/抑止を含まず素検出で）。  
- **AC-03**: 2,000 ファイルで **≤ 90s**。

---

## 11. CI（最小例）
```yaml
name: docops_secscan
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_secscan.yml'
jobs:
  secscan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          pip install -U pip
          pip install pyyaml regex python-Levenshtein
      - name: Scan
        run: |
          python tools/docops_cli/secscan.py scan             --rules tools/docops_cli/config/secscan_rules.yml             --allow tools/docops_cli/config/secscan_allowlist.yml             --out artifacts/secscan --format json,md --fail-on-high
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-secscan-artifacts
          path: artifacts/secscan
```
> PR へのコメントは**件数とルール ID のみ**。具体値は**マスク**して公開しない。

---

## 12. セキュリティ運用
- **fork PR** では検出結果の詳細を**コメントしない**。Artifacts の公開範囲に注意。  
- 発見された秘密値は **即時失効/ローテーション**を推奨（提案テンプレを同梱）。  
- レポート/Artifacts の保持期限は **最短**（例: 14日）。

---

## 13. トレース
- **satisfies**: BG-KMK-05（常時公開可能・事故防止）  
- **depends_on**: CR-01（FM/DocLint）  
- **constrains**: CN-KMK-01..03

---

## 付録A: 抑止コメントの例
```md
<!-- secscan:ignore SC100 until=2025-12-31 reason="AWS 公式ドキュメント引用" scope=line -->
```
## 付録B: report.json の例（抜粋・マスク済み）
```json
{
  "summary": {"files": 32, "findings": 2, "high": 1, "medium": 1, "time_sec": 2.1},
  "findings": [
    {
      "rule_id": "SC110", "category": "secret", "severity": "high",
      "path": "docs/guide.md", "line": 42, "span": [10, 46],
      "snippet_masked": "AIza••••••••••••••••••••••••••••abcd",
      "fingerprint": "a1b2c3d4e5", "score": 0.92
    }
  ]
}
```
