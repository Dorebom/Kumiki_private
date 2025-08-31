---
id: CR-KMK-00
title: "Kumiki 概念要件（再提案・従来CRスタイル準拠） v0.2"
type: concept_requirements
status: draft
version: 0.2.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, preferred_style]
canonical_parent: ""
refines: []
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-03","BG-KMK-04","BG-KMK-05"]
depends_on: ["STD-KMK-FM-01","STD-KMK-ID-01"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: ["CR-KMK-00@v0.1"]
---

# Kumiki 概念要件（Concept Requirements）— 従来CRスタイル準拠

> **G / I / O（全体）**  
> **Goal**: DocOps（生成→紐付け→検証→公開）を**機械可読**に一貫化し、品質を落とさず工数を半減。  
> **Input**: FrontMatter付きMarkdown群、語彙YAML、DocOps CLI、評価用検索クエリ集合、CI設定。  
> **Output**: 雛形群、DocLintレポート、Graph/Trace成果物、BM25+ANN検索結果、公開サイト、監査台帳。

---

## 1. 背景と目的
- 多数の要求・設計・試験文書を**安定ID**と**フラットFrontMatter**で管理し、**入口トレース**を常時維持。
- 日本語を含む文書で**検索性（Recall/Precision）**を確保し、レビュー・引き当ての**往復トレース**を自動化。
- 生成AIは**差分パッチ**で提案し、ヒューマンレビューに馴染むワークフローへ統合。

---

## 2. ペルソナ / ユースケース（抜粋）
- **PM/PL**: マイルストーン前に**トレース欠落ゼロ**を確認。  
- **設計者**: 仕様変更→**影響範囲**と**更新候補**を即時提示。  
- **QA/TE**: 仕様→試験→結果の**往復参照**と**差分到達**の自動検査。  
- **DocOps**: CIで**DocLint/Indexing/Trace**をゲート化、公開まで自動。

---

## 3. 概念レベル CR（CR-01…15）
> それぞれ **G/I/O** と **受入基準（AC）** を最小記述。詳細は RS/HLF/FR/NFR/CN へ展開。

### CR-01: テンプレート自動展開とDocLint
- **G**: RS/HLF/FR/NFR/CN/ADR/TRACEの雛形展開と**規約準拠**のチェックを自動化。  
- **I**: 語彙YAML、テンプレ群（FM必須キー、固定語彙）、対象ディレクトリ。  
- **O**: 展開ログ、DocLintレポート（欠落/重複/語彙違反/リンク切れ）。  
- **AC**: 1,000ファイルでDocLint重大違反0件（テンプレからの初回生成時）。

### CR-02: FM→Graph→入口トレース
- **G**: `refines / satisfies / depends_on / integrates_with / constrains / conflicts_with / supersedes` をグラフ化。  
- **I**: FrontMatter（フラット1段）、語彙YAML。  
- **O**: DOT/JSONのGraph、到達性・差分レポート。  
- **AC**: 既知リンク集合に対し再現率≥0.95、誤陽性≤0.05。

### CR-03: ハイブリッド検索（BM25+ANN）
- **G**: **日本語形態素×n-gram**のハイブリッド索引でJP/EN混在検索を高精度化。  
- **I**: 文書群、クエリセット（≥50）。  
- **O**: 検索インデックス、Top@k結果、根拠抜粋。  
- **AC**: JPクエリTop3再現率≥0.85、F1≥0.88。

### CR-04: 往復トレース到達テスト
- **G**: RS↔HLF↔FR/NFR↔CN↔DD↔TEST↔TRACE の**往復到達**を自動検証。  
- **O**: 不到達ノード/リンクの一覧、修正候補。  
- **AC**: 重要ノードに対し往復到達100%。

### CR-05: 監査台帳（WORM風）
- **G**: 生成・改版・承認・公開の**不可変ログ**を保全。  
- **O**: 署名/ハッシュ付きイベント、エビデンスURI。  
- **AC**: 欠落0、改竄検知100%。

### CR-06: 変更差分→影響ハイライト
- **G**: PRの差分から**上流/下流/横断**影響を自動提示。  
- **AC**: 既知ケースのヒット率≥0.9、誤通知≤0.1。

### CR-07: ID整合と重複検出/修復案
- **G**: **安定ID**の重複/欠番/断リンクを検出し**自動修復案**を提示。  
- **AC**: 重複検出再現率≥0.99、誤修復≤0.5%。

### CR-08: 多言語対訳整合
- **G**: `docs/ja` と `docs/en` の**ID同等性**・参照整合を検査。  
- **AC**: 差異の機械抽出100%、誤検知≤5%。

### CR-09: セキュリティ/機密情報ブロック
- **G**: PII/秘密情報を**検知してPRをFail**、公開事故を防止。  
- **AC**: 既知パターン検知100%、誤検知≤2%。

### CR-10: CIゲート & 公開フロー
- **G**: PRで DocLint/Indexing/Trace を実行し、合格時のみ**公開**。  
- **AC**: CI合計<10分、再実行で決定的（非フレーク）。

### CR-11: 可観測性（メトリクス/ログ/アーティファクト）
- **G**: すべての検査に**構造化メトリクス**を付与し、履歴を**Artifacts/WORM**へ保全。  
- **AC**: 欠測0、長期保存≥180日。

### CR-12: 生成AI差分パッチ提案
- **G**: LLM出力は**unified diff**で提示、PRレビューに直結。  
- **AC**: 採用率≥60%、NG再発≤5%/週。

### CR-13: Embedding/ANNコネクタの差替え
- **G**: ベンダーロックイン回避。IF固定で**FAISS/ScaNN/Annoy**等へ差替え可能。  
- **AC**: 差替え後もTop3率劣化≤3pt。

### CR-14: スケール試験（300→1k）
- **G**: 文書数増加時の**CI時間増分**と**品質**を測定しボトルネックを提示。  
- **AC**: 1kでCI<60分（nightly）、重大違反0。

### CR-15: 承認フローと自動マージ禁止条件
- **G**: クリティカル変更で**手動承認**を必須化し、自動マージを抑止。  
- **AC**: ルール逸脱0、運用監査で指摘0。

---

## 4. 制約（CN）
- **CN-KMK-01**: FrontMatterは**フラット1段**、Obsidian表示と整合。  
- **CN-KMK-02**: 関係語彙は固定（`refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes`）、配列は**文字列IDのみ**。  
- **CN-KMK-03**: 標準CIは**GitHub Actions**、静的公開は**GitHub Pages**を前提。

---

## 5. 成功指標（KPI/KSF）
- 初回DocLint合格率≥85%（テンプレ利用時）。  
- 既知50クエリTop3率≥85%、JP検索満足度≥4.2/5。  
- 往復トレース到達100%。  
- PR→公開リードタイム50%削減。

---

## 6. 検証用ミニプロジェクト（推奨）
- **目的**: 上記CR-01..15を**小規模プロダクト**で通し検証（CI上で再現可能）。  
- **構成**: Edge Agent（シミュレータ）/ Cloud API（FastAPI+SQLite）/ （任意）UI。  
- **効果**: DocOpsゲート、Graph/Trace、検索、監査の**実データ**運用での妥当性確認。

---

## 7. ロードマップ（MVP→v1.0）
- **Phase 0（2週）**: 語彙YAML/テンプレ/ID体系/DocLintルール確定。  
- **Phase 1（4–6週）**: CR-01..07のMVP実装、CIゲート、公開。  
- **Phase 2（3–4週）**: JP検索強化・往復トレース・AI差分。  
- **Phase 3（2–3週）**: 可観測性・監査・スケール試験・承認フロー。

---

## 8. 入口トレース（初期）
- 本CR（CR-KMK-00）は **BG-KMK-01..05** をsatisfies、**CN-KMK-01..03**をconstrains。  
- RS/HLF/FR/NFR/CN 分割後、各章へ `refines/satisfies/depends_on` を配布する。

