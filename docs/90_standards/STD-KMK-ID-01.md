---
id: STD-KMK-ID-01
title: ドキュメントID・命名標準（Kumiki）
version: "1.0"
status: draft
integrates_with: ["STD-KMK-FM-01"]
---

# 1. 目的と適用範囲
Kumiki プロジェクトにおける **ドキュメントID（以下、ID）と命名規則**を定義する。要求・設計・試験・標準・運用など **全ドキュメント種別**に適用し、CI で一貫性を検証する。

# 2. 設計原則（必要十分）
- **一意/不変**: リネーム禁止。内容が大幅に変わる場合は新IDを採番し `supersedes` で置換関係を明示。
- **人間可読/機械可読**: 英大文字・数字・ハイフン・小数点（小節）に限定。ASCII のみ。
- **ソート容易**: 桁固定の連番で比較整列が安定すること。
- **差分耐性**: 文書の並べ替えや章構成変更でIDを変えない。IDは意味的ラベル。

# 3. 文字種と記法
- 使える文字: `A–Z`, `0–9`, `-`, `.`（小節のみ）。`_` や空白は **禁止**。
- 大文字のみ（小文字は使用しない）。
- 推奨長: 6〜32 文字（CI 警告の目安）。

# 4. ID 構造
```
<ID> := <TYPE> "-" [<DOMAIN> "-"] <KIND> "-" <NN> [ "." <SUB> ]*
```
- `<TYPE>`: 文書大分類。`CR | RS | HLF | FR | NFR | CN | DD | TS | ADR | OPS | STD`
- `<DOMAIN>`: 任意のドメイン/プロジェクト識別子。例: `KMK`（Kumiki 固有）、`M5NF` 等
- `<KIND>`: 下位分類。例: `FR`, `NFR`, `CTRL`, `ARCH`, `TEST`, `SEC` など（TYPEにより省略可）
- `<NN>`: **2桁以上の十進連番**（例: `01`, `12`, `103`）
- `<SUB>`: 小節番号（十進）。例: `06.1`, `06.2.3`

> 例: `RS-FR-01`, `RS-NFR-06.1`, `HLF-CTRL-01`, `ADR-016`, `STD-KMK-FM-01`, `DD-ARCH-03`, `TS-INT-12`

### よく使うパターン
- 要求仕様: `RS-FR-<NN>`, `RS-NFR-<NN>`, `RS-CN-<NN>`
- 上位要件: `HLF-<KIND>-<NN>`（例: `HLF-CTRL-01`）
- 設計: `DD-<KIND>-<NN>`（`ARCH`, `API`, `DATA` など）
- 試験: `TS-<KIND>-<NN>`（`UNIT`, `INT`, `SYS`, `E2E` など）
- 変更決定: `ADR-<NNN>`（3桁以上推奨）
- 標準/規約: `STD-KMK-<KIND>-<NN>`（本書は `STD-KMK-ID-01`）
- 運用: `OPS-<KIND>-<NN>`

# 5. 採番ルール
- **連番はスパース許容**（欠番可）。再利用は禁止。
- 小節（例: `06.1`）は **親の意味的まとまり**に従い付番。小節の並び替えでも親の `06` は変えない。
- 版の追加・改訂で ID を変更しない（`version` フィールドで表現）。
- 置換時（大改変）は新IDを発行し、**旧IDの FrontMatter に `supersedes`/`status: deprecated` を明記**。

# 6. 予約・衝突・廃止
- 予約接頭辞: `STD-KMK-*`（Kumiki 標準）、`ADR-*`（アーキ決定）。
- 一時テンプレートの `xx` は **テンプレート専用**。本編では禁止（CI で拒否）。
- 衝突時は **先勝**（最初に main に入った方を正）。後続は採番し直す。

# 7. ID レジストリ運用（推奨）
- ルートに `id_registry.yml` を置き、静的に管理：
  ```yaml
  RS-FR-01: { path: docs/02_requirements/RS-FR-01.md, title: "...", status: review }
  STD-KMK-ID-01: { path: docs/90_standards/STD-KMK-ID-01.md, title: "ドキュメントID・命名標準" }
  ```
- CI チェック：一意性、未登録/重複、孤立ノード、未知ID参照（unknown_refs）。

# 8. 正規表現・ABNF（機械可読）
- Regex（代表例）  
  - `^([A-Z]{2,5})(?:-([A-Z0-9]{2,8}))?(?:-([A-Z]{2,8}))?-([0-9]{2,})(?:\.[0-9]+)*$`
  - 例の許容: `RS-FR-01`, `RS-NFR-06.1`, `HLF-CTRL-01`, `ADR-016`, `STD-KMK-ID-01`
- ABNF（参考）  
  ```abnf
  ID        = TYPE "-" [ DOMAIN "-" ] KIND "-" NUMBER *( "." SUB )
  TYPE      = 2*5ALPHA
  DOMAIN    = 2*8(ALPHA / DIGIT)
  KIND      = 2*8ALPHA
  NUMBER    = 2*DIGIT / (DIGIT 2*DIGIT)
  SUB       = 1*DIGIT
  ```

# 9. 変更手順（運用）
1) 既存IDの大幅変更が必要になった場合は **リネームせず**新IDを採番。  
2) 旧文書に `status: deprecated` と `supersedes: ["<新ID>"]` を付与。  
3) 影響する文書は `depends_on` などの参照を更新。  
4) `id_registry.yml` とリンクを更新し、CI を Pass。

# 10. 付録：ミニ FAQ
- **Q: 番号を詰め直していい？** → **不可**。履歴が壊れる。  
- **Q: 小節だけ分離したい** → 親IDは維持し、`06.1` を独立ファイル化しても ID は変えない。  
- **Q: 別プロジェクトと衝突しそう** → `<DOMAIN>` を付与（例: `RS-FR-01` → `RS-M5NF-FR-01`）。

# 変更履歴
- 1.0: 初版（ID 構造・採番・レジストリ・CI 検証の最小規定）。
