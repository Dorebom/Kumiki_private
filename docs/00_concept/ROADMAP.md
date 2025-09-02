---
id: PLAN-KMK-ROADMAP-2025H2
title: Kumiki ロードマップ（2025H2, 2週間スプリント）
type: roadmap
status: draft
version: 0.1.0
created: '2025-09-02'
updated: '2025-09-02'
canonical_parent: CR-KMK-00
tags:
- roadmap
- plan
- sprint
---

# ロードマップ（2週スプリント）

> 目的：**MVPを8週で確定**、その後は検索/スケール/ガバナンスを強化して **v1.0** に到達。

## Sprint 0（準備週）
- **期間**：09-02 〜 09-07
- **目的/範囲**：CIランナー・Secrets・Pages・`mkdocs.yml`・DocLintルールの土台整備
- **対応CR**：CR-10 / CR-11（基盤）, CR-01（ルール雛形）
- **Exit**：`artifacts/metrics/*` 出力、`docs/index.md` 自動再生成が決定的に通る

## スプリント計画
| Sprint | 期間 | 主要テーマ / 到達点 | 対応CR | 主要Artifacts（増分） | Exit（AC/Gate） |
|---|---|---|---|---|---|
| 1 | 09-08 → 09-21 | DocLintとテンプレの**一気通貫（最小）**。FM必須/ID形式/参照チェック開始 | CR-01 / CR-10 / CR-11 | doclint, gate, metrics | Gateで**DocLint重大=0**、CI決定性の初期検証 |
| 2 | 09-22 → 10-05 | **Trace Graph（入口）**可視化、`canonical_parent`一括整備 | CR-02 / CR-07 | trace | **入口到達100%**、`unknown_refs=0` |
| 3 | 10-06 → 10-19 | **セキュリティ検査（Fail-close）**導入、許容リストWORM連携 | CR-09 / CR-05 | secscan, approval | **致命検知=Fail**、例外はWORM台帳必須 |
| 4 | 10-20 → 11-02 | **Gate統合**（DocLint/Trace/SecScan）で**MVP Gate**完成 | CR-10 / CR-11 | gate, metrics | **MVP確定**：PR時CI<10分/決定的、Passのみ公開 |
| 5 | 11-03 → 11-16 | **検索基盤（BM25+ANN）**初版＋評価ループ開始 | CR-03 / CR-11 | search/index, eval | Hit@3の**ベースライン確立** |
| 6 | 11-17 → 11-30 | **ANN差替えIF**と回帰比較、ID重複修復の自動提案 | CR-13 / CR-07 / CR-03 | search/manifest, dup-report | 劣化≤3pt、重複再現率≥0.99 |
| 7 | 12-01 → 12-14 | **往復到達テスト**・**多言語整合**導入 | CR-04 / CR-08 | trace（逆到達）, i18n-diff | **重要ノード往復100%**、対訳誤検知≤5% |
| 8 | 12-15 → 12-28 | **スケール試験（300→1k）**、LLM差分採用率トラッキング、v1.0準備 | CR-14 / CR-12 / CR-11 / CR-10 | scale-report, patch-stats | 1kで**CI<60分(nightly)**、採用率≥60% |

## 品質・受入（共通）
- DocLint：`major+critical=0`／Trace：`unknown_refs=0`（Sprint7以降は**往復100%**）
- SecScan：`critical=0`（例外はWORM台帳）／Gate：Passのみ公開
- Metrics：`metrics.jsonl` 欠測0／決定性：再実行で同一結果

## BG/HLF 接続
- HLF-01（パイプライン）→ Sprint1–4、HLF-03/08（検索/スケール）→ Sprint5–8、HLF-06（ガバナンス）→ Sprint3–4/6
- BGはスプリントごとにKPI更新をArtifactsで確認（KPI-QLT-01/OPS-01/SRC-01/SEC-01/OBS-01/SCL-01）
