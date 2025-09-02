---
id: CR-KMK-10
title: "CR-10: CIゲート & 公開フロー — 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr10, ci, publish, pages]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04","CR-KMK-05","CR-KMK-06","CR-KMK-07","CR-KMK-08","CR-KMK-09"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-10: CIゲート & 公開フロー（詳細仕様）

> **G**: PR で **DocLint / Indexing / Trace** を実行し、ゲート合格時のみ **公開** する。  
> **AC**: **CI合計 < 10分**、再実行で**決定的（非フレーク）**。

---

## 1. スコープ / 非スコープ
### スコープ
- CI ワークフロー（PR・main push）と **ゲート集約**、Pages への公開（Artifacts 連携を含む）。
- 決定性の担保：**依存の固定**、乱数シード固定、タイムゾーン/ロケール固定、並列/キャッシュの制御。

### 非スコープ
- 本番運用の環境保護ルール（GitHub 側の環境保護設定はガイドのみ）。

---

## 2. 必須ジョブとゲート
- **DocLint（CR-01）**: FrontMatter/本文の静的検査。**エラー=Fail**。
- **Trace（CR-02）**: FM→Graph 構築。**graph.json 必須**。
- **Indexing（CR-03）**: 検索索引の生成。**meta.json 必須**。

> 追加ゲート（任意で有効化）：Reach（CR-04）、SecScan（CR-09）、IDCheck（CR-07）、I18N（CR-08）、Impact（CR-06）、Audit（CR-05）。

---

## 3. 決定性と10分以内の実行
- **依存固定**: `tools/requirements-ci.txt` にピン留め。`pip install -r` + `actions/cache` を使用。
- **乱数/Seed**: ANN/スコアリングは `SEED=42`、`PYTHONHASHSEED=0` を環境固定。
- **TZ/Locale**: `TZ=UTC`, `LANG=C.UTF-8`。
- **並列**: DocLint/Trace/Indexing/SecScan を **並列実行**。ゲート集約で判定。  
- **差分実行**: 変更ファイルが少ない場合は対象を限定（`paths-filter` を使用可能）。

---

## 4. 出力物
- `artifacts/**` の各レポート（JSON/MD）と、公開用 `public/`（索引/サマリ/最新Graph等）。

---

## 5. CLI・ファイル構成
- ルール: `tools/docops_cli/config/publish_rules.yml`  
- 集約: `tools/ci/aggregate_gate.py`（各レポートを集めて合否判定、Pages サマリ用 JSON を出力）  
- 公開: `tools/ci/make_index.py`（`public/index.html` を生成）

---

## 6. 受入基準（AC）
- **AC-01**: PR→ゲート→公開の総所要が **< 10 分（P95）**。  
- **AC-02**: 同一コミットを再実行しても **同一結果**（決定性）。  
- **AC-03**: 失敗時は **原因カテゴリ**（DocLint/Index/Trace/...）を CI Summary に明示。

---

## 7. CI フロー（概要）
1. **PR**: DocLint/Trace/Indexing/SecScan を並列に実行 → **Gate** が `publish_rules.yml` に従い合否判定。  
2. **main push**: Gate 合格を前提に、`public/` を生成 → **GitHub Pages** に公開。  
3. **監査**: Audit（CR-05）を Nightly で実行（任意）。

---

## 8. Pages 公開
- `actions/configure-pages` + `actions/upload-pages-artifact` + `actions/deploy-pages`。  
- `public/` には **最新の各レポート**と**サマリ**、`graph.json` のダウンロードリンクを含める。

---

## 9. トレース
- **satisfies**: BG-KMK-05（常時公開可能）  
- **depends_on**: CR-01..09  
- **constrains**: CN-KMK-01..03
