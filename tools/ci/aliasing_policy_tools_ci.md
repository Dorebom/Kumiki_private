
# BGローカルID → 仮想ノード（FQID）化・エイリアス解決（tools/ci 版）

- 解析スクリプト: `tools/ci/bg_aliasing.py`
- 生成物:
  - `artifacts/indexing/id_aliases.json` … `{"BG-KMK-01": "CR-KMK-00#BG-KMK-01", ...}`
  - `artifacts/indexing/local_bg_index.json` … 抽出索引
  - `artifacts/logs/bg_alias_resolver.lint.json` … `satisfies`→`derives_from` 提案（ファイル変更はしない）

## kumiki_ci_publish_plus.yml への組み込み（例）

```yaml
env:
  ARTIFACTS: ${{ github.workspace }}/artifacts

jobs:
  kumiki_ci_publish_plus:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Prepare artifacts dirs
        run: mkdir -p "$ARTIFACTS/indexing" "$ARTIFACTS/logs"

      - name: Build BG alias map (tools/ci)
        run: |
          python tools/ci/bg_aliasing.py \
            --docs-root docs \
            --out-dir "$ARTIFACTS/indexing" \
            --lint-report "$ARTIFACTS/logs/bg_alias_resolver.lint.json"

      # 以降の trace_emit / graph builder で id_aliases.json を参照
      # 例: GLOBAL_NODES.get(ref) が失敗したら、aliasで解決を試す:
      #   alias = json.load(open("$ARTIFACTS/indexing/id_aliases.json"))
      #   ref = alias.get(ref, ref)

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: kumiki-docops
          path: |
            ${{ env.ARTIFACTS }}/indexing/**
            ${{ env.ARTIFACTS }}/logs/**
```
