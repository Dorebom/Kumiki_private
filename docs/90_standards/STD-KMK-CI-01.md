---
id: STD-KMK-CI-01
title: DocOps CIゲート標準（Kumiki）
version: "1.0"
status: draft
parent: STD-KMK-00_INDEX
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01", "STD-KMK-TRACE-01", "STD-KMK-LINT-01", "STD-KMK-REG-01"]
---

# 1. 目的と適用範囲
Kumiki リポジトリの **文書系CI（DocOps）** のゲート方針・ジョブ構成・しきい値を定義する。対象は Markdown + YAML FrontMatter の全ドキュメントと、その派生物（Trace/MkDocs サイト/レジストリ等）。

# 2. ゲート方針（PR / Nightly / Release）
| ゲート | 目的 | 必須合格条件（Fail条件） |
|---|---|---|
| **PR** | 変更の健全性 | Lint=error0 / unknown_refs=0 / 入口トレースあり / MkDocsビルド成功 / リンク切れ0 / レジストリ整合 |
| **Nightly** | 網羅検査 | PR条件 + 循環0 / 孤立0 / 差分ログ出力 / サイト全体リンクチェック |
| **Release** | 品質固定 | Nightly条件 + warn0 / deprecated参照0 / 生成物の整合（hash/サイズ） |

- 重大度: `error` でゲート停止、`warn` は Nightly まで許容、Release は原則禁止。

# 3. しきい値（既定値・設定で上書き可）
```yaml
# tools/docops_cli/config/gates.yml
version: 1
thresholds:
  unknown_refs: 0
  max_cycles: 0
  max_orphans: 0
  max_broken_links: 0
  require_ts_reachability: true     # FR/NFR→TS 到達必須
  require_parent_singleton: true    # 親は1つ
severities:
  release_warn_is_error: true
artifacts:
  retention_days: 7
```

# 4. CI ジョブ構成（推奨順）
1. **setup**: Python セットアップ + 依存取得（pip キャッシュ）。  
2. **doclint**: `STD-KMK-LINT-01`の FM/VOC/TRACE/ID/REG/DOCS ルールで Lint。  
3. **trace**: FM→Graph 生成、入口/出口/孤立/循環チェック、差分（inherit+delta）出力。  
4. **build**: MkDocs ビルド（日本語検索設定を含む）→ `site/` 生成。  
5. **linkcheck**: 生成サイトのリンク検査（内部相対リンク中心）。  
6. **publish**（releaseのみ）: GitHub Pages へデプロイ。  
7. **upload-artifacts**: Lint/Trace/Link のレポートと `graph.json` を保存。

# 5. 成果物（保存パス）
- `artifacts/lint/report.json` / `report.sarif`  
- `artifacts/trace/graph.json` / `trace_index.csv` / `delta.csv`  
- `artifacts/linkcheck/broken_links.csv`  
- `artifacts/site/`（必要に応じて zip 圧縮）

# 6. GitHub Actions 雛形（最小）
```yaml
name: docops_min
on:
  pull_request:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  docops:
    runs-on: ubuntu-latest
    concurrency:
      group: docops-${{ github.ref }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install deps
        run: |
          python -m pip install -U pip
          pip install -r tools/docops_cli/requirements.txt

      - name: Lint (FM/VOC/TRACE/ID/REG/DOCS)
        run: |
          python tools/ci/doclint.py --root docs --out artifacts/lint/report.json --format json \
            --config tools/docops_cli/config/lint_rules.yml

      - name: Trace build
        run: |
          python tools/ci/trace.py build --docs-root docs --out artifacts/trace/graph.json

      - name: Trace suggest (delta/table)
        run: |
          python tools/ci/trace.py suggest --docs-root docs --out artifacts/trace

      - name: MkDocs build
        run: |
          mkdocs build --strict

      - name: Link check (internal)
        run: |
          python tools/ci/linkcheck.py --site-dir site --out artifacts/linkcheck/broken_links.csv

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: docops-artifacts
          path: |
            artifacts/lint/**
            artifacts/trace/**
            artifacts/linkcheck/**
```

# 7. 必須設定/権限
- Pages deploy（release時）には `actions/deploy-pages@v4` と `pages: write` 権限が必要。  
- `mkdocs.yml` の `nav` と `docs_dir` を正しく設定。日本語検索は拡張有効化。  
- `.doclintignore` / `.traceignore` で `.obsidian/` 等の除外を明示。

# 8. 失敗時の扱い
- **PR**: `error` でブロック、`warn` はマージ可だが自動コメントで指摘。  
- **Nightly**: すべてのルール実行。`warn` も Slack/メールへ通知。  
- **Release**: `warn=0` を満たさない限りタグ禁止。

# 9. ベストプラクティス
- 小さく頻繁にマージ（トレース断絶を早期に検知）。  
- 大量改編は 2 段階（FM→本文）で実施し、先に FM を整合させる。  
- 生成物の**差分レビュー**を習慣化（`delta.csv`/`broken_links.csv`）。

# 10. 変更履歴
- 1.0: 初版（ゲート条件・ジョブ構成・しきい値・Actions雛形・失敗時方針）。
