---
id: CR-KMK-05
title: "CR-05: 監査台帳（WORM風）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr05, audit, worm, ledger]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-05: 監査台帳（WORM風）— 詳細仕様

> **G**: 生成・改版・承認・公開の**不可変ログ**を保全する。  
> **O**: 署名/ハッシュ付きイベント、**エビデンスURI**（CIラン・Artifacts/Pages/Release等）。  
> **AC**: **欠落0、改竄検知100%**。

---

## 1. 用語
- **WORM風台帳**: 追記のみ許可（append-only）。既存行の**編集/削除/並べ替え**は禁止。  
- **イベント**: `create|modify|approve|publish|rollback|reject|archive` 等の事象。  
- **チェーンハッシュ**: 各レコードに `prev_hash` を持たせ、`hash = H(record_canonical + prev_hash)` で**改竄検知**。  
- **署名**: 既定 `ed25519`。`sig = Sign(priv, hash)`。公開鍵は `tools/docops_cli/config/audit_pubkeys.pem`（複数可）。  
- **エビデンスURI**: CIランURL、PR/Commit URL、PagesのビルドURL、Artifactsのパス、公開サイトのSnapshot URI等。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- 台帳フォーマット（NDJSON / JSON Lines）、正規化（JCS）、ハッシュ/署名、追記検証、エビデンス収集、CIゲート。

### 2.2 非スコープ（CR-05段階）
- 署名鍵のKMS運用/ローテーション（外部運用の前提）。  
- 透明性ログ（public transparency log）への外部登録（将来拡張）。

---

## 3. ファイル構成（既定）
```
artifacts/ledger/
  ├─ audit.ndjson              # 追記オンリーの本体
  ├─ manifest.json             # 監査対象のハッシュ集合（Merkle root 付き）
  ├─ proofs/                   # 署名・ルート・補助証跡
  └─ snapshots/                # 代表的成果物の固定スナップショット
tools/docops_cli/config/
  ├─ audit_rules.yml
  └─ audit_pubkeys.pem         # ed25519 公開鍵（複数）
```

---

## 4. データモデル
### 4.1 イベント（NDJSON 1行）
必須フィールド：
- `version`（例: "1"）  
- `event_id`（`ULID` など時系列順性を持つID）  
- `ts_utc`（ISO8601, `YYYY-MM-DDTHH:MM:SSZ`）  
- `actor`（`github:<login>` 等）  
- `event_type`（`create|modify|approve|publish|rollback|reject|archive`）  
- `subjects`（ID配列: 例 `["FR-LOG-12","RS-OBS-03"]`）  
- `paths`（関連ファイルパス配列）  
- `commit`（Git SHA） / `pr`（番号 or URL）  
- `evidence`（URI配列）  
- `content_hash`（対象差分や生成物の `sha256`、複数の場合は Merkle root）  
- `prev_hash`（前レコードの `hash`。先頭レコードは全零 or 固定値）  
- `hash`（`sha256` of `canonical(record_without_sig)` + `prev_hash`）  
- `sig`（`ed25519`署名; base64）

### 4.2 マニフェスト
- 対象範囲（今回のCIランで検査したファイル群）のハッシュ一覧と `merkle_root`。  
- 台帳本体 `audit.ndjson` の先頭/末尾ハッシュ、総件数、署名者情報。

---

## 5. 処理フロー（CI）
1. **収集**: 変更検出（`git diff`）→ 対象文書/生成物の `sha256` を計算。  
2. **イベント生成**: `create/modify/approve/publish/...` を文脈から決定（PR状態/ブランチ/ラベル）。  
3. **正規化**: JSON Canonicalization Scheme（JCS）でキー順・数値・文字列を正規化。  
4. **チェーン**: 直前の `hash` を `prev_hash` としてセット、`hash = H(record_canonical + prev_hash)`。  
5. **署名**: `ed25519` で `hash` に署名（署名鍵はCIシークレット）。  
6. **検証**: 既存 `audit.ndjson` に対して**追記のみ**であること、`prev_hash` の連続性、署名の妥当性を確認。  
7. **マニフェスト**: 収集ハッシュから Merkle 木を構築し `manifest.json` を生成、`proofs/` を保存。  
8. **公開**: Artifacts に保存（任意で `gh release upload`）、公開URLを次回イベントに**エビデンスURI**として記録。  
9. **ゲート**: 欠落/改竄/不連続が1件でもあれば **PR Fail**。

