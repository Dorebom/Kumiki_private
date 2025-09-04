---
id: STD-KMK-REG-01
title: IDレジストリ標準（Kumiki）
version: "1.0"
status: draft
parent: STD-KMK-00_INDEX
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01", "STD-KMK-TRACE-01", "STD-KMK-LINT-01"]
---

# 1. 目的と適用範囲
Kumiki プロジェクトにおける **ID レジストリ（`id_registry.yml`）** の構造・運用・CI検証を定義する。  
対象は全ドキュメント（`CR, RS, HLF, FR, NFR, CN, DD, TS, ADR, OPS, STD`）。**FM（FrontMatter）がメタの正**、**レジストリは索引の正**とする。

# 2. 原則（必要十分）
- **一意性の単一責務**: ID のユニーク性をレジストリで集中管理（重複検出の第一義）。
- **FM一致**: レジストリの `title/status` は FM と一致させる（差分はCIで警告）。
- **最小情報**: 必須は `path/title/status` の3点＋任意の `tags/type`。過剰なメタはFMへ。
- **自動生成優先**: 人手編集は最小化。CLIで追加/更新し、PRでレビュー。

# 3. レジストリの配置と形式
- **配置**: リポジトリ直下に `id_registry.yml`（UTF-8）。
- **形式**: **トップレベルがIDのマップ**。各IDが 1 つのレコードを指す。
- **相対パス**: `path` はリポジトリルートからの相対（`/` 区切り）。

## 3.1 スキーマ（YAML 抜粋）
```yaml
# id_registry.yml
RS-FR-01:
  path: docs/02_requirements/RS-FR-01.md
  title: センサ入力の正規化
  status: review
  type: FR          # 任意: FR/NFR/HLF/DD/TS/ADR/STD/OPS/CN...
  tags: [sensor, io]  # 任意: 文字列の配列（自由語彙）

STD-KMK-FM-01:
  path: docs/90_standards/STD-KMK-FM-01.md
  title: FrontMatter 運用標準（Kumiki）
  status: draft
  type: STD
```

### 3.2 JSON Schema（参考・検証器向け）
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "patternProperties": {
    "^([A-Z]{2,5})(?:-([A-Z0-9]{2,8}))?(?:-([A-Z]{2,8}))?-([0-9]{2,})(?:\.[0-9]+)*$": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "path":  { "type": "string" },
        "title": { "type": "string" },
        "status":{ "enum": ["draft","review","approved","deprecated"] },
        "type":  { "type": "string" },
        "tags":  { "type": "array", "items": { "type": "string" } }
      },
      "required": ["path","title","status"]
    }
  }
}
```

# 4. CI チェック（REG 系）
- **REG-001 (error)**: **ID 重複**（同一IDが複数ファイルに存在/FΜと不一致）。
- **REG-002 (error)**: **未登録**（FMに存在するIDがレジストリに無い／逆も）。
- **REG-003 (error)**: **パス不一致**（レジストリ `path` と実ファイルが不一致・存在しない）。
- **REG-004 (warn)**: **メタ差分**（`title/status` がFMと一致しない）。
- **REG-005 (warn)**: **型不整合**（`type` が推測TYPEと矛盾、例: `RS-FR-01` なのに `type: DD`）。
- **REG-006 (info)**: **未参照**（サイト `nav` 到達不能 or 参照入出次数=0）。

# 5. 運用フロー（推奨）
1) **新規文書作成** → FM に `id/title/version/status` を記述。  
2) **レジストリ反映** → CLI で `id_registry.yml` を自動更新（人手で直接編集しない）：  
   ```bash
   python tools/ci/reg_sync.py add docs/02_requirements/RS-FR-01.md
   ```
3) **CI 検証** → Lint（`LINT-REG-040..`）で一意性/整合性を確認。  
4) **レビュー** → PRで差分（CSV/JSON）を確認して承認。

# 6. 変更と廃止
- **移動**: ファイル移動時は CLI で `path` 更新。履歴保持のため ID は変更しない。  
- **置換**: 大改変は **新ID** を発行し、旧IDのFMに `status: deprecated` と `supersedes: ["<新ID>"]`。レジストリも更新。  
- **削除**: 削除時はレジストリから削除。欠番はそのまま（再利用禁止）。

# 7. 生成物（REG系アーティファクト）
- `artifacts/reg/registry.csv` — レジストリの正規化CSV。  
- `artifacts/reg/missing_in_registry.csv` — FM存在だがレジ未登録。  
- `artifacts/reg/missing_in_fs.csv` — レジ登録だがファイル欠落。  
- `artifacts/reg/drift.csv` — `title/status` の **FM↔REG** 差分。

# 8. CLI インターフェース（叩き台）
```bash
# レジストリに追加/更新（FMから吸い上げ）
python tools/ci/reg_sync.py add docs/90_standards/STD-KMK-REG-01.md

# 一括同期（docs配下を走査して再生成）
python tools/ci/reg_sync.py rebuild --docs-root docs --out id_registry.yml

# チェックのみ
python tools/ci/reg_sync.py check --registry id_registry.yml --docs-root docs --report artifacts/reg
```

# 9. ベストプラクティス
- **レビューの視点**: IDの一意性・pathの正しさ・`status` の妥当性（draft/approved等）。  
- **タグ活用**: クエリやナビ生成に使う軽量メタ。FMより**緩く**使える。  
- **スキーマの節度**: レジストリに過剰メタを持たせない（冪等性と再現性を優先）。

# 10. 付録：最小テンプレ
```yaml
# id_registry.yml (minimum)
STD-KMK-00_INDEX:
  path: docs/90_standards/STD-KMK-00_INDEX.md
  title: Standards Index（Kumiki 標準の親）
  status: draft

STD-KMK-REG-01:
  path: docs/90_standards/STD-KMK-REG-01.md
  title: IDレジストリ標準（Kumiki）
  status: draft
```
# 変更履歴
- 1.0: 初版（構造・CIチェック・運用フロー・生成物・CLI叩き台）。
