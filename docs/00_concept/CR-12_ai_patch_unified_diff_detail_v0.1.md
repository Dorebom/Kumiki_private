---
id: CR-KMK-12
title: "CR-12: 生成AI差分パッチ提案（unified diff）— 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr12, ai, patch, diff, review]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04","CR-KMK-05","CR-KMK-06","CR-KMK-07","CR-KMK-08","CR-KMK-09","CR-KMK-10","CR-KMK-11"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-12: 生成AI差分パッチ提案（unified diff）— 詳細仕様

> **G**: LLM 出力は **unified diff** のみで提示し、PR レビューに直結させる。  
> **AC**: **採用率 ≥ 60%**、**NG 再発 ≤ 5%/週**。

---

## 1. 背景/目的
- 既存の DocLint（CR-01）、Trace（CR-02）、Impact（CR-06）、IDCheck（CR-07）、I18N（CR-08）、SecScan（CR-09）の**検出結果**を入口に、  
  LLM が **安全な範囲（文書/FrontMatter/リンク/軽微文言）** で **修正パッチ**を生成する。  
- **人手承認前提**。AI の提案は **PR へのコメント**または **`.patch` ファイル**として提示し、**自動適用しない**。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- 入力（差分/検出結果/文脈）→ **プロンプト構成** → **unified diff 出力** → **ポストチェック** → **CI への提示**。

### 2.2 非スコープ（CR-12段階）
- 大規模な再構成（ファイル移動/大量削除/生成）。**最大変更行数**などの上限を設ける。

---

## 3. 入出力
### 3.1 入力
- **PR 差分ハンク**（`git diff --unified=3`）、対象ファイル本文（該当セクションのみ）。  
- **検出トリガ**: DocLint/IDCheck/I18N/SecScan/Impact の**違反または提案**（JSON）。  
- **Graph 文脈**: 対象 ID の FrontMatter、近傍ノードの ID/見出し。

### 3.2 出力
- `artifacts/ai_patch/<run>/patches/*.patch`（**unified diff**：`--- a/...`/`+++ b/...`/`@@`）。  
- `artifacts/ai_patch/<run>/report.json`（提案の**要約・根拠・信頼度・安全検査**）。  
- `artifacts/ai_patch/<run>/snippets/`（該当箇所のハイライト・比較、任意）。

---

## 4. 出力制約（厳格）
- **テキストのみ**、**unified diff 以外の文字列（解説/前置き/コードブロック）を禁止**。  
- 新規ファイルは `diff --git a/… b/…` + `new file mode` を明示。バイナリは提案しない。  
- **FrontMatter 禁止事項**: `id` の**変更/削除**、`created/updated` の**改竄**、監査用フィールドの削除。  
- **行数上限**: 1提案あたり **≤ 120 行**、ファイル数 **≤ 5**。

---

## 5. セーフティ/ポストチェック
- **DocLint**: 適用後の文書がルールに適合（CR-01）。  
- **Trace 再検証**: 断リンク・循環が悪化しない（CR-02/04）。  
- **SecScan**: 秘密/PII を**導入していない**（CR-09）。  
- **I18N**: 対訳整合の破壊なし（CR-08、対象が ja/en の場合）。  
- **差分最小化**: 変更は**最小必要行**に留める（ハムラビ距離比率で評価）。  
- **決定性**: `temperature=0.0`, `top_p=1.0`, `seed=42`。

---

## 6. プロンプト設計（概要）
- **System**: 役割・禁止事項・出力形式（unified diffのみ）・言語ポリシー。  
- **User**: ①違反/提案の JSON（正規化） ②対象ハンク/本文抜粋 ③FrontMatter ④Graph 近傍 ⑤制約。  
- **Stop**: `
\ No newline at end of file` のような diff 記法は許容。追加の文章は禁止。

---

## 7. スコアリング/優先度
- **Impact score（CR-06）** と違反の重大度で優先度を決定。  
- `score = 0.6*impact + 0.4*severity`。 `score ≥ 0.75` のみ提案。

---

## 8. 受入審査フロー
1. LLM の diff → **ポストチェック**を通過したものだけ `patches/*.patch` に保存。  
2. PR に **チェックランのアーティファクト**として添付（任意でコメント投稿）。  
3. レビュアが手元で `git apply` → DocLint/Trace を再実行 → マージ。

---

## 9. メトリクス（CR-11連携）
- **採用率**: `accepted / proposed`（P95週）。目標 **≥ 60%**。  
- **NG 再発率**: 週内に **DocLint/SecScan で再発**した割合。目標 **≤ 5%/週**。  
- 収集形式は `metrics_event.json`/`metrics_summary.json`（CR-11）。

---

## 10. CI（最小例）
```yaml
name: docops_ai_patch
on:
  pull_request:
    paths: ['docs/**','tools/**','.github/workflows/docops_ai_patch.yml']
jobs:
  suggest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Generate AI patch proposals
        env:
          AI_PROVIDER: "openai"
          AI_MODEL: "gpt-4o-mini"
          AI_TEMPERATURE: "0.0"
          AI_TOP_P: "1.0"
          AI_SEED: "42"
        run: |
          python tools/docops_cli/ai_patch.py suggest             --rules tools/docops_cli/config/ai_patch_rules.yml             --prompts tools/docops_cli/prompts             --out artifacts/ai_patch --format json,patch
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with: { name: docops-ai-patch, path: artifacts/ai_patch }
```
> 実体 `ai_patch.py` は CR-12 の成果物（別途実装）。

---

## 11. トレース
- **satisfies**: BG-KMK-01（工数削減）, BG-KMK-02（品質向上）, BG-KMK-05（公開運用）  
- **depends_on**: CR-01..11  
- **constrains**: CN-KMK-01..03

---

## 付録A: 失敗/抑止ルール（AP*）
- **AP001**: diff 以外のテキストを出力 → **Reject**。  
- **AP010**: FrontMatter の `id/created/updated` を変更 → **Reject**。  
- **AP020**: 1提案の行数超過（>120）/ファイル超過（>5） → **Trim or Reject**。  
- **AP030**: ポストチェック失敗（DocLint/Trace/SecScan/I18N） → **Reject**。

## 付録B: report.json（例）
```json
{
  "summary": {"proposed": 5, "accepted": 3, "rejected": 2, "time_sec": 18.2},
  "items": [
    {
      "id": "AP-20250831-001",
      "path": "docs/00_concept/CR-01_doclint_detail.md",
      "reason": "DocLint: missing 'satisfies' in FrontMatter",
      "impact": 0.82,
      "severity": 0.6,
      "score": 0.73,
      "diff_file": "patches/CR-01_fix_satisfies.patch",
      "post_checks": {"doclint": "ok","trace":"ok","secscan":"ok","i18n":"skip"},
      "confidence": 0.72
    }
  ]
}
```