---

## 6. 機能要求（FR-05.x）
- **FR-05.1 追記検証**: `audit.ndjson` の差分が**末尾追記のみ**であることを検査（改行も含む）。  
- **FR-05.2 チェーン検証**: `prev_hash` 連続性、`hash` 再計算一致、`sig` 検証を**全行**で実施。  
- **FR-05.3 マニフェスト検証**: `merkle_root` 再計算一致。監査対象ファイル群の**欠落0**。  
- **FR-05.4 エビデンスURI**: すべてのイベントに最低1件以上の**到達可能なURI**を要求。  
- **FR-05.5 ロールバック記録**: `rollback` は**新規イベント**として記録。削除/改変は禁止。  
- **FR-05.6 可観測性**: 検証件数/失敗件数/時間のメトリクスを出力、Artifactsに保全。

---

## 7. 受入基準（AC）
- **AC-01 欠落0**: マニフェスト対象のファイル/生成物が台帳に**全て**反映。  
- **AC-02 改竄検知100%**: 任意1行の改変/並べ替え/削除に対して**常に Fail**。  
- **AC-03 決定性**: 同一入力で台帳出力は**ビット等価**（時刻以外の差異なし）。

---

## 8. CLI I/F（案）
```bash
# 追記・署名（CIで使用）
docops audit append   --rules tools/docops_cli/config/audit_rules.yml   --out artifacts/ledger

# 全検証（PRゲート）
docops audit verify   --rules tools/docops_cli/config/audit_rules.yml   --ledger artifacts/ledger/audit.ndjson   --manifest artifacts/ledger/manifest.json   --pubkeys tools/docops_cli/config/audit_pubkeys.pem   --fail-on-missing --fail-on-broken-chain
```

---

## 9. 設定（audit_rules.yml 概要）
- 署名アルゴリズム（ed25519 既定）、公開鍵ファイル、対象パス、エビデンス必須数、タイムスキュー許容。

---

## 10. CI（最小例）
```yaml
name: docops_audit
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_audit.yml'
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          pip install -U pip
          pip install pyyaml cryptography merklelib python-ulid
      - name: Append & Verify Ledger
        run: |
          python tools/docops_cli/audit.py append             --rules tools/docops_cli/config/audit_rules.yml             --out artifacts/ledger
          python tools/docops_cli/audit.py verify             --rules tools/docops_cli/config/audit_rules.yml             --ledger artifacts/ledger/audit.ndjson             --manifest artifacts/ledger/manifest.json             --pubkeys tools/docops_cli/config/audit_pubkeys.pem             --fail-on-missing --fail-on-broken-chain
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-audit-ledger
          path: artifacts/ledger
```
> 実体 `tools/docops_cli/audit.py` は CR-05 の成果物。

---

## 11. セキュリティ / 運用上の留意
- CI シークレットの**署名鍵は読み取り専用**で投入し、PR from fork では `append` を**実行しない**。  
- 公開鍵は本リポに保存（`audit_pubkeys.pem`）。ローテ時は**複数鍵併存**を許容。  
- 代表スナップショットを**Release assets**に保存すると URI 安定性が高まる。

---

## 12. トレース
- **satisfies**: BG-KMK-05（常時公開可能・監査性）  
- **depends_on**: CR-01..04（生成/リンク/検索/到達の成果を監査対象に）  
- **constrains**: CN-KMK-01..03

---

## 付録A: イベント例（整形表示）
```json
{
  "version": "1",
  "event_id": "01HYJZ9Z9J3CEPM2QKQ5P9Y7KE",
  "ts_utc": "2025-08-31T13:00:00Z",
  "actor": "github:alice",
  "event_type": "publish",
  "subjects": ["CR-KMK-03"],
  "paths": ["docs/00_concept/CR-03_hybrid_search_detail_v0.1.md"],
  "commit": "42a33a6e0268d32ebd6c9b0521726fa66d19628f",
  "pr": "https://github.com/org/repo/pull/123",
  "evidence": ["https://github.com/org/repo/actions/runs/1234567890"],
  "content_hash": "sha256:...merkle-root...",
  "prev_hash": "sha256:...",
  "hash": "sha256:...",
  "sig_alg": "ed25519",
  "sig": "base64:..."
}
```

## 付録B: 追記以外の差分検出
- 既存行の変更、途中への新規挿入、削除、空白や行末の変更も**Fail**。差分は `report.md` に抜粋表示。
