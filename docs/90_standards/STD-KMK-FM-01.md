---
id: STD-KMK-FM-01
title: FrontMatter 運用標準（Kumiki）
version: "1.0"
status: draft
---

# 目的と適用範囲
Kumiki プロジェクトにおける Markdown 文書の YAML FrontMatter（以下、FM）の **必須・推奨ルール**を定める。Obsidian 互換を前提とし、要求仕様（RS）、上位要件（HLF）、機能要件（FR）、非機能要件（NFR）、コンセプト要件（CN）、標準（STD）、設計（DD）、テスト（TS）など、**すべてのドキュメント種別**に適用する。

# 基本方針（簡潔・必要十分）
- **フラット構造**: FM は 1 階層のみ。オブジェクト/ネスト禁止。
- **配列は文字列 ID のみ**: 配列要素は **ID 文字列**に限定。オブジェクトやキー付き要素禁止。
- **最小必須キー**: `id`, `title`, `version`, `status`。
- **関係語彙は固定**: `refines`, `satisfies`, `depends_on`, `integrates_with`, `constrains`, `conflicts_with`, `supersedes`, `children`, `parent`。
- **空フィールドは省略**: 値が空の場合、そのキーは **書かない**。

# キー仕様
- `id`: 文書の一意 ID（例: `RS-NFR-06`, `HLF-CTRL-01`, 本標準は `STD-KMK-FM-01`）。
- `title`: 文書の題名（短く具体的に）。
- `version`: 文書版（例: `"1.0"`）。Schema 変更を伴う場合は上位桁を上げる。
- `status`: `draft | review | approved | deprecated` のいずれか。
- `parent`: **正規の親（canonical parent）を 1 つ**だけ記載。
- `children`: 子文書の ID 配列。粒度区分（`FR-xx` と `FR-xx.x` 等）を区別して列挙。
- `refines`:（上流）より抽象の上位文書を洗練する関係。
- `satisfies`:（上流）上位要求や根拠に**準拠/充足**する関係。
- `depends_on`:（横）成立に**依存**する根拠/構成要素/ADR 等。
- `integrates_with`:（横）**連携**して価値を成す関係。
- `constrains`:（横）他文書の解空間を**制約**する関係。
- `conflicts_with`:（横）両立しない、前提が矛盾する関係。
- `supersedes`:（横）旧文書を**廃し置換**する関係（置換元を列挙）。
- `note`: 任意の短い補足（自由記述）。長文は本文側へ。

> 参考：`derives_from` は **語彙外**。根拠参照は `satisfies`/`depends_on` で表現する。

# 関係ルール
- **親は 1（必須）**: `parent` は 1 つのみ。相互整合（親→子・子→親）は CI で検証。
- **孤立ノード禁止**: `refines`/`satisfies`/`children` のいずれかで**少なくとも 1 つ**接続。
- **参照表記**は **ID のみ**（Markdown リンクは FM では禁止）。
- **未確定参照**は一時的に `TBD` を許容（`status: approved` に上げる前に必ず解消）。

# バリデーションと CI
- Lint で以下をチェック：
  1) 必須キーの存在（`id/title/version/status`）。
  2) フラット構造（ネスト禁止）。
  3) 語彙外キーの検出（警告）。
  4) `parent` は 1 つのみ。
  5) ID 参照の実在性（`unknown_refs` 検出）。
  6) 孤立ノード検出（上流/下流の接続）。
  7) `status: deprecated` が参照されている場合は警告。
- `approved` へ昇格する条件：未確定参照の解消・CI/Lint をすべて Pass。

# 最小例（この標準自身）
```yaml
---
id: STD-KMK-FM-01
title: FrontMatter 運用標準（Kumiki）
version: "1.0"
status: draft
---
```

# 記入例（要求仕様の断片）
```yaml
---
id: RS-NFR-06
title: 拡張容易性（Extensibility）
version: "1.2"
status: review
parent: RS-NFR
refines: ["RS-NFR"]
depends_on: ["ADR-016", "ADR-CONFIG-v1"]
children: ["RS-NFR-06.1", "RS-NFR-06.2"]
---
```

# 運用メモ
- 語彙の追加は原則禁止。必要な場合は **本標準（ID: STD-KMK-FM-01）を改版**する。
- 既存文書の FM 改定は PR として提出し、CI の Lint を通すこと。
- Obsidian での見栄えを優先し、長文の説明は本文側に記す（FM には短く）。

# 変更履歴
- 1.0: 初版（簡潔・必要十分の FM 規約を単一ファイルで定義）。
