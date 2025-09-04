---
id: STD-KMK-MKDOCS-01
title: サイト構成・公開標準（Kumiki）
version: "1.0"
status: draft
parent: STD-KMK-00_INDEX
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01", "STD-KMK-TRACE-01", "STD-KMK-LINT-01", "STD-KMK-REG-01", "STD-KMK-CI-01"]
---

# 1. 目的と適用範囲
Kumiki ドキュメントサイトの **MkDocs 構成・検索・公開** の最小～推奨規定を定める。  
対象: 全ドキュメント（Markdown + YAML FrontMatter）、ならびに `mkdocs.yml`。

# 2. 基本方針（必要十分）
- **単純なルート**: `docs_dir: docs` を標準化。  
- **日本語検索**: `search` プラグインに `lang: [ja, en]` を指定。  
- **安定ナビ**: 先頭数字で並び順を固定（`00_`, `01_`, …, `90_`）。各セクションに `_index.md` を置き、`nav` から参照。  
- **相対リンク**: 本文のリンクは相対パスで統一（移動耐性）。  
- **除外の明示**: `.obsidian/`, `artifacts/`, 生成物はビルド対象外。

# 3. `mkdocs.yml` 最小テンプレ
```yaml
site_name: Kumiki Docs
site_url: https://<org>.github.io/<repo>/
docs_dir: docs

theme:
  name: material
  language: ja
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.indexes
    - content.code.copy

plugins:
  - search:
      lang: [ja, en]
      separator: "[\\s\\-]+"   # 英字・数字は分割、日本語は形態素に依存

markdown_extensions:
  - admonition
  - footnotes
  - tables
  - toc:
      permalink: true
  - attr_list
  - pymdownx.details
  - pymdownx.superfences

nav:
  - ホーム: index.md
  - コンセプト: 00_concept/_index.md
  - 要求仕様: 02_requirements/_index.md
  - 設計: 03_design/_index.md
  - テスト: 50_test/_index.md
  - トレース: 70_trace/_index.md
  - 運用: 80_ops/_index.md
  - 標準: 90_standards/_index.md
```

> **備考**: 具体ファイルは各 `_index.md` 内から相対リンクで列挙。セクション直下に `index.md` を置く形でもよいが、**命名の一貫性**を優先する。

# 4. ディレクトリ構成の推奨
```
docs/
  index.md                       # トップ
  00_concept/_index.md
  02_requirements/_index.md      # RS/HLF/FR/NFR/CN の索引
  03_design/_index.md            # DD 系
  50_test/_index.md              # TS 系
  70_trace/_index.md             # Trace の概要・断絶一覧
  80_ops/_index.md               # Runbook/SOP
  90_standards/_index.md         # STD インデックス（= STD-KMK-00_INDEX.md でも可）
```

# 5. 検索と言語設定（日本語）
- `theme.language: ja` と `plugins.search.lang: [ja, en]` を**両方**設定。  
- `separator` は `"[\\s\\-]+"` を推奨。日本語の分割はテーマ側の言語サポートに依存。  
- 既知の弱点（複合語のヒット率低下）は見出し/要約に **形態素を含む語**（例: 「トレース」「トレーサビリティ」）を併記して補う。

# 6. リンク・画像・添付の規定
- **相対リンク**: `../` を使い階層間リンク。ルート相対 `/` は禁止（サイトURL変更に弱い）。  
- **画像**: `docs/assets/img/` に置き、`![alt](../../assets/img/xxx.png)` で参照。  
- **図（PlantUML）**: 生成画像は `assets/diag/`。生成スクリプトは CI で実行可。

# 7. 除外・ウォッチ
- ビルド除外: `.obsidian/`, `.git/`, `artifacts/`, `site/`, `venv/`。  
- ウォッチ（ローカル開発）では `.obsidian/` を無視してホットリロードの無駄を減らす。

# 8. 公開（GitHub Pages）
- CI（参照: `STD-KMK-CI-01`）で **PR/Nightly** はビルドのみ、**Release** で `actions/deploy-pages@v4` により公開。  
- `site_url` を正しく設定（リポジトリ移設時の 404 回避）。  
- 404 ページ `docs/404.md` を用意（最低限で可）。

# 9. 失敗の典型と対処
- **docs_dir 不一致**: `mkdocs.yml` と実パスを合わせる。  
- **リンク切れ**: `linkcheck` の出力で検出（相対パスの見直し）。  
- **日本語検索が弱い**: `lang` の確認、見出しに代表語を併記、`toc` を活用。

# 10. 変更履歴
- 1.0: 初版（最小テンプレ・日本語検索・ディレクトリ/ナビ規定・公開フロー）。
