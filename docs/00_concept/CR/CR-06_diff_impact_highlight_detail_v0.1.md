---
id: CR-KMK-06
title: "CR-06: 変更差分→影響ハイライト（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr06, impact, diff, highlight]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-06: 変更差分→影響ハイライト（詳細仕様）

> **G**: PR の差分から **上流 / 下流 / 横断** 影響を自動提示する。  
> **O**: 影響レポート（JSON/Markdown）、根拠特徴量、FM 追記/修正の **パッチ**（任意）、該当文書の **見出し＋抜粋ハイライト**。  
> **AC**: 既知ケースの **ヒット率 ≥ 0.9、誤通知 ≤ 0.1**。

---

## 1. 用語
- **影響（Impact）**: 変更により、リンク／依存／近接関係から更新・レビューが必要になる可能性。  
- **上流/下流/横断**:  
  - **上流**: `FR/NFR/TEST/TRACE/DD` → `HLF/RS` 方向（要求側）。  
  - **下流**: `RS/HLF` → `FR/NFR/DD/TEST/TRACE` 方向（実装/検証側）。  
  - **横断**: `depends_on / integrates_with` など横方向、またはタグ・同義語・ファイル近接での関連。  
- **差分（Diff）**: `git diff --unified=0` の hunk 単位（追加/削除/変更）を基本とする。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- PR 差分の解析、Graph（CR-02）・検索（CR-03）との連携、影響候補のスコアリング、ハイライト生成、パッチ提案。

### 2.2 非スコープ（CR-06段階）
- 自動マージ/自動修正の実施（提案のみ）。

---

## 3. 入出力
### 3.1 入力
- PR の差分: `git diff`（範囲 `--merge-base origin/main HEAD` を既定）  
- Graph JSON: `artifacts/trace/<run>/graph.json`（CR-02）  
- 検索インデックス: `artifacts/search/<run>/...`（CR-03; 任意で類似箇所抽出に使用）  
- ルール: `tools/docops_cli/config/impact_rules.yml`

### 3.2 出力
- `artifacts/impact/<run>/report.json|md`（影響候補・方向・スコア・根拠）  
- `artifacts/impact/<run>/patches/*.patch`（FM 追記/修正提案; 任意）  
- `artifacts/impact/<run>/snippets/`（ハイライト抜粋: HTML/MD）

---

## 4. 影響判定モデル（特徴量）
### 4.1 グラフ系（CR-02 由来）
- **距離（graph_dist）**: 変更ノードから対象ノードまでの最短距離（有向/無向の切替は relation 毎）。  
- **関係タイプ重み（edge_weight）**: `satisfies/refines/depends_on/integrates_with/constrains` 毎に重み。  
- **方向（direction）**: `upstream | downstream | lateral` の別。

### 4.2 差分系
- **変更規模（delta_size）**: 追加/削除行数、変更箇所（見出し/表/本文/FrontMatter）。  
- **セクション一致（section_overlap）**: 対象ノード側の **該当見出し** に近い差分であれば加点。

### 4.3 類似度系（任意）
- **語彙一致（lex_overlap）**: BM25 上位スニペットのオーバーラップ。  
- **埋め込み類似（ann_sim）**: 変更文と対象文のコサイン類似（CR-03 の ANN 使い回し）。

### 4.4 共変量（補助）
- **履歴共変更（cochange_rate）**: git 履歴での同時変更率。  
- **タグ一致（tag_match）**: `tags` 共有で加点。

### 4.5 スコア式（既定・決定的）
```
impact = 0.35*graph_dist_w + 0.20*edge_weight + 0.15*delta_size +
          0.10*section_overlap + 0.10*lex_overlap + 0.05*ann_sim +
          0.05*cochange_rate
```
- `graph_dist_w = max(0, 1 - dist/3)`（距離 0→1、1→0.67、2→0.33、3以上→0）  
- しきい値: `threshold=0.65`、強推奨 `strong_threshold=0.80`。

---

## 5. ハイライト生成
- 対象ノード文書の **該当見出しブロック** を抽出（見出しから次見出し直前まで）。  
- マッチ語・ID・差分に由来するキーフレーズを **<mark>** で強調（MD/HTML両対応）。  
- 最大 2 スニペット、各 120 文字（サロゲートペア、全角半角を壊さない）。

---

## 6. 提案パッチ（任意）
- 欠落している `satisfies / refines / depends_on` を **FrontMatter** へ追記提案（unified diff）。  
- `conflicts_with / constrains` の明文化提案。  
- 重複/循環を避けるため CR-02 の正規化を再利用。

---

## 7. ルール/コード（IM*）
- **IM010**: 影響候補（threshold 以上）。  
- **IM011**: 強推奨候補（strong_threshold 以上）。  
- **IM020**: 断リンク検出に伴う修復提案。  
- **IM030**: FM 追記提案を生成。  
- **IM040**: ハイライト抽出失敗（見出し不正）。

---

## 8. CLI I/F（案）
```bash
# 影響分析（PR内の変更差分から）
docops impact analyze   --rules tools/docops_cli/config/impact_rules.yml   --graph artifacts/trace/<run>/graph.json   --search artifacts/search/<run>   --diff-range "origin/main...HEAD"   --out artifacts/impact --format json,md --emit-snippets

# パッチ生成（任意）
docops impact suggest   --rules tools/docops_cli/config/impact_rules.yml   --graph artifacts/trace/<run>/graph.json   --out artifacts/impact/patches
```

---

## 9. 受入基準（AC）
- **AC-01**: ゴールドセットに対する **ヒット率 ≥ 0.9、誤通知 ≤ 0.1**。  
- **AC-02**: 提案パッチが **決定的**（同一入力で同一 diff）。  
- **AC-03**: 1,000 ファイルで **≤ 90s**（Impact 分のみ）。

---

## 10. 設定（impact_rules.yml 概要）
- 閾値/強閾値、relation ごとの重み、最大探索深さ、履歴参照の期間、BM25/ANN 利用可否、スニペット長。

---

## 11. CI（最小例）
```yaml
name: docops_impact
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_impact.yml'
jobs:
  impact:
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
          pip install pyyaml numpy scikit-learn networkx
      - name: Build Graph (if not exists) & Analyze Impact
        run: |
          python tools/docops_cli/trace.py build             --rules tools/docops_cli/config/trace_rules.yml             --out artifacts/trace --format json
          python tools/docops_cli/impact.py analyze             --rules tools/docops_cli/config/impact_rules.yml             --graph artifacts/trace/graph.json             --diff-range "origin/main...HEAD"             --out artifacts/impact --format json,md --emit-snippets
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-impact-artifacts
          path: artifacts/impact
```

---

## 12. トレース
- **satisfies**: BG-KMK-01（工数削減）, BG-KMK-02（トレース品質）, BG-KMK-05（常時公開可能）  
- **depends_on**: CR-02（Graph）, CR-03（検索）  
- **constrains**: CN-KMK-01..03

---

## 付録A: スコア例（features）
```json
{
  "direction": "downstream",
  "graph_dist_w": 0.67,
  "edge_weight": 0.90,
  "delta_size": 0.40,
  "section_overlap": 0.10,
  "lex_overlap": 0.22,
  "ann_sim": 0.18,
  "cochange_rate": 0.15,
  "impact": 0.78
}
```

## 付録B: ハイライト例（MD）
```
### 3.2 ローテーションポリシー
... 現在の<mark>ローテーション周期</mark>を 90→60日に変更 ...
```
