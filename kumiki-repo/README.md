# Kumiki — ドロップイン DocOps アドオン

## 概要
**Kumiki** は、既存のソフトウェア開発リポジトリに *あと付け* できる **DocOps（Documentation Operations）** 基盤です。
リポジトリ直下に **サブモジュールとして配置**することで、現在のコード／設計ドキュメントの配置を変えずに、
**FrontMatter規約に基づく自動検証・トレース・インデクシング**を追加します。

## コンセプト
- **非侵襲（Non‑intrusive）**：既存の `.git` / `.github` / フォルダ構成に干渉しない。
- **宣言的（Declarative）**：`sources.yml` で「どこを管理対象にするか」を記述して、Kumiki が巡回。
- **一貫性（Consistency）**：FrontMatter を **フラット1段**＋**単一 `canonical_parent`**＋**固定語彙**で統一。
- **安全な公開（Safe Publishing）**：`public-*` ブランチのみ公開し、`publish.yml` で禁止パスをガード。
- **拡張性（Extensible）**：Graph/Index/レポートはプラガブル。Embedding/ANN/サイト出力も後付け可能。

## 特徴（ハイライト）
- 🧩 **ドロップイン**：`kumiki/` をサブモジュール追加するだけ。既存の `docs/` や `apps/*/docs/` はそのまま。
- 🔒 **干渉ゼロ**：CI は **親リポのルート**のみで実行。Kumiki 側は **コンポジットアクション**で提供。
- 📐 **FrontMatterポリシー**：フラット1段／配列は**文字列IDのみ**／`canonical_parent` は**必ず1つ**／語彙は固定。
- 🕸️ **Graph/Trace**：relations（`refines / derives_from / satisfies / depends_on / integrates_with / constrains / conflicts_with / supersedes`）
  から有向グラフを構築し、**孤立・循環・到達不能**を検出。差分トレースのレポート化も可能。
- 🔎 **Index/Search**：TF‑IDF による簡易検索。Embedding/ANN は**拡張ポイント**として後付け。
- 🧪 **最小ゲートCI**：PRで **スキーマ検証／語彙チェック／単一親チェック** を自動実行（失敗でブロック）。
- 🚧 **公開ミラーの安全化**：`public-*` だけを公開し、`publish.yml` の**禁止パス**で漏れ防止。
- 🧰 **FM注入ツール**：既存MDに FrontMatter が無くても、スクリプトで**最小FMを自動付与**。
- 🧭 **モノレポ対応**：`apps/*/docs/` と `packages/*/docs/` を横断管理。Obsidian (`.obsidian/`) は既定で除外。

---

## 🧭 クイックスタート（サブモジュール方式で親リポに導入）

> 親リポ直下に `kumiki/` を追加します。チームでは clone 時に `--recurse-submodules` を推奨。

```bash
# 1) 追加（安定タグへ固定する運用を推奨）
git submodule add https://github.com/your-org/kumiki.git kumiki
(cd kumiki && git checkout v0.1.0)
git add .gitmodules kumiki
git commit -m "Add kumiki submodule (pinned to v0.1.0)"

# 2) 既存ドキュメントの探索範囲を設定（親リポ側のパスを書く）
$EDITOR kumiki/config/sources.yml

# 3) （任意）FrontMatter が無い .md に最小FMを一括付与
python kumiki/scripts/inject_frontmatter.py

# 4) ローカル検証
pip install -r kumiki/cli/requirements.txt
python kumiki/cli/kumiki_cli.py --check --graph
# 例: 検索
python kumiki/cli/kumiki_cli.py --search "FrontMatter"
```

### 親リポのCI（ルートで実行）

`.github/workflows/kumiki.yml` を**親リポ**に置き、ネストした **コンポジットアクション**を呼び出します。

```yaml
name: Kumiki checks
on:
  pull_request:
    paths:
      - 'kumiki/**'
      - 'docs/**'
      - 'apps/**/docs/**'
      - 'packages/**/docs/**'
  workflow_dispatch:

jobs:
  kumiki:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true
          fetch-depth: 0
      - name: Kumiki check
        uses: ./kumiki/actions/check
```

---

## ⚙️ 設定ファイルの要点

### `config/docops.lock`
- **FrontMatter規約**を定義（フラット1段、単一 `canonical_parent`、許可 relations など）
- 例外/禁止フィールド、バリデーション項目を列挙

### `config/_vocabulary.yml`
- relations の語彙集合を定義（上流/横方向など）

### `config/sources.yml`
既存リポ内の**探索範囲/除外**を宣言します。Obsidian は既定で除外。

```yaml
targets:
  - root: docs
    include: ["**/*.md"]
    exclude: ["**/.obsidian/**"]
    default_canonical_parent: "RS-00_overview"

  - root: apps
    include: ["*/docs/**/*.md", "*/README.md"]
    exclude: ["**/node_modules/**", "**/dist/**"]

  - root: packages
    include: ["*/docs/**/*.md", "*/README.md"]
    exclude: ["**/node_modules/**", "**/dist/**"]

  - root: .
    include: ["ARCHITECTURE.md", "CONTRIBUTING.md"]
```

### `config/publish.yml`（公開ブランチのガード）
- `public-*` ブランチにおける**禁止パス**を列挙し、CIで混入を検出・失敗させます。

```yaml
forbid_in_public:
  - "docs/private/**"
  - "**/.obsidian/**"
  - "**/*.key"
  - "**/*.pem"
  - "secrets/**"
```

---

## 🧩 FrontMatter 仕様（必須フィールド）

- `id`（一意）、`title`、`canonical_parent`（単一値）  
- relations は**配列（文字列IDのみ）**で記載：  
  `refines`, `derives_from`, `satisfies`, `depends_on`, `integrates_with`, `constrains`, `conflicts_with`, `supersedes`

```md
---
id: RS-00_overview
title: 要求仕様 概要
canonical_parent: RS-00_overview
refines: []
derives_from: []
satisfies: []
depends_on: []
integrates_with: []
constrains: []
conflicts_with: []
supersedes: []
---

本文……
```

> **推奨**: 要求仕様のID深さは**最大4層**まで（詳細設計での深さを確保）。

---

## 🛠️ CLI コマンド

```bash
# 1) スキーマ検証・語彙チェック・単一親チェック
python kumiki/cli/kumiki_cli.py --check

# 2) グラフ統計（孤立/到達不能の検出）
python kumiki/cli/kumiki_cli.py --graph

# 3) 簡易検索（TF-IDF）
python kumiki/cli/kumiki_cli.py --search "クエリ文字列"
```

- 成果物：`reports/`（レポート）, `index/`（検索インデックス）に出力します。  
- Embedding/ANN は**拡張ポイント**として後付け可能（プラガブル設計）。

---

## 🚀 Kumiki 自身のドキュメントを Kumiki で管理（ドッグフード）

このリポジトリの `docs/` は Kumiki の開発設計・テスト・ユーザーガイドの**単一ソース**です。  
PRでは `ci.yml` が検証＆サイトをArtifact化、`main`では `pages.yml` が GitHub Pages に公開します。

---

**Happy DocOps!** 🎋
（Kumiki = 組み木。既存リポへ“噛み合わせる”ように後付けできるのがコンセプトです。）

_最終更新: 2025-08-31_
