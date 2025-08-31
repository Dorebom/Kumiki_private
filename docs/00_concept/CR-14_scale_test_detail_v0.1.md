---
id: CR-KMK-14
title: "CR-14: スケール試験（300→1k）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr14, scale, performance, quality]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-03","CR-KMK-06","CR-KMK-09","CR-KMK-10","CR-KMK-11","CR-KMK-12","CR-KMK-13"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-14: スケール試験（300→1k）— 詳細仕様

> **G**: 文書数増加時の **CI 時間増分** と **品質** を測定し、**ボトルネック**を提示する。  
> **AC**: **1k で CI < 60 分（nightly）**、**重大違反 0**。

---

## 1. 目的
- 既存の DocOps パイプライン（CR-01..13）の**スケーラビリティ**を 300 → 600 → 1000 ドキュメントで検証し、  
  時間（P95）・品質指標（DocLint/SecScan/Trace/Search）を**定量化**、改善対象を**特定**する。

---

## 2. 評価軸
### 2.1 時間（必須）
- **CI 総時間**（wall clock）
- コンポーネント別：DocLint / Trace / Index / SecScan / Gate / Publish / AI Patch（任意）

### 2.2 品質（必須）
- **重大違反（Critical）**：SecScan `high`、DocLint `errors`、Trace `cycles`、IDCheck `duplicates/broken_refs`。  
- **検索品質**：Hit@3 / MRR（CR-03/13 の eval を 100 サンプルで）。

### 2.3 ボトルネック抽出
- **線形近似の傾き** `s = d(time)/d(#docs)` と **寄与率**（割合）で上位3要因を報告。

---

## 3. 入出力
### 入力
- `tools/docops_cli/config/scale_rules.yml`（サイズ配列、許容時間、品質閾値、生成種別）。

### 出力（run ごと）
- `artifacts/scale/<run>/scale_report.json|md`（schema: `scale_report.json`）  
- `artifacts/scale/<run>/timeseries.csv`（size, component, time_ms, violations, metrics）  
- `public/scale/<run>/index.html`（CR-10 Pages で公開）

---

## 4. 手順
1. **データ生成**（決定的）: `seed_docs.py` が `N ∈ {300,600,1000}` の**合成ドキュメント**を生成。  
   - FM（id/title/type/status/tags/...）を付与、参照グラフを**小世界**で生成（断リンク0）。  
   - ja/en を 1:1 で作成（I18N 対訳ペア完全）。
2. **パイプライン実行**: DocLint → Trace → Index → SecScan → Gate（CR-10 の実装／互換 I/F を呼ぶ）。  
3. **検索品質評価**: ランダム 100 クエリで Hit@3 / MRR を測定（CR-13 の `ann_benchmark` 相当関数）。
4. **集計**: 実行時間を計測・保存。品質指標と合わせて `scale_report.json` を生成。  
5. **ボトルネック解析**: size vs time を線形回帰し、傾きの大きい順に上位3件を `bottlenecks[]` として提示。

---

## 5. 受入基準（AC）
- **AC-01（時間）**: `size=1000` で `ci_wall_clock_min < 60`（nightly ラン）。  
- **AC-02（品質）**: 重大違反 = 0（`secscan.high=0` & `doclint.errors=0` & `trace.cycles=0` & `idcheck.duplicates/broken_refs=0`）。  
- **AC-03（報告）**: `scale_report.json` に **times**/**quality**/**bottlenecks** が全て記録（欠測0）。

---

## 6. 可観測性（CR-11）
- 各サイズごとに `kumiki.scale.ci_time_ms`, `doclint_time_ms`, `trace_time_ms`, `index_time_ms`, `secscan_time_ms`,  
  `search_hit3_ratio`, `search_mrr`, `violations_critical_count` を発行し、Pages/WORM 保全。

---

## 7. CI（nightly）
- `.github/workflows/docops_scale_test.yml` を **毎日 15:00 UTC（= 0:00 JST）** に起動。  
- ラン内で 300→600→1000 を**順次**実行し、`scale_report.json` をまとめてアップロード・公開。

---

## 8. ボトルネック改善の指針（出力に含める）
- **I/O**：ファイル走査を差分化、`glob` の並列化。  
- **Index**：分割シャーディング（例：8 シャード）＋マージ。  
- **Trace**：ID辞書の永続キャッシュ（pickle/SQLite）。  
- **SecScan**：拡張子ベースのプリフィルタ＋高コスト規則の遅延適用。

---

## 9. トレース
- **satisfies**: BG-KMK-02（性能/品質見える化）, BG-KMK-05（常時公開可能）  
- **depends_on**: CR-03, CR-09, CR-10, CR-11, CR-13  
- **constrains**: CN-KMK-01..03
