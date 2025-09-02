---
id: CR-KMK-03
title: "CR-03: ハイブリッド検索（BM25+ANN）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr03, search, bm25, ann]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-03","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","STD-KMK-FM-01","STD-KMK-ID-01"]
integrates_with: ["STD-OBSIDIAN-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-03: ハイブリッド検索（BM25+ANN）— 詳細仕様

> **目的**: 日本語/英語混在の Markdown 群に対して、**Lexical（BM25）× Semantic（ANN）** のハイブリッド検索を提供し、
> JP クエリでも**高い再現率と適合率**を実現する。結果はサイト内検索および CI の評価で用いる。

---

## 1. 用語
- **BM25**: 逆文書頻度に基づくスコアリング。フィールド別ブースト（title/heading/tags）。
- **ANN**: 埋め込みの近傍探索（FAISS/ScaNN/Annoy 等）。類似度は **cosine** を既定。
- **ハイブリッド再ランク**: Lexical/ANN の候補を集合化し、特徴量の線形結合または WRR で再ランク。
- **JP 形態素**: Sudachi/KUROMOJI を想定。未知語は **2–3gram** で補完。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- トークナイズ/正規化、索引生成、候補集合化、再ランク、ハイライト、評価用ベンチの一式。

### 2.2 非スコープ（CR-03段階）
- LLM 質問応答（RAG）本体。  
- ベクトル DB のマネージド運用（自前インデックス想定; 切替IFは用意）。

---

## 3. 入出力
### 3.1 入力
- `docs/**/*.md`（`.obsidian/` 除外）。
- ルール/辞書: `tools/docops_cli/config/search_rules.yml`, `synonyms_ja_en.yml`, `normalize_ja.yml`。

### 3.2 出力
- `artifacts/search/<run>/bm25_index/`（倒立インデックス）。
- `artifacts/search/<run>/ann_index/`（埋め込みインデックス）。
- `artifacts/search/<run>/meta.json`（インデックスメタ）。
- `artifacts/search/<run>/eval_report.(json|md)`（評価結果）。

---

## 4. 機能要求（FR-03.x）
### FR-03.1 正規化・トークナイズ
- **正規化**: 大小/全半/記号/約物を統一。旧字体→新字体のマップ、ダッシュ/波ダッシュの揺れ統合。  
- **JP 形態素**: Sudachi **A**（細分）を既定、**B** を選択可。固有名詞/未知語は **2–3gram** で補完。  
- **EN**: Lowercase + Unicode NFKC + simple stem（porter 任意）。

### FR-03.2 フィールド設計
- **索引フィールド**: `title`, `headings`, `body`, `tags`, `id`。  
- **ブースト**: `title:3.0`, `headings:1.6`, `tags:1.4`, `id:2.0`, `body:1.0`（既定）。

### FR-03.3 候補生成（Lexical/ANN）
- BM25: `top_k_lex = 200`。  
- ANN: `top_k_ann = 200`（cosine）。  
- 集合化: 和集合（最大 400）。重複は特徴量を併合。

### FR-03.4 再ランク（線形結合・既定）
- **特徴量**: `bm25_norm, ann_sim, phrase_bonus, proximity, field_boost, graph_hint`。  
- **スコア式（既定）**:  
  `final = 0.50*bm25_norm + 0.35*ann_sim + 0.05*phrase_bonus + 0.05*proximity + 0.03*field_boost + 0.02*graph_hint`  
  - `bm25_norm`: 候補集合内の MinMax 正規化。  
  - `phrase_bonus`: 完全句一致 +0.05（上限）。  
  - `proximity`: ターム近接度（ウィンドウ 8 語内なら +0.05 上限）。  
  - `graph_hint`: CR-02 の Graph で **satisfies/refines** が近傍にある場合 +0.02 上限。

### FR-03.5 WRR（代替再ランク）
- **Weighted Reciprocal Rank**: `score = α/(rank_bm25+β) + (1-α)/(rank_ann+β)`（既定 `α=0.55, β=1`）。

### FR-03.6 ハイライト
- マッチ範囲を最大 2 箇所、前後各 80 文字。`…` で省略。JP のサロゲートペアを壊さない。

### FR-03.7 同義語/エイリアス
- `synonyms_ja_en.yml` を展開。「拡張容易性 ≈ Extensibility」「監査 ≈ Audit」「誤検知 ≈ False Positive」等。

### FR-03.8 多言語クエリ処理
- JP/EN の言語推定（文字種/比率）。言語別パイプラインを自動選択。ローマ字→かなの簡易変換は任意。

### FR-03.9 評価
- 指標: **Top1/Top3/Top10**, **MRR@10**, **nDCG@10**, **JP Precision/Recall/F1**。  
- データ: `eval/queries.yaml`（≥30件; JP/EN 混在; 期待 ID 群）。

### FR-03.10 性能
- 1,000 ファイルで **索引生成 ≤ 120s**、クエリ **P95 ≤ 120ms**（ローカル想定）。  
- 10,000 ファイルで nightly **≤ 20min**。

---

## 5. 受入基準（AC）
- **AC-01**: JP クエリ Top3 再現率 **≥ 0.85**、F1 **≥ 0.88**。  
- **AC-02**: MRR@10 **≥ 0.80**、nDCG@10 **≥ 0.85**。  
- **AC-03**: 再ランクが**決定的**（シード/正規化で安定）。  
- **AC-04**: 上記性能目標を満たす。

---

## 6. CLI I/F（案）
```bash
# 索引生成
docops search index   --rules tools/docops_cli/config/search_rules.yml   --out artifacts/search

# 検索（対話）
docops search query --q "日本語 検索 形態素 n-gram"   --rules tools/docops_cli/config/search_rules.yml   --out artifacts/search

# 評価（ベンチ）
docops search eval   --rules tools/docops_cli/config/search_rules.yml   --queries eval/queries.yaml   --out artifacts/search/eval_report.json --format json,md
```

---

## 7. 設定（search_rules.yml 概要）
- トークナイザ/正規化/ストップワード、BM25 パラメータ（k1,b）、ANN エンジン/次元、ハイブリッド重み。

---

## 8. トレース
- **satisfies**: BG-KMK-03（JP/EN 検索品質）, BG-KMK-05（常時公開可能）  
- **depends_on**: CR-01, CR-02（FM/Graph の前提）  
- **constrains**: CN-KMK-01..03（FM/固定語彙/CI 前提）

---

## 付録A: 正規化規則（抜粋）
- 全角英数→半角、`〜`/`～`→`~`、`／`→`/`、`・`→空白、`—`/`–`→`-`。  
- 旧字体→新字体（例: `髙`→`高`）。  
- 記号をトークン境界にする（アンダースコアは保持）。

## 付録B: スコア特徴量（例）
```json
{
  "bm25_norm": 0.72,
  "ann_sim": 0.83,
  "phrase_bonus": 0.03,
  "proximity": 0.04,
  "field_boost": 0.02,
  "graph_hint": 0.01
}
```

## 付録C: 評価レポート JSON（スキーマ）
`tools/docops_cli/schemas/search_eval_report.json` を参照。
