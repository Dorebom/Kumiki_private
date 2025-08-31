---
id: CR-KMK-02
title: "CR-02: FM→Graph→入口トレース（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr02, graph, trace]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["STD-KMK-FM-01","STD-KMK-ID-01","CR-KMK-01"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-02: FM→Graph→入口トレース（詳細仕様）

> **目的**: FrontMatter の関係語彙（refines/satisfies/depends_on/…）から **知識グラフ**を構築し、
> **往復到達**の検証と**入口トレース（不足リンク候補）**の自動提案を行う。結果は PR でゲートする。

---

## 1. 用語
- **入口トレース**: 文書間の上流/下流/横断リンクの「**最初の紐付け**」を指す。FM の該当配列に入る候補リンク群。
- **関係語彙**: `refines / satisfies / depends_on / integrates_with / constrains / conflicts_with / supersedes`（固定）。
- **ノード種別**: `CR, RS, HLF, FR, NFR, CN, ADR, TRACE, DD, TEST` 等の **ID 接頭辞**で判定（拡張可）。
- **往復到達**: ある要求から設計/試験を経て要求へ戻る「**往復経路**」が存在すること。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- Graph 構築（FM→Graph）、到達性解析、循環/孤立検知、入口トレース候補生成、パッチ出力。
- 生成物: DOT/JSON、レポート（MD/JSON）、パッチ（unified diff）。

### 2.2 非スコープ（CR-02段階）
- Embedding ベースの意味リンク生成（CR-03で拡張）。
- 外部システム（Jira/Confluence）同期。

---

## 3. 入出力
### 3.1 入力
- `docs/**/*.md`（`.obsidian/` を除外）。
- ルール: `tools/docops_cli/config/trace_rules.yml`。

### 3.2 出力
- `artifacts/trace/<run>/graph.json`（Graph JSON; schema v1）。
- `artifacts/trace/<run>/graph.dot`（可視化用 DOT）。
- `artifacts/trace/<run>/report.json`（検査・候補詳細）。
- `artifacts/trace/<run>/report.md`（人間可読レポート）。
- `artifacts/trace/<run>/patches/*.patch`（FM 追記提案）。

---

## 4. データモデル（Graph v1）
### 4.1 ノード
- **キー**: `id`（安定 ID; 例: `FR-M5NF-01`）, `kind`（接頭辞から推定）, `title`, `path`, `tags`。

### 4.2 エッジ
- **型**: `refines|satisfies|depends_on|integrates_with|constrains|conflicts_with|supersedes`。  
- **性質**: 既定は **有向**。`integrates_with` のみ **無向** として扱えるオプションを提供（設定で選択）。  
- **属性**: `source`, `target`, `e_type`, `evidence`（根拠: FM/本文/見出し）, `confidence`（0..1）。

---

## 5. アルゴリズム
### 5.1 FrontMatter 解析
1. 各 Markdown を走査し YAML FrontMatter を抽出。  
2. 必須キー/型/固定語彙は CR-01（DocLint）に委譲するが、本機能でも **寛容パース**で継続。  
3. ノード `id/kind/title/path/tags` を登録。FM の関係配列から **既存エッジ**を生成。

### 5.2 入口トレース候補生成（多段）
```
優先度: ①厳密ID一致 > ②見出し/本文のID様式一致 > ③語彙エイリアス > ④近接/構造ヒューリスティクス
```
- **R1: 厳密一致**: 本文/表/コードブロック内の **ID 文字列**（正規表現）を抽出 → エッジ候補。  
- **R2: タイプ整合**: ノード種別に応じて妥当な関係のみ提案（例: `FR`→`RS` に `satisfies` を優先）。  
- **R3: 見出し近接**: 「関連HLF/関連NFR/Related/References」等の見出し直下の ID は **重み+0.2**。  
- **R4: 語彙/別名**: `_vocabulary.yml` の **エイリアス**（例: "高位設計"→HLF）とマッピング。  
- **R5: 構造近接**: 同フォルダ/同シリーズ（例: `FR-12` と `FR-12.x`）に **+0.1**。  
- **R6: 断リンク救済**: 既存 FM の参照が不在なら、同名タイトル/同義タグから候補を提示。

**スコア**: `score = 0.6*exact_id + 0.2*heading_hint + 0.1*structure_prox + 0.1*alias_hint`（0..1）  
**しきい値**: 0.65 以上を提案、0.8 以上は **強推奨** に分類（設定で変更可）。

