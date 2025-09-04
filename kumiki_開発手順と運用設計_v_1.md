# Kumiki 開発手順と運用設計 v1.0

> 目的：Kumiki を「自分自身のドキュメントにも適用される DocOps システム」として、後戻りコストを抑えつつ段階的に完成度を高め、長期運用と拡張を両立するための実践ガイド。

---

## 0. 全体方針（要点）
- **二層構造**で考える：
  - **Control Plane**（標準・スキーマ・CLI・Actions）＝仕組みを定義・提供する層。
  - **Data Plane**（docs/ 配下の実ドキュメント）＝仕組みの対象物として運用される層。
- **安定リング**（Experimental → Beta → GA）をスキーマ/CLI/Actions のすべてに適用し、リングに応じて CI ゲート強度・後方互換ポリシーを変える。
- **docops.lock による固定化**：スキーマ/CLI/Actions のバージョンを docops.lock で明示的に固定。CI は lock 情報を唯一の真実とする。
- **最小核→段階拡張**：PR 最小ゲート（docops_min）→ Nightly 総合（docops_full）→ Release Publish（サイト公開＋成果物固定）の 3 段で運用。
- **Workflow は“分解＋呼び出し（workflow_call/Composite Action）”**。巨大ワークフローは分割して再利用性とデバッグ容易性を確保。
- **契約テスト（Contract Tests）＋ゴールデンテスト**で I/O 互換を守る（graph.json, trace.json, index/ 等の出力をスナップショット管理）。

---

## 1. リポジトリ戦略
### 1.1 構成（推奨 Monorepo）
```
/ (root)
├─ docs/                 # Data Plane：運用対象のドキュメント（Obsidian互換）
│  ├─ 00_concept/
│  ├─ 01_requirements/
│  ├─ 02_architecture/
│  ├─ 03_design/
│  ├─ 09_ops/
│  └─ 99_std/
├─ tools/
│  └─ docops_cli/        # Control Plane：CLI（Python）
│      ├─ kumiki/        # パッケージ本体
│      ├─ tests/         # 単体/統合/ゴールデン
│      └─ pyproject.toml
├─ .github/
│  ├─ actions/           # Composite Actions（再利用・ピン止め可能）
│  └─ workflows/
│      ├─ docops_min.yml
│      ├─ docops_full.yml
│      └─ publish_pages.yml
├─ mkdocs.yml
├─ docops.lock           # 運用固定ポイント（バージョン・ポリシ・フラグ）
└─ MIGRATIONS.md         # 破壊的変更の移行手順と自動変換ルール
```

### 1.2 ブランチ/公開方針
- `main`: 安定（Beta 以上）。PR ゲートは docops_min 通過必須。
- `develop`（任意）：機能統合。Nightly で docops_full を回す。
- `feat/*`: 機能開発（Experimental）。
- 公開は **タグ（vX.Y.Z）基準**で Pages／Releases を実施。
- 公開/非公開の混在が必要なら **public mirror** を導入（private を SoT、public は CI で同期）。

---

## 2. スキーマ/語彙/ID（長期互換の土台）
### 2.1 FrontMatter 原則
- **フラット 1 段**（Obsidian 互換）
- **関係語彙（固定）**：`refines / satisfies / depends_on / integrates_with / constrains / conflicts_with / supersedes`
- **上流語彙**：`refines / satisfies`、**根拠**：`derives_from`（導入可）
- 値は **文字列 ID の配列のみ**（オブジェクト禁止）

