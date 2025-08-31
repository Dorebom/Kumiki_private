---
id: CR-KMK-08
title: "CR-08: 多言語対訳整合（ja↔en）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr08, i18n, bilingual, consistency]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-03","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02"]
integrates_with: ["STD-OBSIDIAN-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-08: 多言語対訳整合（ja↔en）— 詳細仕様

> **G**: `docs/ja` と `docs/en` の **ID同等性**・参照整合を検査する。  
> **O**: 差異レポート（JSON/MD）、修正候補（FM追記/置換パッチ、リンク書換）、不足ファイルの **Stub 生成案**。  
> **AC**: 差異の**機械抽出100%**、**誤検知 ≤ 5%**。

---

## 1. 用語
- **対訳ペア**: 同一の **安定ID** を共有し、`docs/ja/**.md` と `docs/en/**.md` に存在する2つの文書。  
- **ID同等性**: JA/EN の FrontMatter `id` が完全一致。  
- **参照整合**: JA/EN の `refines/satisfies/depends_on/...` の **集合**が同一（順序は不問）。  
- **見出し構造指紋**: 見出し階層（H1–H3既定）の **slug 列**から得られる fingerprint。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- ペアリング（IDベース）・存在検査、FrontMatter 比較、関係語彙セット比較、内部リンクの**ロケール整合**検査、見出し構造比較、修正候補生成。

### 2.2 非スコープ（CR-08段階）
- 機械翻訳品質の評価。本文の意味比較。

---

## 3. 入出力
### 3.1 入力
- `docs/ja/**/*.md`, `docs/en/**/*.md`  
- ルール: `tools/docops_cli/config/i18n_rules.yml`（しきい値/対象階層/slug規則/例外）。

### 3.2 出力
- `artifacts/i18n/<run>/report.json|md`（差異一覧と提案）  
- `artifacts/i18n/<run>/patches/*.patch`（FM/リンク書換）  
- `artifacts/i18n/<run>/stubs/`（不足ファイルの stub 案）

---

## 4. 機能要求（FR-08.x）
### FR-08.1 ペアリングと存在検査
- すべての JA/EN 文書から FrontMatter `id` を抽出し、**同一ID**のペアを形成。  
- 片側のみ存在は **I18N010: missing_pair**。`stub` を生成提案。

### FR-08.2 ID同等性
- ペア内で `id` が異なる場合は **I18N001: id_mismatch**。安全な置換案（片側を他方の ID に正規化）を提示。

### FR-08.3 参照整合（関係語彙の集合一致）
- `refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes` について、  
  JA と EN の **集合差分**を算出。欠落/過剰を **I18N020** として列挙し、**FM追記/削除パッチ**案を生成。

### FR-08.4 ロケール整合（内部リンク）
- 本文の相対リンクが、JA では `docs/ja/`、EN では `docs/en/` を指すこと。  
- 他ロケールへの誤リンクは **I18N030: link_locale_mismatch**。**書換パッチ**を生成。  
- ID参照リンク（`[text](../FR-FOO-01.md)` 等）は **同一 ID** の **同ロケールパス**に誘導。

### FR-08.5 見出し構造指紋
- H1–H3 の slug リストを抽出し、**Jaccard** 類似度を算出。`min_jaccard` 未満は **I18N040: heading_divergence**。  
- スラッグ規則は `i18n_rules.yml` の **ja_slug/en_slug** を用いる（日本語はかな英数化＋記号除去、英語は小文字+ハイフン連結）。

### FR-08.6 タグ・ステータスの整合（任意）
- `status`（draft/approved 等）と主要 `tags`（ドメインタグ）は一致が望ましい。差分は **WARN(I18N050)**。

### FR-08.7 提案生成（決定的）
- `patches/*.patch` は **unified diff**。`stubs/` は FrontMatter のみを含む **雛形**を生成（`status: needs-translation`）。  
- 生成順序・キー順は固定化し**決定性**を担保。

### FR-08.8 性能
- 2×1,000 ファイルで **≤ 90s**。

---

## 5. アルゴリズム
1. JA/EN をそれぞれ走査し `id→path` 辞書を構築。  
2. **共通ID**でペア、**片側のみ**は missing_pair。  
3. ペアごとに FrontMatter の関係語彙セットを比較（順序無視、重複除去）。  
4. 本文リンクを抽出しロケール正当性を検査（パス正規化、IDリンクは他方辞書で逆引き）。  
5. 見出しを H1–H3 で抽出し slug 化→ Jaccard 類似度。  
6. 差分に応じて **パッチ/Stub** を生成。

---

## 6. ルール/コード（I18N*）
- **I18N001**: id_mismatch  
- **I18N010**: missing_pair  
- **I18N020**: relation_set_diff  
- **I18N030**: link_locale_mismatch  
- **I18N040**: heading_divergence  
- **I18N050**: tag_or_status_diff (WARN)

---

## 7. CLI I/F（案）
```bash
# 検査
docops i18n verify   --rules tools/docops_cli/config/i18n_rules.yml   --out artifacts/i18n --format json,md

# 修正提案（パッチ/スタブ）
docops i18n suggest   --rules tools/docops_cli/config/i18n_rules.yml   --out artifacts/i18n --emit-stubs
```

---

## 8. 受入基準（AC）
- **AC-01**: 差異の機械抽出 **100%**（ゴールドセットに対し漏れなし）。  
- **AC-02**: **誤検知 ≤ 5%**。  
- **AC-03**: 2×1,000 ファイルで **≤ 90s**。

---

## 9. 設定（i18n_rules.yml 概要）
- ルートパス、見出し対象レベル、slug 規則（ja/en）、Jaccard しきい値、ロケールリンクの厳格度、stub のテンプレ。

---

## 10. CI（最小例）
```yaml
name: docops_i18n
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_i18n.yml'
jobs:
  i18n:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          pip install -U pip
          pip install pyyaml regex python-slugify markdown-it-py
      - name: Verify & Suggest
        run: |
          python tools/docops_cli/i18n.py verify             --rules tools/docops_cli/config/i18n_rules.yml             --out artifacts/i18n --format json,md
          python tools/docops_cli/i18n.py suggest             --rules tools/docops_cli/config/i18n_rules.yml             --out artifacts/i18n --emit-stubs
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-i18n-artifacts
          path: artifacts/i18n
```

---

## 11. トレース
- **satisfies**: BG-KMK-03（多言語でも検索・参照品質を維持）, BG-KMK-05  
- **depends_on**: CR-01（FMルール）, CR-02（関係語彙）, CR-03（slug/link生成規則の再利用）  
- **constrains**: CN-KMK-01..03

---

## 付録A: 見出し slug 規則（既定）
- **ja_slug**: 非ASCII をかな英数へ可能な範囲で変換、空白/記号を `-` に、連続 `-` を圧縮、先頭末尾をトリム。  
- **en_slug**: 小文字化→英数字以外を `-` に、連続 `-` 圧縮、トリム。

## 付録B: report.json の例（抜粋）
```json
{
  "summary": { "pairs": 220, "missing": 3, "id_mismatch": 1, "relation_diff": 5, "link_mismatch": 2, "heading_divergence": 4 },
  "items": [
    {
      "id": "FR-LOG-12",
      "ja_path": "docs/ja/10_requirements/FR-LOG-12.md",
      "en_path": "docs/en/10_requirements/FR-LOG-12.md",
      "issues": ["relation_set_diff","heading_divergence"],
      "patches": ["patches/FR-LOG-12_fm.patch"],
      "stubs": []
    }
  ]
}
```
