---
id: STD-KMK-VOC-01
title: 語彙・関係語彙標準（Kumiki）
version: "1.0"
status: draft
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01"]
---

# 1. 目的と適用範囲
Kumiki プロジェクトの **FrontMatter（FM）内で許可される語彙と関係語彙** を定義する。  
FM はフラット構造（ネスト禁止／配列はID文字列のみ）である前提（参照: STD-KMK-FM-01）。  
対象文書: `CR, RS, HLF, FR, NFR, CN, DD, TS, ADR, OPS, STD` を含むすべて。

# 2. 語彙一覧（正規キー）
> ここに **未定義キーの追加は禁止**。必要な場合は本標準を改版する。

| 区分 | キー | 型 | 多重度 | 説明（要点） |
|---|---|---|---|---|
| 基本 | `id` | string | 1 | 文書の一意ID。ASCII・大文字・数字・ハイフン・小数点（小節）に限定（参照: STD-KMK-ID-01）。 |
| 基本 | `title` | string | 1 | 文書の題名。短く具体的に。 |
| 基本 | `version` | string | 1 | 文書版（例: `"1.0"`）。Schema変更時は上位桁。 |
| 基本 | `status` | enum | 1 | `draft | review | approved | deprecated` のいずれか。 |
| 階層 | `parent` | string | 1 | 正規の親（canonical）。**必ず1つ**。 |
| 階層 | `children` | string[] | 0..n | 子文書のID配列。粒度（`FR-xx`/`FR-xx.x`）を区別して列挙。 |
| 上流 | `refines` | string[] | 0..n | 上位を洗練（抽象→具体）。上流接続。 |
| 上流 | `satisfies` | string[] | 0..n | 上位要求・根拠を充足／遵守。上流接続。 |
| 横断 | `depends_on` | string[] | 0..n | 成立に依存（根拠・構成要素・ADR）。 |
| 横断 | `integrates_with` | string[] | 0..n | 連携して価値を成す（相互運用）。 |
| 横断 | `constrains` | string[] | 0..n | 相手の設計自由度を制約。 |
| 横断 | `conflicts_with` | string[] | 0..n | 両立不可または前提矛盾。 |
| 横断 | `supersedes` | string[] | 0..n | 旧文書を置換（置換元IDを列挙）。 |
| 補足 | `note` | string | 0..1 | 短い補足。長文は本文へ。 |

**禁止事項**  
- ネスト（オブジェクト）・キー付き配列・リンク記法（`[text](path)`）
- 語彙外キー（下 §5 の別名/同義語も禁止）

# 3. 関係語彙の意味と向き
- `parent`/`children` は **階層的包含**（章立て・粒度差）。`parent` は 1 つのみ。  
- `refines` は **抽象→具体の洗練**。例: `HLF` → `FR`。  
- `satisfies` は **準拠・充足**。例: `FR/NFR` が `HLF/CR/法規/ADR` を満たす。  
- `depends_on` は **必要条件**。例: `FR-XX` が `ADR-016` に依存。  
- `integrates_with` は **相互連携**。例: `DD-API-01` が `DD-DATA-02` と統合して機能。  
- `constrains` は **制約付与**。例: `NFR-RT-01` が `DD-CTRL-01` を制約。  
- `conflicts_with` は **同時成立不可**。レビューで解消か分岐（派生）を検討。  
- `supersedes` は **置換（新→旧）**。旧側は `status: deprecated` を併記。

> **注意**: 本プロジェクトでは **`derives_from` は採用しない**。根拠参照は `satisfies` または `depends_on` で表現する（単語の重複・曖昧化を排除）。

## 3.1 方向性の図示（概念）
```
上流:  HLF/CR/ADR
          ^    ^
        (satisfies / refines)
          |    |
下流:  FR/NFR ——→ DD ——→ TS
         |        ↑
         └ depends_on / constrains / integrates_with / conflicts_with
```

