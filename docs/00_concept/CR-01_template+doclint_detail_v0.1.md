---
id: CR-KMK-01
title: "CR-01: テンプレート自動展開と DocLint（詳細仕様）"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr01, doclint, template]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["STD-KMK-FM-01","STD-KMK-ID-01"]
integrates_with: ["STD-GHA-01","STD-OBSIDIAN-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-01: テンプレート自動展開と DocLint（詳細仕様）

> **目的**: 雛形展開（テンプレートの自動生成）と **DocLint**（文書構造・FrontMatter・リンク・UML 等の一貫検査）を統合し、
> PR 時に**自動ゲート**する。Obsidian 表示・GitHub Pages 公開と**完全整合**させる。

---

## 1. 用語
- **テンプレート展開**: フォルダ構成とファイル雛形の一括生成（FM 初期値・安定 ID プレースホルダ付与）。
- **DocLint**: FrontMatter 検証、関係語彙検査、ID/リンク整合、PlantUML 構文、外部リンク健全性の総称。
- **固定語彙**: `refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes`。配列は **文字列 ID のみ**。
- **フラット FrontMatter**: ネスト禁止（配列は許容）。Obsidian 互換で表示が崩れないこと。

---

## 2. スコープ / 非スコープ
### 2.1 スコープ
- 雛形展開対象: `CR/RS/HLF/FR/NFR/CN/ADR/TRACE`（必要最小の Markdown）。
- Lint 対象: FrontMatter / 関係語彙 / 安定 ID / 相対リンク / 画像 / 外部リンク / PlantUML。
- 成果物: Lint レポート（JSON/Markdown）, 修復パッチ（unified diff）, Graph（DOT/JSON）, 指標メトリクス。

### 2.2 非スコープ（CR-01段階）
- Embedding/ANN の実索引生成（CR-03）。
- セキュリティ/PII 検知（CR-09）。

---

## 3. 入出力
### 3.1 入力
- `docs/` 下の Markdown 群（`.obsidian/` は対象外）。
- 語彙・ルール: `tools/docops_cli/config/doclint_rules.yml`。

### 3.2 出力
- `artifacts/doclint/<commit|run-id>/report.json`（構造化レポート）。
- `artifacts/doclint/<...>/report.md`（人間可読）。
- `artifacts/doclint/<...>/graph.(dot|json)`（リンクグラフ）。
- `artifacts/doclint/<...>/patches/*.patch`（自動修復案）。

---

## 4. 機能要求（FR-01.x）
### FR-01.1 テンプレート展開（CLI）
- **UI**: `docops templates init --preset kumiki --out docs --force?`  
- **生成**: `docs/00_concept/`, `10_requirements/`, `20_design/`, `30_test/`, `40_ops/`, `adr/`, `trace/`。  
- **FM 初期化**: 必須キー（id/title/type/status/version/created/updated/owner/tags）を埋め、関係配列は空配列。  
- **ID プレースホルダ**: `CR-KMK-XX` 形式を付与（重複回避は DocLint 側で検出）。
- **受入基準**: 雛形生成の**再入可能**性（同一コマンド 3 回実行で差分なし）。

### FR-01.2 FrontMatter ルール検証
- **必須キー**: `id,title,type,status,version,created,updated,owner,tags`。  
- **任意キー**: `canonical_parent,refines,satisfies,depends_on,integrates_with,constrains,conflicts_with,supersedes` のみ。  
- **型制約**: 文字列 or 文字列配列。ネスト禁止。  
- **ID 形式**（例）: `^(CR|RS|HLF|FR|NFR|CN|ADR|TRACE)-[A-Z0-9](2,)-[0-9A-Za-z_.-]+$`。  
- **重複/欠番**: 既存ファイルと照合し、重複は **ERROR(DL001)**、未参照 ID は **WARN(DL101)**。

### FR-01.3 関係語彙の検査
- **許可キー限定**（固定語彙のみ）。未知キーは **ERROR(DL010)**。  
- **参照 ID 実在**: 参照先ファイルが存在しなければ **ERROR(DL011)**。  
- **自己循環**: 自己を参照するリンクは **ERROR(DL012)**。

### FR-01.4 リンク健全性
- **相対リンク**: 存在/大小文字/拡張子/アンカーID（Markdown header→slug）を検査。  
- **外部リンク**: `HEAD` もしくは `GET` で 2xx/3xx を許容、4xx/5xx は **WARN(DL201)**（ゲート可変）。  
- **画像**: 画像ファイルの存在と拡張子（png/jpg/svg/gif）を検査。

### FR-01.5 PlantUML 構文
- コードブロック ```plantuml ... ``` または `@startuml`〜`@enduml` を検知。  
- `-checksyntax` 等で検証し、失敗は **ERROR(DL020)**。

### FR-01.6 グラフ生成と到達性
- FrontMatter 関係を DOT/JSON に落とし、孤立ノード・断リンク・循環を抽出。  
- **循環**: `refines/satisfies` の閉路を **ERROR(DL013)**。  
- **孤立**: 重要ノード種（RS/FR/NFR/CN/HLF）が孤立なら **WARN(DL102)**。

### FR-01.7 しきい値とゲート
- 重大 **ERROR** が 1 件でもあれば PR を **fail**。  
- **WARN** は集計。`--fail-on-warn` オプションでゲート強化可。

### FR-01.8 性能・スケール
- 1,000 ファイルで 60 秒以内（DocLintのみ）。10,000 ファイルで 10 分以内（nightly）。

### FR-01.9 設定ファイル（例）
- 既定は `tools/docops_cli/config/doclint_rules.yml` を使用。リポジトリごとに上書き可能。

### FR-01.10 出力と可観測性
- Markdown/JSON の **二重レポート**、メトリクス（ルール別件数、実行時間）を保存。

---

## 5. 受入基準（AC）
- **AC-01**: テンプレート展開再入可能、差分なし。  
- **AC-02**: 必須キー欠落を 100% 検知（偽陽性 0）。  
- **AC-03**: 関係語彙の未知キー検出 100%。  
- **AC-04**: 参照切れ/自己循環/循環検知 100%。  
- **AC-05**: PlantUML 構文エラー検知 100%。  
- **AC-06**: 1,000 ファイルで 60s 以内。

---

## 6. ルールコード（例）
- **DL001**: 必須キー欠落  
- **DL002**: 型不一致（配列以外/配列内が文字列以外）  
- **DL003**: ID 形式不一致（regex違反）  
- **DL010**: 非許可の関係語彙キー  
- **DL011**: 参照 ID が存在しない  
- **DL012**: 自己参照  
- **DL013**: 閉路検出（refines/satisfies）  
- **DL020**: PlantUML 構文エラー  
- **DL101**: 未参照 ID（孤立候補）  
- **DL102**: 重要ノードの孤立  
- **DL201**: 外部リンク死活不良（4xx/5xx/Timeout）

---

## 7. CLI I/F（参考）
```bash
# 雛形展開
docops templates init --preset kumiki --out docs

# Lint 実行（PR最小ゲート）
docops lint --rules tools/docops_cli/config/doclint_rules.yml --format json,md --out artifacts/doclint

# Graph 出力
docops graph --out artifacts/doclint
```

---

## 8. CI（最小例・PRゲート）
```yaml
name: docops_min
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - '.github/workflows/docops_min.yml'
jobs:
  docops:
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
          pip install networkx pyyaml markdown-it-py plantuml-markdown
      - name: DocLint
        run: |
          python tools/docops_cli/lint.py             --rules tools/docops_cli/config/doclint_rules.yml             --out artifacts/doclint --format json,md
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: doclint-artifacts
          path: artifacts/doclint
```
> 実体スクリプト `tools/docops_cli/lint.py` は別途実装（CR-01の成果物）。

---

## 9. 試験観点（抜粋）
- **TC-001** 必須キーの欠落検知。  
- **TC-002** 関係語彙に未知キーがある。  
- **TC-003** 参照 ID のファイル不在。  
- **TC-004** 自己参照を含む。  
- **TC-005** `refines` 閉路がある。  
- **TC-006** 相対リンクの拡張子違い。  
- **TC-007** 外部リンク 404。  
- **TC-008** PlantUML の `@enduml` 欠落。  
- **TC-009** `.obsidian/` 配下を無視している。  
- **TC-010** 1,000 ファイルで 60s 以内。

---

## 10. オープン事項（OQ）
- ID 形式の最終正規表現（既存資産との互換）。  
- 外部リンクの許容タイムアウト（3s/5s/10s）。  
- PlantUML チェックの実装方式（ローカル vs サービス）。

---

## 11. トレース
- **satisfies**: BG-KMK-01（工数削減）, BG-KMK-02（トレース欠落ゼロ）, BG-KMK-05（常時公開可能）。  
- **constrains**: CN-KMK-01..03（フラット FM、固定語彙、GHA/Pages 前提）。
