---
id: CR-KMK-04
title: "CR-04: 往復トレース到達テスト（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr04, reachability, roundtrip]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-04: 往復トレース到達テスト（詳細仕様）

> **G**: RS↔HLF↔FR/NFR↔CN↔DD↔TEST↔TRACE の**往復到達**を自動検証する。  
> **O**: 不到達ノード/リンクの一覧、修正候補（FM 追記パッチ）。  
> **AC**: **重要ノード**に対し往復到達 **100%**。

---

## 1. 用語
- **往復到達（Roundtrip Reachability）**: 起点ノードから指定レイヤを**順方向**に辿り、検査終点から**起点へ戻る**経路が存在すること。  
- **レイヤ（Layer/Kinds）**: `RS, HLF, FR, NFR, CN, DD, TEST, TRACE`。  
- **関係語彙**: `refines, satisfies, depends_on, integrates_with, constrains, conflicts_with, supersedes`（固定）。  
- **重要ノード**: 既定は `RS, HLF, FR, NFR, CN`。設定で変更可。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- FM→Graph（CR-02）を前提に、**レイヤ制約付き最短往復探索**、閉路/孤立検知、欠落区間の**修復候補**提案。

### 2.2 非スコープ（CR-04段階）
- Embedding に基づく自動リンク生成（CR-03/02 の候補出力は利用可）。

---

## 3. 入出力
### 3.1 入力
- Graph JSON（CR-02 の `graph.json`）または `docs/**/*.md`（内部で生成）。  
- ルール: `tools/docops_cli/config/reach_rules.yml`。  
- （任意）期待ゴール: `eval/reach_goals.yaml`。

### 3.2 出力
- `artifacts/reach/<run>/report.json|md`（到達率/違反一覧/提案）。  
- `artifacts/reach/<run>/patches/*.patch`（FM 追記案）。  
- `artifacts/reach/<run>/coverage.csv`（ノード単位の達成ステータス）。

---

## 4. 仕様（レイヤ/遷移/極性）
### 4.1 既定の正規化極性（FMの向き→論理順方向）
- `refines`: **下位→上位**（例: `HLF -> RS`, `DD -> FR`）。**順方向**は **逆向き**に辿る（`RS -> HLF`）。  
- `satisfies`: **下位→上位**（例: `FR -> RS`, `TEST -> FR` を推奨）。**順方向**は **逆向き**（`RS -> FR`）。  
- `depends_on`: 双方向に辿れる補助（順方向/逆方向ともに許容）。  
- `integrates_with`: 無向（双方向）。  
- `constrains`: **CN -> *（制約対象）** を推奨。順方向は **CN を経由**可能（`FR <-> CN`）。  
- `conflicts_with/supersedes`: 到達には不使用（検査上の情報として扱う）。

> **注**: 既存リポで「TEST depends_on FR」等の表現がある場合は `reach_rules.yml` の `edge_alias` で **satisfies 相当**に寄せる。

### 4.2 レイヤ遷移（既定）
順方向（Go）：
```
RS → HLF? → (FR | NFR)+ → CN? → DD? → TEST+ → TRACE+
```
- `?`: 任意, `+`: 1つ以上。HLF/CN/DD は**スキップ許容**（設定可）。FR|NFR は**いずれか必須**。  
- 逆方向（Back）：TRACE または TEST から **FR/NFR → RS** へ戻る（`satisfies/refines` の**逆辿り**）。  
- **到達成立条件**: Go/Back がともに成立し、途中の**重要レイヤ**（既定: RS/HLF/FR/NFR/CN）を仕様通り通過。

---

## 5. アルゴリズム
1. **Graph 正規化**: CR-02 生成の `graph.json` を読み込み、`reach_rules.yml` に従い**論理順方向**エッジ集合を構築。  
2. **起点集合**: `start_kinds: ['RS']` を既定とし、全 RS を起点に評価。  
3. **制約付き探索（Go）**: レイヤ DFA に基づく BFS/多段 Dijkstra を実施。FR/NFR は**どちらかを踏めば可**。  
4. **到達終点**: `TRACE` or `TEST` に到達した時点で Back 探索へ遷移。  
5. **逆探索（Back）**: 逆極性で `FR/NFR` → `RS` のパスを探索。  
6. **往復成立**: Go/Back ともに成立し、定義済み必須レイヤが**少なくとも1回**含まれること。  
7. **不足区間推定**: 未成立の場合、最短**欠落レイヤ**を特定し、CR-02 の候補生成規則を用いて **FM 追記案**を提示。  
8. **決定性**: 入力が同一なら**同一経路/提案**を出力（ソート基準・tie-breaker を固定）。

---

## 6. ルール/コード（RT*）
- **RT001**: 起点から Go 経路なし（例: `RS` から `FR/NFR` へ辿れない）。  
- **RT002**: Back 経路なし（`TEST/TRACE` から `RS` に戻れない）。  
- **RT010**: 必須レイヤ欠落（HLF/FR|NFR/CN/DD/TEST/TRACE いずれか不通）。  
- **RT020**: 閉路による停滞（到達不能化）。  
- **RT030**: 断リンク（CR-02 の TR020 と連携）。

---

## 7. CLI I/F（案）
```bash
# 往復到達の検証
docops reach verify   --rules tools/docops_cli/config/reach_rules.yml   --graph artifacts/trace/<run>/graph.json   --out artifacts/reach --format json,md --emit-csv

# 修復候補（FM 追記パッチ）を出力
docops reach suggest   --rules tools/docops_cli/config/reach_rules.yml   --graph artifacts/trace/<run>/graph.json   --out artifacts/reach/patches
```

---

## 8. 受入基準（AC）
- **AC-01**: 重要ノード（既定: RS/HLF/FR/NFR/CN）について往復到達 **100%**。  
- **AC-02**: 欠落時に**最小提案**を生成（重複/循環なし）。  
- **AC-03**: 1,000 ファイルで **≤ 60s**。

---

## 9. 出力形式
- `report.json`（schema: `schemas/reach_report.json`）: ノード別ステータス、違反（RT*）、提案パッチ一覧。  
- `report.md`: サマリ + 上位違反、主要ノードの往復経路例。  
- `coverage.csv`: `id,kind,go,back,roundtrip,missing_layers`。

---

## 10. CI（最小例）
```yaml
name: docops_reach
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_reach.yml'
jobs:
  reach:
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
          pip install networkx pyyaml
      - name: Build Graph (if not exists) & Verify
        run: |
          python tools/docops_cli/trace.py build             --rules tools/docops_cli/config/trace_rules.yml             --out artifacts/trace --format json
          python tools/docops_cli/reach.py verify             --rules tools/docops_cli/config/reach_rules.yml             --graph artifacts/trace/graph.json             --out artifacts/reach --format json,md --emit-csv
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-reach-artifacts
          path: artifacts/reach
```

---

## 11. トレース
- **satisfies**: BG-KMK-01, BG-KMK-02, BG-KMK-05  
- **depends_on**: CR-02（Graph）  
- **constrains**: CN-KMK-01..03

---

## 付録A: 例（推奨FM）
- `HLF-CTRL-01 refines RS-CTRL-00`  
- `FR-LOG-12 satisfies RS-OBS-03`  
- `DD-LOG-12 refines FR-LOG-12`  
- `TEST-LOG-12 satisfies FR-LOG-12`（または `depends_on FR-LOG-12` を `edge_alias` で `satisfies` 相当に）  
- `TRACE-REL-01 integrates_with TEST-LOG-12` / `satisfies RS-OBS-03`（証跡が要求に紐付く場合）

