---
id: STD-KMK-TRACE-01
title: トレーサビリティ標準（Kumiki）
version: "1.0"
status: draft
parent: STD-KMK-00_INDEX
integrates_with: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01"]
---

# 1. 目的と適用範囲
Kumiki の全ドキュメント（`CR, RS, HLF, FR, NFR, CN, DD, TS, ADR, OPS, STD`）に対し、**トレーサビリティ（Trace）**の最小必須要件と検証基準を定める。FM の固定語彙に基づき、**孤立ノードの排除**・**入口/出口トレースの担保**・**差分トレース（inherit+delta）** を標準化する。

# 2. 基本原則（必要十分）
- **入口トレース必須**: 下位文書は少なくとも 1 つの上位根拠に接続（`refines` または `satisfies`）。
- **出口トレース推奨/必須**: 要求は検証手段へ接続（主に `children`→`TS-*`）。NFR も **少なくとも 1 つの TS** を推奨（性能/信頼性の可観測化）。
- **孤立ノード禁止**: `refines`/`satisfies`/`children` のいずれかにより接続。CI で検出しブロック可。
- **差分トレース（inherit+delta）**: 小節（例: `FR-06.1`）は親 `FR-06` の関係を **継承** し、差分（追加/削除/上書き）のみを列挙・集約する。
- **片方向の明確化**: 矢印の向きは **「根拠←要求→検証」** を基準に統一。

# 3. 関係の意味（方向と期待ペア）
| 関係 | 方向 | 期待される型ペア（例） |
|---|---|---|
| `parent`/`children` | 親 → 子 | `RS-FR → RS-FR-06.1`, `RS-NFR → RS-NFR-06.1` |
| `refines` | 下位 → 上位 | `FR → HLF/CR`, `DD → FR/NFR` |
| `satisfies` | 下位 → 上位 | `FR/NFR → HLF/CR/法規/ADR` |
| `depends_on` | 元 → 依存先 | `FR → ADR`, `DD → API/ADR` |
| `integrates_with` | 双方向 | `DD-API ↔ DD-DATA`, `DD ↔ OPS` |
| `constrains` | 制約元 → 制約対象 | `NFR → DD/FR`, `STD → RS/DD/OPS` |
| `conflicts_with` | 相互 | 要件/設計の競合（解消または分岐が必要） |
| `supersedes` | 新 → 旧 | `ADR-016 → ADR-009`, `STD 新版 → 旧版` |

# 4. 文書種別ごとの必須/推奨トレース
- **HLF/CR**: `children` に `FR`/`NFR` を少なくとも 1 件。  
- **FR**: `satisfies` に `HLF/CR`、`children` に **TS**（単体/結合/シナリオのいずれか）を 1 件以上。必要に応じて `depends_on` に `ADR`。  
- **NFR**: `constrains` に `DD` または `FR`、`children` に **TS** を 1 件以上。  
- **DD**: `satisfies` に `FR/NFR`。`depends_on` に `ADR` や他DD。`children` に **TS（設計検証）** を推奨。  
- **TS**: `satisfies` に **検証対象（FR/NFR）** を 1 件以上。テストが設計のみに紐づく場合は、その設計が辿って対象FR/NFRに達することを CI で検知。  
- **ADR**: `satisfies`/`constrains` の被参照を想定。重大な置換は `supersedes` を使用。  
- **STD/OPS**: `constrains` で各文書を制約。`OPS` は運用 Runbook で `STD` を遵守。

# 5. 差分トレース（inherit+delta）の規定
- **継承**: 子 `X.y` は親 `X` の `refines/satisfies/depends_on/integrates_with/constrains/conflicts_with` を継承する。  
- **差分**: 子で新たに記した関係は **追加**、親から不要になった関係は **削除** として自動判定。  
- **出力**: CI は「継承後の正味集合」と「差分ログ（added/removed/overridden）」を発行。