# 4. カーディナリティと整合
- `parent` = **1**、`children` = **0..n**。親子は **相互整合**（CIで検査）。  
- 各文書は `refines`/`satisfies`/`children` の **いずれかで接続**（孤立ノード禁止）。  
- 参照先IDは **必ず実在**（unknown_refs=0を目標）。`TBD` は一時許容だが `approved` 前に解消。

# 5. 別名・同義語の扱い（禁止→正規語彙へ統一）
| 禁止ワード | 使わない理由 | 置き換え（正規） |
|---|---|---|
| `derives_from` | `satisfies`/`depends_on` と意味重複・曖昧 | `satisfies` または `depends_on` |
| `implements` | 実装概念と要件準拠が混同 | `satisfies` |
| `blocks` | 片方向の否定制約で曖昧 | `constrains` または `conflicts_with` |
| `relates_to` | 意味が広すぎる | 該当する正規語彙に分解 |
| `based_on` | 系譜/根拠が曖昧 | `depends_on` |
| `replaces` | 置換語彙が二重化 | `supersedes` |

# 6. 例（最小FM断片）
## 6.1 FR が HLF を満たし、ADRに依存
```yaml
---
id: RS-FR-12
title: ログ収集（最小オーバーヘッド）
version: "1.0"
status: review
parent: RS-FR
satisfies: ["HLF-OBS-01"]
depends_on: ["ADR-016"]
children: ["RS-FR-12.1"]
---
```

## 6.2 NFR が DD を制約し、TS へ入口トレース
```yaml
---
id: RS-NFR-01
title: 1kHz 制御ループのジッタ
version: "1.1"
status: approved
parent: RS-NFR
constrains: ["DD-CTRL-01"]
children: ["TS-RT-01"]
---
```

## 6.3 ADR が旧設計文書を置換
```yaml
---
id: ADR-016
title: HID/TID ハイブリッド ID 方式
version: "1.0"
status: approved
supersedes: ["ADR-009"]
---
```

# 7. Lint 規定（VOC系ルールの最小セット）
- **VOC-001**: 語彙外キーの禁止（表 §2 のみ許可）。  
- **VOC-002**: `parent` は **1つだけ**。複数・空文字はエラー。  
- **VOC-003**: `children`/関係配列の要素は **ID文字列のみ**（オブジェクト不可）。  
- **VOC-004**: 別名/同義語（§5）は **エラー**。自動提案で正規語彙へ修正。  
- **VOC-005**: `refines`/`satisfies`/`children` のいずれも無い場合は **警告**（孤立）。  
- **VOC-006**: `supersedes` を持つ旧文書は `status: deprecated` を推奨（警告）。

# 8. JSON Schema（参考・機械検証の叩き台）
> スキーマは **フラット構造**・**ID配列のみ** を強制する簡易版（実装は DocLint に委譲）。
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "id":        { "type": "string" },
    "title":     { "type": "string" },
    "version":   { "type": "string" },
    "status":    { "enum": ["draft","review","approved","deprecated"] },
    "parent":    { "type": "string" },
    "children":  { "type": "array", "items": { "type": "string" } },
    "refines":   { "type": "array", "items": { "type": "string" } },
    "satisfies": { "type": "array", "items": { "type": "string" } },
    "depends_on":{ "type": "array", "items": { "type": "string" } },
    "integrates_with": { "type": "array", "items": { "type": "string" } },
    "constrains":{ "type": "array", "items": { "type": "string" } },
    "conflicts_with":{ "type": "array", "items": { "type": "string" } },
    "supersedes":{ "type": "array", "items": { "type": "string" } },
    "note":      { "type": "string" }
  },
  "required": ["id","title","version","status"]
}
```

# 9. 運用メモ
- 新語彙の提案は **本標準の改版PR** として提出（採用は合意制）。  
- 語彙が迷う場合は **最も厳密な意味**に寄せて分解（例: `relates_to` → `depends_on`+`integrates_with`）。  
- Obsidian での表示は短く、説明は本文側に置く。

# 変更履歴
- 1.0: 初版（FM正規キー・関係語彙の意味/向き/カーディナリティ/禁止別名・Lint 最小セット）。