### 2.2 JSON Schema（抜粋サンプル）
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id": {"type": "string", "pattern": "^[A-Z][A-Z0-9-_.]+$"},
    "title": {"type": "string"},
    "parent": {"type": "string"},
    "children": {"type": "array", "items": {"type": "string"}},
    "refines": {"type": "array", "items": {"type": "string"}},
    "satisfies": {"type": "array", "items": {"type": "string"}},
    "depends_on": {"type": "array", "items": {"type": "string"}},
    "integrates_with": {"type": "array", "items": {"type": "string"}},
    "constrains": {"type": "array", "items": {"type": "string"}},
    "conflicts_with": {"type": "array", "items": {"type": "string"}},
    "supersedes": {"type": "array", "items": {"type": "string"}},
    "derives_from": {"type": "array", "items": {"type": "string"}},
    "version": {"type": "string"}
  },
  "required": ["id", "title"]
}
```

### 2.3 ID レジストリ運用
- `99_std/STD-KMK-REG-01.md` に **ID 予約・エイリアス・廃止**のルールを明記。
- **本文内 ID の拾い上げ**（例：`ID: BG-KMK-01` のようなパターン）を CLI が抽出→`id_registry.yml` に同期。
- **unknown_refs** は Phase1=警告、Phase2=エラー。**別名（alias）/履歴（deprecated）** を許可して自動解決。

---

## 3. CLI 設計（tools/docops_cli）
### 3.1 コマンド面（I/O 契約）
- `fm validate`：FM 構文＋Schema 検証
- `graph build`：FrontMatter→`graph.json`（ノード/エッジ/逆索引/unknown_refs）
- `trace build`：HLF/FR/NFR/CN/STD 間トレース→`trace.json`/`trace.md`
- `index build`：BM25/ANN スケルトン→`index/`（再現性のため seed 固定）
- `lint run`：Lint ルール（`STD-KMK-LINT-01` 準拠）
- `site check`：MkDocs 前のリンク・画像・PlantUML 検証

**注意**：CLI 引数は **後方互換**を守る。破壊的変更は `MIGRATIONS.md` に自動変換手順と共に記載。

### 3.2 テスト/品質
- 単体：語彙・Schema・ID 抽出・グラフ組立の最小ケース充足
- 統合：`/docs` 全体に対する `graph.json`・`trace.json` の **ゴールデン**比較（差分に根拠ログ）
- 変異/故障注入：FM 欠落・ID 重複・循環・誤綴りの検出
- パフォーマンス：PR で 3 分以内、Nightly で 10〜15 分以内を予算化

---

## 4. GitHub Actions 戦略
### 4.1 分解と再利用
- **Composite Actions**（`.github/actions/*`）にセットアップ/検証/生成を分離
- **workflow_call** で `docops_min` と `docops_full` を組み立て
- 依存は **SHA ピン止め**（サードパーティ）＋ Python deps は `uv`/`pip-tools` で lock

### 4.2 ワークフロー雛形
**.github/workflows/docops_min.yml**（PR 最小ゲート）
```yaml
name: docops_min
on:
  pull_request:
    paths:
      - 'docs/**'
      - 'tools/docops_cli/**'
      - 'mkdocs.yml'
jobs:
  lint-and-graph:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-python-uv
      - uses: ./.github/actions/docops-validate   # fm validate + lint
      - uses: ./.github/actions/docops-graph      # graph build (artifacts)
      - uses: ./.github/actions/docops-trace      # trace build (artifacts)
```

**.github/workflows/docops_full.yml**（Nightly 総合）
```yaml
name: docops_full
on:
  schedule:
    - cron: '20 17 * * *'  # JST 02:20 相当
  workflow_dispatch:
jobs:
  full:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-python-uv
      - uses: ./.github/actions/docops-validate
      - uses: ./.github/actions/docops-graph
      - uses: ./.github/actions/docops-trace
      - uses: ./.github/actions/docops-index      # BM25/ANN のスケルトン
      - uses: ./.github/actions/site-check        # MkDocs 事前検証
```

**.github/workflows/publish_pages.yml**（タグで公開）
```yaml
name: publish_pages
on:
  push:
    tags:
      - 'v*.*.*'
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-python-uv
      - uses: ./.github/actions/docops-validate
      - uses: ./.github/actions/docops-graph
      - uses: ./.github/actions/docops-trace
      - uses: ./.github/actions/site-check
      - name: Build MkDocs
        run: mkdocs build --strict
      - name: Upload pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site
      - name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

### 4.3 Composite Action 雛形
**.github/actions/docops-validate/action.yml**
```yaml
name: docops-validate
runs:
  using: 'composite'
  steps:
    - run: uv pip install -e tools/docops_cli[all]
      shell: bash
    - run: python -m kumiki.fm validate docs --schema 99_std/schema.json
      shell: bash
    - run: python -m kumiki.lint run --rules 99_std/STD-KMK-LINT-01.yml
      shell: bash
```

---

## 5. docops.lock（運用固定ポイント）
**目的**：CI/CLI/スキーマの“可搬な固定化”。PR や環境差の影響を最小化。

```yaml
version: 1
schema:
  frontmatter:  "kmk-fm@1.0.0-GA"    # JSON Schema の論理バージョン
  vocabulary:   "STD-KMK-VOC-01@1.0"
cli:
  docops_cli:   "0.3.x"               # 互換範囲。正確な解決は uv/pip-tools lock
outputs:
  graph_format: "1.0"                 # graph.json の互換契約
  trace_format: "1.0"
ci:
  gates:
    pr:       { unknown_refs: "warn",  fail_on_error: true }
    nightly:  { unknown_refs: "error", fail_on_error: true }
    release:  { unknown_refs: "error", fail_on_error: true }
flags:
  fm_flat_only: true
  harvest_inline_ids: true
  obsidian_ignore: [".obsidian/"]
```

**運用**：破壊的変更は `MIGRATIONS.md` に手順とワンショット変換スクリプトを添付。CI は lock 更新がない限り旧仕様で動作。

---

## 6. 標準（STD）・運用（OPS）
- `STD-KMK-00_INDEX.md`：標準の目次と **MVP パック**／拡張パックの範囲定義
- `STD-KMK-VOC-01`：語彙・関係語彙の確定（本ガイド準拠）
- `STD-KMK-TRACE-01`：トレーサビリティ標準（入出力、欠落扱い、差分トレース）
- `STD-KMK-LINT-01`：DocLint ルール（必須キー、語彙制約、リンク検証）
- `STD-KMK-REG-01`：ID レジストリ運用（予約、重複、alias、廃止）
- `STD-KMK-CI-01`：DocOps CI ゲート（PR/Nightly/Release）
- `STD-KMK-MKDOCS-01`：サイト構成・公開標準（構造・目次・検索設定）
- `OPS-KMK-RUNBOOK-01`：障害時 Runbook（Pages 失敗・索引破損・大量 unknown_refs）

---

## 7. 段階的ロードマップ（DoD 付き）
### Phase 0：基盤整備（ブレない土台）
- **成果物**：`docops.lock` 雛形、JSON Schema v1、`STD-KMK-*-01` MVP 版、`docops_min.yml`
- **DoD**：`fm validate` と `lint run` が PR で **安定 3 回連続成功**

### Phase 1：MVP（最小自己適用）
- **範囲**：`graph build`/`trace build`/`site check` を実装、`docops_full.yml` 稼働
- **DoD**：`graph.json` と `trace.json` の **ゴールデン固定**、Nightly 緑連続 7 日

### Phase 2：Hardening（大規模化・互換）
- **範囲**：BM25/ANN スケルトン、ID alias/廃止の自動解決、unknown_refs=error へ昇格
- **DoD**：`MIGRATIONS.md` 実績 1 件以上、`docops.lock` を bump しても過去タグで再現可

### Phase 3：拡張パック（外部適用）
- **範囲**：他リポへの再利用（Composite Actions の独立配布 or public mirror）、MkDocs 検索の日本語最適化、Ops Runbook 整備
- **DoD**：外部 1 リポで導入→PR/Release サイクル完走、SLA（PR 3 分/ Nightly 15 分）達成

---

## 8. “後戻り”を抑える設計テクニック
1. **契約先行**：先に JSON Schema・graph.json/trace.json の **I/O 契約**を決め、実装は後追い。
2. **分割可能なワークフロー**：Composite に分け、個別に再実行しやすくする（デバッグ効率↑）。
3. **ゴールデン＋差分根拠**：差分時に“どの文から、そのリンクを推定したか”の根拠スニペット出力。
4. **Feature Flags**：`docops.lock` の flags で新機能を段階的に有効化（canary）
5. **警告→エラー昇格**：運用影響を見ながらゲート強度を上げる（Phase ごとに昇格）
6. **ピン止めと Mirrors**：外部アクション/依存は SHA ピン止め、公開はタグで凍結→再現性確保。

---

## 9. 既知の落とし穴と対策
- **巨大ワークフロー**：1 ファイルに詰めない。`workflow_call` で呼ぶ。
- **未知引数のドリフト**：CLI の引数増減は Deprecation 期間を取り、`--help` と `MIGRATIONS.md` を必ず更新。
- **unknown_refs 大量発生**：ID 抽出の正規表現を本文対応（段落 ID）＋ alias ルール導入。
- **Pages “Not Found”/壊れリンク**：`site check` で docs_dir と相対リンクを事前検証。
- **検索の日本語未ヒット**：MkDocs のプラグイン/Tokenizer 設定を Phase 3 で導入（Kuromoji など）。

---

## 10. 次アクション（直近 1〜2 週間）
- [ ] `STD-KMK-00_INDEX.md` に MVP パックを確定（VOC/TRACE/LINT/REG/CI/MKDOCS）
- [ ] JSON Schema v1 を `99_std/` に配置、`fm validate` を実装
- [ ] `docops.lock` 雛形を作成し CI で読み込む
- [ ] Composite Actions：`setup-python-uv` / `docops-validate` / `docops-graph` / `docops-trace`
- [ ] `docops_min.yml` を main PR ゲートに組込み
- [ ] ゴールデンテスト基盤（graph/trace）を tests/ に追加
- [ ] `MIGRATIONS.md` 雛形作成（テンプレ含む）

---

### 付録 A：`MIGRATIONS.md` テンプレ（抜粋）
```
# MIGRATION: kmk-fm@1.0.0 → 1.1.0
- 変更種別: 互換/非互換（破壊的）
- 影響範囲: FrontMatter キー `derives_from` の導入、`evidence_of` 廃止
- 自動変換: tools/scripts/migrate_fm_1_0_to_1_1.py
- ロールバック: 変換前のバックアップを _backup/ に保存
- 検証: fm validate / lint run / graph build の 3 点が緑なら完了
```

### 付録 B：ゴールデンテストの設計指針
- `tests/golden/docs_small/*` に最小ドキュメント集を保持
- `pytest -k golden` で `graph.json`/`trace.json` を比較、差分は unified diff＋根拠スニペット出力

---

これで「後戻り」を抑えつつ、**スキーマ→CLI→CI→サイト**の順で外周から内側へ固め、自己適用を安全に進められます。