# 6. 生成物（標準ファイル構成の推奨）
- **アーティファクト**（CI生成）：
  - `artifacts/trace/graph.json` — ノード/エッジの生グラフ（IDと関係種別）。
  - `artifacts/trace/trace_index.csv` — 主要エッジの索引（下記 §7 スキーマ）。
  - `artifacts/trace/delta.csv` — inherit+delta の差分一覧。  
- **ドキュメント**（サイト掲載）：
  - `docs/70_trace/TRACE-INDEX.md` — 概観（孤立/断絶/循環の概要、要約表）。
  - `docs/70_trace/TRACE-BREAKS.md` — 断絶/孤立の詳細と修正提案。

# 7. トレース表スキーマ（CSV/MD 共通）
| 列名 | 型 | 説明 |
|---|---|---|
| `source_id` | string | 元文書（例: `RS-FR-12`） |
| `relation` | enum | `parent/refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes` |
| `target_id` | string | 参照先 ID |
| `rationale_snippet` | string | 本文抜粋（根拠20〜200字） |
| `confidence` | int (0..100) | 自動抽出の確度（BM25/ANNのスコア正規化等） |
| `reviewer` | string | 人手レビュー者（省略可） |
| `last_checked` | date | 確認日（ISO8601） |

> **FM の制約**: FM 配列は「ID文字列のみ」。根拠文や信頼度は **本文/表側**に出す。

# 8. CI/Lint 規定（TRACE系）
- **TRACE-001（入口）**: `FR/NFR/DD/TS` は `refines` または `satisfies` が **>=1**。違反は **エラー**。  
- **TRACE-002（出口）**: `FR/NFR` は `children` または **間接**に `TS` へ到達できること。到達不可は **警告/エラー（設定可）**。  
- **TRACE-003（孤立）**: 上流/下流のいずれにも接続しない文書は **エラー**。  
- **TRACE-004（循環）**: `refines/satisfies/depends_on/constrains` の **有向サイクル**を検出、閾値超過で **エラー**。  
- **TRACE-005（deprecated参照）**: `status: deprecated` への参照は **警告**。回避策を提案。  
- **TRACE-006（差分）**: 子が親から関係をすべて削除している場合は **警告**（親の意味を失う可能性）。  
- **TRACE-007（未知ID）**: `unknown_refs` は **0** を目標（`approved` 昇格条件）。

# 9. 例（FR→TS の入口/出口トレース）
```yaml
---
id: RS-FR-12
title: ログ収集（最小オーバーヘッド）
version: "1.0"
status: review
parent: RS-FR
satisfies: ["HLF-OBS-01"]
depends_on: ["ADR-016"]
children: ["TS-OBS-12", "TS-RT-07"]
---
```
上記から、CI は次のエッジを生成：  
- `RS-FR-12 --satisfies--> HLF-OBS-01`  
- `RS-FR-12 --depends_on--> ADR-016`  
- `RS-FR-12 --children--> TS-OBS-12`, `TS-RT-07`  
さらに `TS-* --satisfies--> RS-FR-12` がテスト側で定義されていることを検証する。

# 10. 実装メモ（アルゴリズム叩き台）
1) **FM収集** → 全MDのFMを抽出（フラット配列のみ）。  
2) **グラフ化** → NetworkX 等に `Node(id)` と `Edge(id, relation, id)` を投入。  
3) **到達解析** → FR/NFR から TS への到達性チェック（経路長制限可）。  
4) **inherit+delta** → `X → X.y` で関係集合を差分計算（added/removed/overridden）。  
5) **検証** → §8 の Lint を適用、CSV/MD を出力。  
6) **可視化** → `graph.json` を D3/mermaid 等でサイト表示（任意）。

# 11. 運用メモ
- 参照密度が高い要件は、**本文中に根拠抜粋（rationale_snippet）** を併記してレビュー効率を上げる。  
- `TS` は **対象FR/NFRの粒度に合わせて** 設計（過不足の検出に効く）。  
- `STD/OPS` は `constrains` を適切に使い、要求や設計へ「守るべきルール」を明示する。

# 変更履歴
- 1.0: 初版（入口/出口/孤立/差分/到達性の最小規定と生成物・Lint ルール）。
