---
id: CR-KMK-07
title: "CR-07: ID整合と重複検出/修復案（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr07, id, duplicate, repair]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-07: ID整合と重複検出/修復案（詳細仕様）

> **G**: **安定ID**の重複/欠番/断リンクを検出し**自動修復案**を提示する。  
> **O**: 検出レポート（JSON/MD）、`old→new` マップ、FM/本文の**一括置換パッチ**、`supersedes` 追記案。  
> **AC**: **重複検出再現率 ≥ 0.99、誤修復 ≤ 0.5%**。

---

## 1. 用語
- **安定ID**: `^(CR|RS|HLF|FR|NFR|CN|ADR|TRACE|DD|TEST)-[A-Z0-9]{2,}-[0-9A-Za-z_.-]+$` を満たす識別子。  
- **重複（Duplicate）**: **異なるファイル**が**同一ID**を宣言。  
- **欠番（Gap）**: シリーズ（例: `FR-LOG-XX`）の **番号飛び**。厳密には **任意**だが、`series_rules` を設定した場合のみ違反。  
- **断リンク（Broken Ref）**: FM/本文の参照IDが**不在**。  
- **正規化（Normalization）**: 大小文字/余分な空白/全半角などを **ID規則に収束**。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- ID スキーマ検査、重複/断リンク検出、シリーズ欠番（任意）、自動修復案生成、`supersedes`/`conflicts_with` の補助提案。

### 2.2 非スコープ（CR-07段階）
- 参照テキストの**意味的な**再ライティング（単純置換のみ）。

---

## 3. 入出力
### 3.1 入力
- `docs/**/*.md`（`.obsidian/` 除外）  
- Graph JSON（CR-02, 任意。リンク整合の再検証に使用）  
- ルール: `tools/docops_cli/config/id_rules.yml`

### 3.2 出力
- `artifacts/idcheck/<run>/report.json|md`（重複/欠番/断リンク/正規化違反）  
- `artifacts/idcheck/<run>/patches/*.patch`（FM/本文の置換パッチ）  
- `artifacts/idcheck/<run>/renames.csv`（`old_id,new_id,reason`）

---

## 4. 機能要求（FR-07.x）
### FR-07.1 IDスキーマ/正規化
- Regex 準拠を検査。大小混在は **大文字化**、全角→半角、余分な空白/記号の除去ルールを適用（`normalize`）。  
- 既定の **接頭辞→kind** 対応を維持（CR-02 と同一）。

### FR-07.2 重複検出
- **ファイル間**で同一 `id` が存在すれば **DUP001**。  
- **選好規則**: `created` が古い方を **正（canonical）**、新しい方を **改名候補**とする（同値はパス辞書順）。

### FR-07.3 欠番（任意）
- `series_rules` を設定した場合のみ評価（例: `FR-LOG-{NN}`）。  
- 欠番は **WARN(GAP101)**、シリーズ範囲の表を `report.md` に生成。

### FR-07.4 断リンク検出
- FM（`refines/satisfies/...`）および本文中の **IDパターン**を抽出→**存在確認**。  
- 不在の場合 **BRK010**。最適候補（タイトル類似、`tags` 一致、同フォルダ近接）を **Top3** 提案。

### FR-07.5 自動修復案（決定的）
- **重複**: 改名対象の `id` を **一意な新ID**に置換。形式: `<prefix>-<SERIES>-<slug>[-R<rev>]`。  
  - 置換対象: ファイルの FrontMatter `id` と **全参照**（FM/本文）を一括更新。  
  - **supersedes**: 改名後の FM に `supersedes: ["<old_id>"]` を自動追記提案。  
- **正規化**: 大文字化/全半角変換/トリムを安全に適用。  
- **断リンク**: 候補のうちスコア ≥ `0.8` を **推奨置換**、< `0.8` は **stub 作成**（空の雛形）提案。  
- パッチは **unified diff**、`renames.csv` を併出力。

### FR-07.6 安全性/影響評価
- 置換前後で **Graph 差分**を計算し、`refines/satisfies` の **閉路が増えない**ことを確認。  
- 影響が大きい場合は **IMPACT WARN**（CR-06 と連携）。

### FR-07.7 決定性/性能
- 同入力で出力が**ビット等価**。ソート/タイブレークを固定化。  
- 1,000 ファイルで **≤ 60s**。

---

## 5. しきい値と評価
- **重複検出再現率 ≥ 0.99**（`eval/id_cases.yaml` の重複シナリオ）。  
- **誤修復 ≤ 0.5%**（置換誤り/誤候補選択率）。  
- 断リンク候補の Top1 適合率（任意）≥ 0.85。

---

## 6. ルール/コード（ID*）
- **ID001**: ID 形式不一致 / 正規化必要。  
- **ID010**: 重複検出。  
- **ID020**: 断リンク（FM/本文）。  
- **ID030**: 欠番（シリーズ）。  
- **ID040**: 修復パッチ生成。  
- **ID050**: Graph 影響大のため要注意。

---

## 7. CLI I/F（案）
```bash
# 検査のみ
docops idcheck verify   --rules tools/docops_cli/config/id_rules.yml   --out artifacts/idcheck --format json,md

# 修復案の生成（unified diff, renames.csv）
docops idcheck suggest   --rules tools/docops_cli/config/id_rules.yml   --out artifacts/idcheck --generate-stub
```

---

## 8. 設定（id_rules.yml 概要）
- `id_regex`、`normalize`、`series_rules`、`rename_policy`（canonical優先/新規採番）、`candidate_threshold`、`stub_template`。

---

## 9. CI（最小例）
```yaml
name: docops_idcheck
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_idcheck.yml'
jobs:
  idcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - name: Set up Python
        uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - name: Install deps
        run: |
          pip install -U pip
          pip install pyyaml regex python-slugify
      - name: Verify & Suggest
        run: |
          python tools/docops_cli/idcheck.py verify             --rules tools/docops_cli/config/id_rules.yml             --out artifacts/idcheck --format json,md
          python tools/docops_cli/idcheck.py suggest             --rules tools/docops_cli/config/id_rules.yml             --out artifacts/idcheck --generate-stub
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-idcheck-artifacts
          path: artifacts/idcheck
```

---

## 10. トレース
- **satisfies**: BG-KMK-01（工数削減）, BG-KMK-02（トレース品質）, BG-KMK-05（常時公開可能）  
- **depends_on**: CR-01（FM/DocLint）, CR-02（Graph）  
- **constrains**: CN-KMK-01..03

---

## 付録A: 置換パッチ例
```
--- a/docs/10_requirements/FR-LOG-12.md
+++ b/docs/10_requirements/FR-LOG-12.md
@@
-id: FR-LOG-12
+id: FR-LOG-12A
@@
- satisfies: ["RS-OBS-03"]
+ satisfies: ["RS-OBS-03"]
+ supersedes: ["FR-LOG-12"]
```
