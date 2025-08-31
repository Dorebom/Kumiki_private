---
id: CR-KMK-11
title: "CR-11: 可観測性（メトリクス/ログ/アーティファクト）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr11, observability, metrics, logs, artifacts, worm]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04","CR-KMK-05","CR-KMK-06","CR-KMK-07","CR-KMK-08","CR-KMK-09","CR-KMK-10"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-11: 可観測性（メトリクス/ログ/アーティファクト）— 詳細仕様

> **G**: すべての検査（CR-01..10）に **構造化メトリクス** を付与し、履歴を **Artifacts/WORM** に保全する。  
> **AC**: **欠測0**、**長期保存 ≥ 180日**。

---

## 1. 方針
- **メトリクス先行**: 小さく安定した**低カーディナリティ**のメトリクス（Counter/Gauge/Timing/Histogram）を第一級に。  
- **決定的**: 同一入力で**同一メトリクス**（乱数/時刻依存を排除 or 明示フィールド化）。  
- **経路**: PR/Push の各実行で `artifacts/metrics/<run>/` に保存 → GitHub Pages の `public/metrics/` に公開 → **WORM台帳（CR-05）** に追記。

---

## 2. 名前付け・単位・ラベル
- **命名**: `kumiki.<component>.<metric>`（例: `kumiki.doclint.files_total`）。  
- **単位接尾辞**: `_count`, `_ms`, `_bytes`, `_ratio`。  
- **ラベル（固定キーのみ）**: `repo, branch, sha, run_id, workflow, job, cr_id, status, locale`。**任意キーの持ち込み禁止**。  
- **時間**: 実測は `*_ms`、時刻は `ts_utc`（ISO8601）。

---

## 3. コンポーネント別メトリクス（必須）
- **CR-01 DocLint**: `files_total_count`, `errors_count`, `warnings_count`, `duration_ms`.  
- **CR-02 Trace**: `nodes_total_count`, `edges_total_count`, `cycles_count`, `isolates_count`, `duration_ms`.  
- **CR-03 Search/Index**: `docs_indexed_count`, `index_time_ms`, `query_p95_ms`, `eval_mrr`, `eval_ndcg`.  
- **CR-04 Reach**: `evaluated_count`, `roundtrip_ok_count`, `roundtrip_rate_ratio`, `duration_ms`.  
- **CR-05 Audit(WORM)**: `events_appended_count`, `verify_fail_count`, `duration_ms`.  
- **CR-06 Impact**: `changed_files_count`, `candidates_count`, `suggestions_count`, `duration_ms`.  
- **CR-07 IDCheck**: `ids_count`, `duplicates_count`, `broken_refs_count`, `gaps_count`, `duration_ms`.  
- **CR-08 I18N**: `pairs_count`, `missing_count`, `id_mismatch_count`, `relation_diff_count`, `duration_ms`.  
- **CR-09 SecScan**: `findings_count`, `high_count`, `medium_count`, `low_count`, `duration_ms`.  
- **CR-10 Gate/Publish**: `gate_ok_count`（0/1）, `total_ci_time_ms`, `determinism_checksum`（hex）。

> すべての**必須メトリクス**は `metrics_summary.json` に存在しなければならない（**欠測0**）。

---

## 4. 出力物
```
artifacts/metrics/<run>/
  ├─ metrics.jsonl          # 1行1イベント（NDJSON, schema: metrics_event.json）
  ├─ metrics_summary.json   # 集約/必須メトリクス（schema: metrics_summary.json）
  ├─ metrics_timeseries.csv # 主要メトリクスの縦持ちテーブル
  └─ logs.jsonl             # 付随ログ（schema: log_event.json）
public/metrics/<timestamp>-<run_id>/  # Pages にコピー（CR-10 公開フロー経由）
```

---

## 5. ログ（最小限の構造化）
- `level` は `INFO|WARN|ERROR`、`component` は `doclint|trace|...|gate|publish|obs`。  
- `message` は人間可読。`data` に詳細（ID/件数/しきい値・判定）。

---

## 6. 欠測の扱い
- 集約器（`metrics_collect.py`）は、各 CR のレポートから**必須キー**を収集し、欠落時は `missing: ["..."]` を列挙して **CI Fail**。

---

## 7. 長期保存（≥180日）
- **WORM 連携（CR-05）**: `audit append` で `artifacts/metrics/<run>/metrics_summary.json` をハッシュ対象に含め、**不可変追記**。  
- **Pages 永続**: `public/metrics/<timestamp>-<run_id>/` に**世代別**で配置（上書き不可）。  
- **月次スナップショット**（任意）: Release `metrics-YYYY-MM.zip` として公開資産に固着。

---

## 8. CLI / CI 連携
- 収集: `python tools/ci/metrics_collect.py --rules tools/docops_cli/config/obs_rules.yml --out artifacts/metrics`  
- 公開: `python tools/ci/metrics_publish.py`（`public/metrics/**` へコピー）  
- CR-10 の `gate` 後に `obs` ジョブを追加し、Pages 公開および WORM 追記を実施。

---

## 9. 受入基準（AC）
- **AC-01**: `metrics_summary.json` の**必須メトリクス欠測0**で CI Pass、欠測時は Fail。  
- **AC-02**: `public/metrics/**` と WORM 台帳の両方に**ランごとの記録**が存在（直近 180 日分）。

---

## 10. トレース
- **satisfies**: BG-KMK-01（工数削減・品質可視化）, BG-KMK-05（常時公開可能）  
- **depends_on**: CR-05, CR-10  
- **constrains**: CN-KMK-01..03