### 5.3 到達性/循環/孤立
- **往復**: `RS → HLF → FR/NFR → TEST/TRACE → RS` の最短往復経路を探索（BFS/多層制約）。  
- **循環**: `refines/satisfies` 閉路を検出（強連結成分; SCC）。  
- **孤立**: 重要ノード種（`RS/HLF/FR/NFR/CN`）で **入出次数=0** を警告。

### 5.4 パッチ生成
- 候補がしきい値超過のものについて、FrontMatter の対象配列に **非破壊追記**の unified diff を生成。  
- 既存値と重複しないよう正規化（ソート/重複除去）。

---

## 6. ルール/コード体系
- **TR001**: FM からの既存リンク（正常）。
- **TR010**: 入口候補（score ≥ threshold）。
- **TR011**: 強推奨候補（score ≥ strong_threshold）。
- **TR020**: 断リンク（参照先不在）。
- **TR030**: 閉路検出（refines/satisfies）。
- **TR040**: 孤立ノード（重要種）。
- **TR050**: 往復未到達（指定集合）。

---

## 7. CLI I/F（案）
```bash
# Graph 構築＋検査＋候補提示
docops trace build   --rules tools/docops_cli/config/trace_rules.yml   --out artifacts/trace --format json,md --emit-dot

# 候補をFMパッチとして出力
docops trace suggest   --rules tools/docops_cli/config/trace_rules.yml   --out artifacts/trace --threshold 0.65 --strong-threshold 0.8
```

---

## 8. 設定（trace_rules.yml 概要）
- しきい値、対象種別、候補最大件数、無視パス、無視見出し、`integrates_with` の有向/無向扱い 等。

---

## 9. 受入基準（AC）
- **AC-01**: 既知リンク集合に対する **再現率≥0.95、適合率≥0.90**。  
- **AC-02**: 閉路検知/孤立検知/往復未到達の **検知率100%**。  
- **AC-03**: パッチが**決定的**（同一入力で同一 diff）。  
- **AC-04**: 1,000 ファイルで 60s 以内（Graph+候補抽出）。

---

## 10. 試験観点（抜粋）
- **TC-201**: 本文に明示 ID がある場合の候補化。  
- **TC-202**: 見出し「関連HLF」直下の ID に重み付け。  
- **TC-203**: 断リンク → 同名タイトルからの救済候補。  
- **TC-204**: `refines` 閉路の検出。  
- **TC-205**: 重要ノード種の孤立検出。  
- **TC-206**: RS→HLF→FR→TEST→RS の往復到達。  
- **TC-207**: パッチの重複除去・正規化。

---

## 11. CI（最小例）
```yaml
name: docops_trace
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_trace.yml'
jobs:
  trace:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: |
          pip install -U pip
          pip install networkx pyyaml markdown-it-py
      - name: Build Graph & Suggest
        run: |
          python tools/docops_cli/trace.py build             --rules tools/docops_cli/config/trace_rules.yml             --out artifacts/trace --format json,md --emit-dot
          python tools/docops_cli/trace.py suggest             --rules tools/docops_cli/config/trace_rules.yml             --out artifacts/trace --threshold 0.65 --strong-threshold 0.8
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-trace-artifacts
          path: artifacts/trace
```
> 実体 `tools/docops_cli/trace.py` は CR-02 の成果物。

---

## 12. トレース
- **satisfies**: BG-KMK-01, BG-KMK-02, BG-KMK-05  
- **constrains**: CN-KMK-01..03

---

## 付録A: Graph JSON 例（抜粋）
```json
{
  "version": "1",
  "nodes": [
    {"id":"RS-PJT-01","kind":"RS","title":"要件概説","path":"docs/10_requirements/RS-01.md","tags":["requirements"]},
    {"id":"FR-PJT-12","kind":"FR","title":"ログ出力","path":"docs/10_requirements/FR-12.md","tags":["logging"]}
  ],
  "edges": [
    {"source":"FR-PJT-12","target":"RS-PJT-01","e_type":"satisfies","evidence":"frontmatter","confidence":1.0}
  ]
}
```

## 付録B: DOT 例（抜粋）
```
digraph G {
  "FR-PJT-12" -> "RS-PJT-01" [label="satisfies"];
}
```
