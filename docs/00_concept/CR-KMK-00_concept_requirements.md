---
id: CR-KMK-00
title: Kumiki 概念要件（Concept Requirements）
type: concept_requirements
status: review
version: 0.3.0
created: '2025-08-31'
updated: '2025-09-02'
owner: PMO
tags:
- kumiki
- concept
- docops
canonical_parent: []
defines_ids:
- BG-KMK-01
- BG-KMK-02
- BG-KMK-03
- BG-KMK-04
- BG-KMK-05
- BG-KMK-06
- HLF-01
- HLF-02
- HLF-03
- HLF-04
- HLF-05
- HLF-06
- HLF-07
- HLF-08
- CR-KMK-01
- CR-KMK-02
- CR-KMK-03
- CR-KMK-04
- CR-KMK-05
- CR-KMK-06
- CR-KMK-07
- CR-KMK-08
- CR-KMK-09
- CR-KMK-10
- CR-KMK-11
- CR-KMK-12
- CR-KMK-13
- CR-KMK-14
- CR-KMK-15
id_aliases:
- CR-01
- CR-02
- CR-03
- CR-04
- CR-05
- CR-06
- CR-07
- CR-08
- CR-09
- CR-10
- CR-11
- CR-12
- CR-13
- CR-14
- CR-15
- BG-01
- BG-02
- BG-03
- BG-04
- BG-05
- BG-06
---

# Kumiki 概念要件（Concept Requirements）

> **Kumiki** は、ソフトウェア開発向けの「ドキュメント自動生成・管理（DocOps）」プラットフォーム。Obsidian 互換の Markdown、フラット FrontMatter、安定 ID、トレース、自動インデクシング、AI 補助編集、CI ゲート、静的公開までを**一貫プロセス**として提供する。

---

# 1. 目的・ビジョン

> **一言サマリ**：Kumiki は、テンプレ展開 → Lint → トレース → CIゲート → 公開 → 監査を一気通貫で自動化する **DocOps 基盤**。  
> 変更の可観測性と再現性を保証し、**品質の一貫性**・**監査可能性**・**リードタイム短縮**を実現する。

## 1.1 背景 / 課題
- 文書品質の**ばらつき**（表記揺れ・FM欠落・リンク切れ）。
- トレーサビリティの**断絶**（上位要求⇄CR⇄実装/テストの往復不全）。
- レビュー/承認プロセスの**属人化**・公開までの**リードタイム長期化**。
- 秘密情報の**流出リスク**、公開後の**監査証跡不足**。
- 検索の**到達性不足**（語彙外/同義語に弱い）。

根本原因：手作業運用、非構造メタデータ、決定性のないCI、検索IFのロックイン、監査エビデンスの分散・欠落。

## 1.2 Vision（目指す状態）
- **単一ソース（Markdown+FrontMatter）**を中核に、生成/検査/公開/監査を**自動化&冪等化**。
- **Trace Graph**で BG↔HLF↔CR↔FR/NFR↔CN↔DD↔TEST の**往復到達**を常時検証。
- **CI as Product**：DocLint・Trace・Search・SecScan を**決定的**（再実行で同じ結果）に。
- **Security by default**：PII/Secrets を PR で**自動ブロック**、WORM 台帳で改竄検知 100%。
- **Search first**：BM25+ANN のハイブリッドで**探索性**を改善。**IF固定**で FAISS/ScaNN/Annoy を差替え可能。
- **Scale-ready**：300→1k 文書でも CI と検索が**実用性能**を維持。

## 1.3 目的（Objectives）— BG との対応
- **O1 品質の一貫性**（BG-KMK-01）：DocLint で FM 必須と表記を機械担保、差分影響をハイライト。
- **O2 監査可能性**（BG-KMK-02）：生成・承認・公開イベントを**不可変**に保存（CR-05）。
- **O3 リードタイム短縮**（BG-KMK-03）：PR→公開を**自動ゲート**で直列化（CR-10/15）。
- **O4 探索性向上**（BG-KMK-04）：BM25+ANN と評価ループで Hit@3 改善（CR-03/13/14）。
- **O5 セキュリティ事故ゼロ**（BG-KMK-05）：PR時の検知を**Fail-close**運用（CR-09/05）。
- **O6 スケールとコスト効率**（BG-KMK-06）：夜間 1k で CI<60m、Artifacts 欠測 0（CR-11/14）。

## 1.4 提供価値（Value Proposition）
- **開発者**：テンプレ自動展開、即時 Lint、**影響ハイライト**、**AI差分パッチ**で手戻り削減。
- **レビュア**：**往復トレース**と Gate サマリで**判断の透明性**向上。
- **セキュリティ/監査**：PR での**機密検知**と **WORM 台帳**で**事後追跡性**を担保。
- **PM/PO**：**KPI ダッシュボード**（CI時間、Lint率、到達率、検知件数）で運用の見える化。

## 1.5 ペルソナ / 主要ユースケース
- **P1: プロジェクトリード/PM** — マイルストーン時に**トレースと網羅性**を即時確認。
- **P2: システム/ソフトウェア設計者** — 仕様変更から**影響範囲**と**更新候補**を自動提示。
- **P3: QA/テストエンジニア** — 仕様→試験ケース→結果の**往復参照**と**欠落検知**。
- **P4: ドキュメント担当** — **日本語検索**の精度とセクション粒度の**差分レビュー**。
- **P5: DevOps** — **CI/CD 内での DocOps ゲート**（lint/trace/coverage/リンク健全性）。

## 1.6 原則（Guiding Principles）
1. **FrontMatter First**：ID/関係キーを一次情報に。生成物は**構造化**して残す。  
2. **Deterministic CI**：再実行で同一結果（Seed固定/環境固定/閾値明示）。  
3. **Evidence by Default**：すべての検査は**Artifacts + メトリクス**を出力し、WORM へ保全。  
4. **Open Connectors**：検索/ANN/埋め込みは**IF固定**で差替え可能（CR-13）。  
5. **Fail-safe Security**：機密検知は**Fail-close**、許容例外は台帳で審査。  

## 2. システム境界（Context）
- **入力**：Markdown+FrontMatter、PRイベント、スキャン結果
- **出力**：公開サイト、Artifacts、WORM台帳
- **関係者**：開発者、DocOps、セキュリティ、承認者（Code Owners）

### 2.1 目的と境界の考え方
- **境界（Boundary）**は「Kumiki が**制御**し、**再現性を保証**する領域」を指す。  
- **外部（External）**は、Kumiki が**結果を依存**するが**制御できない**領域（例：GitHub、Pages、Secrets Manager）。

```
[Author/Reviewer] --PR/Push--> [GitHub Repo] --Actions--> [Kumiki Pipeline]
| |--> Artifacts/metrics (構造化)
| |--> Site (公開物)
| '--> WORM Ledger (不可変台帳)
'--<-- Reviews/Comments/Checks <---------------------'
```

### 2.2 入力（Inputs）
1) **Markdown + FrontMatter（FM）**
   - 対象: `docs/**/*.md`
   - **必須キー**: `id,title,type,status,version,created,updated`
   - **関係キー**: `canonical_parent, depends_on, refines, satisfies, integrates_with, constrains, supersedes, contributes_to (BG), satisfies_hlf (HLF)`
   - **最小FM例**:
     ```yaml
     ---
     id: CR-KMK-03
     title: "ハイブリッド検索（BM25+ANN）"
     type: concept_requirement
     status: review
     version: 0.2.0
     created: 2025-08-31
     updated: 2025-09-02
     canonical_parent: CR-KMK-00
     contributes_to: [BG-KMK-04, BG-KMK-06]
     satisfies_hlf: [HLF-03, HLF-08]
     ---
     ```
2) **PR/Push イベント**
   - 利用イベント: `pull_request (opened/synchronize/reopened)`, `push (main)`, `workflow_dispatch`
   - 取得情報: 差分（`git diff`）、コミット SHA、ラベル、レビュー状態、CODEOWNERS 対象かどうか。
3) **スキャン結果（セキュリティ/品質）**
   - PII/Secrets パターン、許容（allowlist）、リンタールール、対訳表（ja↔en）。

### 2.3 出力（Outputs）
1) **公開サイト**  
   - 生成: `mkdocs build -f mkdocs.yml` → `site/` → GitHub Pages  
   - 保証: **CR-10**のゲート通過時のみデプロイ。
2) **Artifacts（構造化成果物）**
   - DocLint: `artifacts/doclint/report.json`, `report.md`
     - 例（要約）:
       ```json
       {"errors": 0, "files": 42,
        "items": [{"path":"docs/..","code":"FM_REQUIRED_MISSING","severity":"major","msg":"必須キー欠落: id"}]}
       ```
   - Trace Graph: `artifacts/trace/graph.json`, `graph.md`
     - 例（要約）:
       ```json
       {"cycles":0,"nodes":[{"id":"CR-KMK-03","path":"docs/00_concept/CR-KMK-03.md"}],
        "edges":[{"src":"CR-KMK-03","dst":"HLF-03","type":"satisfies_hlf"}],
        "unknown_refs": []}
       ```
   - Search/Index: `artifacts/search/index/*`（BM25/ANN/Embedding）
   - SecScan: `artifacts/secscan/findings.json`（ヒット箇所抜粋付き）
   - Gate: `artifacts/gate/summary.json`（合否/根拠）
   - Metrics: `artifacts/metrics/metrics.jsonl`（ジョブ毎の time/size/counters）
3) **WORM 監査台帳**
   - 形式: `artifacts/approval/audit_event.jsonl`（append-only）
   - イベント例:
     ```json
     {"ts":"2025-09-02T10:23:45Z","actor":"github-actions[bot]","action":"publish",
      "subject_id":"CR-KMK-03","sha":"<commit>","sig":"<detached-signature>",
      "evidence_uri":"site/index.html"}
     ```

### 2.4 関係者（Stakeholders）
- **開発者（Author）**: 原稿/修正の作成、PR 起票。
- **レビュア（Reviewer/DocOps）**: Lint/Trace/差分影響を確認、コメント。
- **セキュリティ**: 検出ルール運用、例外の審査（WORM に残す）。
- **承認者（Code Owners）**: クリティカル変更の手動承認（CR-15）。
- **CI運用者**: ランナー/Secrets/Pages の健全性維持。

> 参考: RACI（簡易）  
> - 作業（R）= 開発者/DocOps、承認（A）= 承認者、助言（C）= セキュリティ、報告（I）= PMO

### 2.5 信頼境界・データ分類
- **Trust Boundary**: GitHub Actions 実行環境 ↔ 公開サイト ↔ 監査ストア（WORM）
- **分類**:  
  - P0: Secrets/PII（外部公開不可、リポ内も秘匿）  
  - P1: 内部メタ（FM、Trace、Metrics）  
  - P2: 公開コンテンツ（site/）
- 方針: **Fail-close**（危険が疑われれば公開停止）＋ **台帳必須**（CR-05）

### 2.6 インターフェース（IF）とコマンド
- 生成: `python tools/ci/gen_index.py --update-mkdocs`
- Lint: `python tools/ci/lint.py check --rules tools/docops_cli/config/doclint_rules.yml --out artifacts/doclint --format json,md`
- Trace: `python tools/docops_cli/trace.py build --rules tools/docops_cli/config/trace_rules.yml --out artifacts/trace --format json,md`
- Publish: `mkdocs build -f mkdocs.yml && <pages deploy>`
- 受け渡し契約（例）:
  - `graph.json` トップに `cycles` を置く（承認ゲートが参照）
  - DocLint の `severity` は `minor|major|critical` の３値

### 2.7 前提/制約（Assumptions/Constraints）
- Python 3.11 / Linux ランナー / GitHub Pages
- `docs/` 直下が MkDocs の `docs_dir`（二重 `docs/docs` は不可）
- FM キーは**1階層フラット**（ネストしない）
- 生成物は**決定的**（seed/閾値/バージョン固定）



## 3. スコープ／非スコープ

### 3.1 スコープ（MVP → 拡張）

#### 3.1.1 文書CIパイプライン（テンプレ → Lint → Index → Trace → Gate → Publish）
- テンプレ自動展開（タイトル/見出し/FM雛形、Obsidian互換の**フラットFrontMatter**準拠）
- DocLint（必須FM・ID形式・重複・参照妥当性・PlantUMLシンタックス・外部リンク健全性）
- Indexing（BM25/ANN/Embedding の作成・更新）
- Trace Graph（`depends_on/refines/satisfies/integrates_with/constrains/supersedes/canonical_parent/satisfies_hlf/contributes_to`）
- Gate集約（CR-10）：PRでの最小ゲート、Nightly/Releaseゲート、**合格時のみ公開**
- 公開（MkDocs/Pages）と Artifacts の永続化  
（対応：**CR-01/02/04/10/11**, HLF-01/02/05/06, BG-01/02/03）

#### 3.1.2 ID管理と入口トレース
- **安定ID**（HID/TID 等）規約、`canonical_parent` の付与と入口到達の自動付与
- 参照関係の自動生成（`refines/satisfies/depends_on` など）
- 重複/欠番/断リンクの検出と**自動修復案**（CR-07）  
（対応：**CR-02/04/07**, HLF-02, BG-01/03）

**[追記] 上流ID（BG/HLF/KPI）の扱いと入口ノード化**

- **定義**：`BG-KMK-xx`（ビジネスゴール）、`HLF-xx`（ハイレベル機能要求）、`KPI-***-xx` は「入口（upstream root）」IDクラスとして扱う。  
- **存在形態**：  
  (1) 別ドキュメントで詳細化（推奨）／(2) 本ドキュメント（`CR-KMK-00`）内のみの定義（許容）。  
- **到達要件**：Graph 上で入口IDがノード登録され、下流（CR/FR/NFR/CN/DD/TEST）から  
  - `BG/HLF` へは `satisfies` または `refines`、  
  - `KPI` へは `constrains`  
  のいずれかで**少なくとも1本**のエッジが張られて到達できること。未到達は Gate で **Fail**（CR-04）。

**FrontMatter 規約（追加）** — *フラット1段／配列は文字列IDのみ*
- `CR-KMK-00`（本ページ）に、入口IDを**文書内定義**として公開するためのメタキーを追加：
  - `defines_ids: [BG-KMK-01, ..., HLF-01, ..., KPI-QLT-01, ...]`  
    → 本ページ内で**正規に定義**する入口IDの列挙（Graph にアンカー付きノードを生成）
  - `id_aliases: [BG-01, KPI-QUALITY-01, ...]`  
    → 旧表記・短縮表記・外部由来の**別名**（解決テーブルとして使用）
- 下流ドキュメント側（例：CR/FR/NFR/CN…）の推奨フィールド：
  - `satisfies: [BG-KMK-xx, HLF-yy]`  … 上流ゴール/HLFへの満足を明示
  - `constrains: [KPI-***-zz]`       … 達成を**制約/目標**として明示（KPIのトレース入口）
  - `canonical_parent: CR-KMK-00`     … 概念要件への入口を一本化（多親防止）
- **互換（deprecated）**：過去の独自キーは CLI 側で自動正規化（CR-07）。  
  - `hlf_roots` → `satisfies`（HLF）へ統合  
  - `contributes_to` → `satisfies`（BG）へ統合

**入口トレース生成アルゴリズム（要約）**
1. 各文書の FM から固定語彙の関係キーを収集（`refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes`）。  
2. `CR-KMK-00` の `defines_ids` を読み、本文内の入口ID（BG/HLF/KPI）を**ノード**として登録（章見出しに自動アンカー付与）。  
3. `id_aliases` を**別名解決テーブル**に登録（重複・衝突は CR-07 の自動修復案へ）。  
4. 全ドキュメントの関係キーを**型付きエッジ**に変換。  
5. 入口IDへの**到達率**を算出：  
   - `BG/HLF`：`satisfies|refines` 経由で到達  
   - `KPI`：`constrains` 経由で到達  
6. `unknown_refs`・閉路・多親違反を検出し、**自動修復案**（置換/追加/分割/再配線）を生成（CR-07）。

**検証とゲート（最小基準）**
- `unknown_refs = 0`、**入口到達 = 100%（重要ノード）**。  
- `canonical_parent` は**常に1つ**（多親は Fail）。  
- `KPI-*` が定義される場合、**少なくとも1つ**の下流ノードから `constrains` で到達していること（未到達は警告→Gate 条件化可）。

**実装例（FM スニペット）**
- `CR-KMK-00`（本ページ）:
  ```yaml
  defines_ids:
    - BG-KMK-01; BG-KMK-02; BG-KMK-03; BG-KMK-04; BG-KMK-05; BG-KMK-06
    - HLF-01; HLF-02; HLF-03; HLF-04; HLF-05; HLF-06; HLF-07; HLF-08
    - KPI-QLT-01; KPI-OPS-01; KPI-SRC-01; KPI-SEC-01; KPI-OBS-01; KPI-SCL-01
  id_aliases: [BG-01, KPI-QUALITY-01]  # 任意


#### 3.1.3 検索（Lexical + Embedding、評価付き）
- **自動インデクシング**：BM25 + Embedding（ANN）。日本語形態素（Kuromoji/Sudachi）＋ n-gram フォールバック
- 評価と回帰比較（Hit@k、nDCG、Top@3 劣化監視）
- コネクタ差替え（FAISS/ScaNN/Annoy）を **IF固定**で許容  
（対応：**CR-03/13/14**, HLF-03/08, BG-04/06）

#### 3.1.4 セキュリティ検査（Fail-close）
- PII/Secrets 検知、許容リスト（WORM台帳で審査・保全）
- 公開直前の **Fail-close** 運用、PRでのブロック  
（対応：**CR-09/05**, HLF-04/06, BG-05/02）

#### 3.1.5 LLM 補助（人手承認前提）
- 差分生成・**unified diff** パッチ提案、トレース欠落の草案、要約/表生成
- 適用は**必ず人手承認**（Automergeしない）  
（対応：**CR-12/15**, HLF-01/05/06, BG-01/03）

#### 3.1.6 静的サイト公開とクライアント検索
- MkDocs + Pages による静的サイト、Pagefind 等のクライアント検索（日本語対応強化）
- 公開物は Gate 通過時のみ更新  
（対応：**CR-10/11**, HLF-01/05, BG-01/03）

#### 3.1.7 可観測性・監査台帳
- 全ジョブで**構造化メトリクス**出力、Artifacts/WORM への長期保全（≥180日）
- 生成・改版・承認・公開の**不可変ログ（WORM）**  
（対応：**CR-05/11/15**, HLF-05/06, BG-02/06）

#### 3.1.8 CI 連携（GitHub Actions）
- PR最小ゲート、Nightly、Release、Pages/Artifacts 公開
- 決定性・再現性（seed/閾値/バージョン固定）  
（対応：**CR-10/11**, HLF-01/05/06, BG-01/03/06）

#### 3.1.9 多言語対訳整合
- `docs/ja` と `docs/en` の **ID同等性・参照整合**の検査
- 差異検出と同期支援（生成は対象外）  
（対応：**CR-08**, HLF-07, BG-01）

---

### 3.2 非スコープ（MVP 段階）

- **リアルタイム共同編集**（Google Docs 的コラボ機能）
- **企業横断 SSO/権限管理の統合**（将来拡張で検討）
- 外部ナレッジベース（Confluence/Jira）**全面同期**（必要時の**局所インポートのみ**）
- **外部DLP/IRM/Secrets Manager の機能置換**（Kumiki は連携のみ）
- **自動翻訳生成**（品質検査・対訳整合は対象、翻訳の生成は対象外）
- **UI/UX の本格CMS化**（MkDocs を超える独自CMSの実装は範囲外）
- **業務アプリ/プロダクトそのものの要件・設計**
- **テスト自動化の包括的実装**（本基盤はテスト成果物との**トレース接続**まで）

---

### 3.3 スコープ領域と BG/HLF/CR の対応（要約）

| スコープ領域 | 主対応CR | 対応HLF | 関連BG |
|---|---|---|---|
| 文書CIパイプライン | CR-01/02/04/10/11 | HLF-01/02/05/06 | BG-01/02/03 |
| ID管理・入口トレース | CR-02/04/07 | HLF-02 | BG-01/03 |
| 検索（Lexical+Embedding） | CR-03/13/14 | HLF-03/08 | BG-04/06 |
| セキュリティ検査 | CR-09/05 | HLF-04/06 | BG-05/02 |
| LLM補助 | CR-12/15 | HLF-01/05/06 | BG-01/03 |
| 静的サイト公開/Artifacts | CR-10/11 | HLF-01/05 | BG-01/03 |
| 可観測性・監査台帳 | CR-05/11/15 | HLF-05/06 | BG-02/06 |
| 多言語対訳整合 | CR-08 | HLF-07 | BG-01 |

### 3.4 ボーダーライン（誤解しやすい境界）
- **多言語**：対訳整合（ID/参照）はスコープ、翻訳文の品質判定・生成は非スコープ  
- **AI 支援**：`*.patch` の提案（CR-12）はスコープ、**自動適用**は非スコープ（人手承認必須）  
- **セキュリティ**：PR 時の検知と公開ブロックはスコープ、**恒久鍵管理**は非スコープ（外部に委譲）

### 3.5 成果物と受入（Scope Done の判定）
- **成果物**: `site/`, `artifacts/**`, `audit_event.jsonl`（WORM）
- **受入**:
  - DocLint 重大エラー 0（PR 基準）
  - 入口/往復 到達 100%（重要ノード）
  - SecScan 既知パターン検知 100%・誤検知 ≤2%
  - CI 合計 <10 分（PR 時） / <60 分（1k, nightly）

---

## 4. 成果物（Artifacts）

> すべての成果物は機械可読・決定的・参照可能であること。  
> 原則：すべて**機械可読（構造化）**・**決定的**・**参照可能（URI化）**・**WORM保全**。  
> 生成物は CI ごとに `artifacts/` 直下へ出力し、**最低180日**保管（CR-11）。公開可否は **Gate** 成果物で決定（CR-10）。

- テンプレート: docs/ 配下の雛形（CR/RS/HLF/FR/NFR/CN/ADR/TRACE）。
- CLI: docops_cli（FM→Graph→BM25/ANN スケルトン、差分/Lint/Trace ツール）。
- CI 設定: .github/workflows/（PR 最小ゲート、静的公開）。
- スタイルガイド: FrontMatter 運用規約、ID 体系、語彙 _vocabulary.yml。

| パス | 目的 / 主な内容 | 主生成（CR） | 主利用 / Gate 影響 | 対応BG | 対応HLF | 主KPI/SLO |
|---|---|---|---|---|---|---|
| `artifacts/doclint/*` | 文書の静的検査（FM必須・ID整合・記法一貫性・参照妥当性） | CR-01 | Gateの入力（重大/致命エラーがあればFail） | BG-KMK-01, BG-KMK-03 | HLF-01, HLF-05 | DocLint重大エラー率≤目標（KPI-QLT-01） |
| `artifacts/trace/*` | トレーサビリティ（BG↔HLF↔CR↔FR/NFR↔CN↔DD↔TEST）到達性/閉路/未知参照 | CR-02, CR-04 | Gateの入力（重要ノードの往復到達100%を判定） | BG-KMK-01, BG-KMK-03 | HLF-02 | 重要ノード往復到達=100% |
| `artifacts/search/*` | 検索インデックス/評価（BM25, ANN, Embedding, 回帰比較） | CR-03, CR-13, CR-14 | Gateの入力（基準未達・劣化>閾値でFail） | BG-KMK-04, BG-KMK-06 | HLF-03, HLF-08 | Hit@3≥基準／劣化≤3pt（KPI-SRC-01） |
| `artifacts/secscan/*` | セキュリティ検査（PII/Secrets/機密の検知と許容判定） | CR-09 | Gateの入力（致命検知でFail、Fail-close） | BG-KMK-05, BG-KMK-02 | HLF-04, HLF-06 | 公開後検知0／PR時Fail率=100%（KPI-SEC-01） |
| `artifacts/approval/*` | 生成・改版・承認・公開の不可変台帳（WORM） | CR-05, CR-15 | 監査・ガバナンス（公開根拠の証跡／例外承認の台帳） | BG-KMK-02, BG-KMK-05 | HLF-06, HLF-05 | 監査イベント欠落0／改竄検知100% |
| `artifacts/gate/*` | 各検査の合否集約と最終判断（公開可否の単一真偽） | CR-10 | 公開フローの唯一の判定源（Pass時のみ公開） | BG-KMK-01, BG-KMK-03, BG-KMK-05 | HLF-01, HLF-06 | PR→公開リードタイム短縮（KPI-OPS-01）に寄与 |

- **ファイル名規約**：`<artifact>_<yyyymmddTHHMMSSZ>.<ext>` を推奨（例外：固定名を上書きする代表ファイル）。  
- **時刻**：`UTC ISO8601（Z）` に統一。  
- **整合性**：`_checksums.txt` で **SHA256** を列挙、WORM台帳イベントにもハッシュを併記（CR-05）。

### 4.1 相互関係（要点）
- **Gate** は `doclint / trace / secscan / search` の結果を取り込み、**最終合否**に集約する（CR-10）。  
- **WORM台帳** は公開・承認・例外の事実を**改竄検知可能**な形で保全し、すべての成果物の**根拠URI**を保持する（CR-05）。  
- **検索成果物**は HLF-03/08 の達成度を示す評価と連動し、**差替え時の劣化閾値**を満たすことが公開条件となる（CR-13/14）。  
- **トレース成果物**は BG/HLF と CR 群との**往復接続**を裏付け、**重要ノードの到達100%**を Gate が検証する（CR-02/04）。  
- **DocLint成果物**は BG-KMK-01（品質一貫性）の**一次指標**であり、**重大エラーのゼロ化**が Gate 通過の前提となる（CR-01）。  
- **SecScan成果物**は BG-KMK-05（セキュリティ事故ゼロ）の**一次指標**であり、**致命検知=即Fail**の方針に従う（CR-09）。

---


## 5. 事業ゴール（BG）
### BG-KMK-01：公開品質の一貫性
- **KPI**：DocLint重大エラー率（per PR）
- **計測**：artifacts/doclint/report.json（major/critical件数）
- **目標**：≤ 2%（四半期移動平均）

### BG-KMK-02：監査可能性・改竄検知
- **KPI**：監査イベント欠落率／改竄検知率
- **計測**：artifacts/approval/audit_event.jsonl（CR-05）
- **目標**：欠落0／検知100%

### BG-KMK-03：変更リードタイム短縮
- **KPI**：PR→公開の中央値（hours）
- **計測**：CIメトリクス（開始/終了時刻）
- **目標**：-30%/Q

### BG-KMK-04：探索性（検索精度）向上
- **KPI**：Hit@3 / nDCG@10
- **計測**：CR-03 ベンチレポート
- **目標**：+5pt対ベースライン

### BG-KMK-05：セキュリティ事故ゼロ
- **KPI**：公開後検知数／PR時Fail率
- **計測**：CR-09/WORM 台帳
- **目標**：公開後0／PR時100%Fail

### BG-KMK-06：スケールとコスト効率
- **KPI**：CI時間@1k・検索P95(ms)
- **計測**：CR-14 測定
- **目標**：<60m ／ <300ms


## 6. ハイレベル機能要求（HLF）
### HLF-01：DocOpsパイプライン
- **範囲**：テンプレ→Lint→Index→Trace→SecScan→Gate→Publish
- **主対応CR**：CR-01,02,09,10,11,15
- **受入**：CI合計<10min、Artifacts欠測0

### HLF-02：トレーサビリティグラフ
- **範囲**：RS↔HLF↔FR/NFR↔CN↔DD↔TEST↔TRACE 可視化・検証
- **主対応CR**：CR-02,04,07
- **受入**：往復100%、未知参照0

### HLF-03：検索・ナレッジ到達
- **範囲**：BM25+ANNと評価ループ
- **主対応CR**：CR-03,13,14
- **受入**：Hit@3基準達成、劣化≤3pt

### HLF-04：セキュリティ/機密ブロック
- **範囲**：PII/Secrets検知→PR Fail
- **主対応CR**：CR-09,05
- **受入**：既知検知100%、誤検知≤2%

### HLF-05：可観測性
- **範囲**：構造化メトリクス出力と保全
- **主対応CR**：CR-11,05
- **受入**：欠測0、≥180日保存

### HLF-06：ガバナンス/承認ゲート
- **範囲**：クリティカル変更の手動承認必須
- **主対応CR**：CR-15,10,05
- **受入**：逸脱0、監査指摘0

### HLF-07：多言語対訳整合
- **範囲**：ID同等性・参照整合の検査
- **主対応CR**：CR-08
- **受入**：差異抽出100%、誤検知≤5%

### HLF-08：スケール耐性
- **範囲**：300→1k性能・品質測定
- **主対応CR**：CR-14,03,11
- **受入**：1kでCI<60分、重大違反0


## 7. 概念レベルCR（CR-01〜15）— 要約
### CR-KMK-01: テンプレート自動展開と DocLint
- **G**: テンプレ生成とFM必須項目の機械担保、表記揺れ/構造崩れをDocLintで検出。
- **I**: `docs/**/*.md` 差分、テンプレ定義、`doclint_rules.yml`。
- **O**: `artifacts/doclint/report.json, .md`、自動Fix（オプション）。
- **AC**: 必須キー欠落0、既知Lint違反の検出率≥99%。
- **関連**: BG=BG-KMK-01 / HLF=HLF-01, HLF-05

### CR-KMK-02: FM→Graph→入口トレース
- **G**: FMの関係キーからGraphを生成し、親→子の入口到達性を提示。
- **I**: FrontMatter、`trace_rules.yml`。
- **O**: `artifacts/trace/graph.json, .md`（`cycles`/`unknown_refs` 含む）。
- **AC**: 入口到達率=100%、未知参照=0。
- **関連**: BG=BG-KMK-01, BG-KMK-03 / HLF=HLF-02, HLF-06

### CR-KMK-03: ハイブリッド検索（BM25+ANN）
- **G**: BM25+ANNのハイブリッド検索で語彙外にも強い検索を実現。
- **I**: 埋め込み、インデックス規則。
- **O**: `artifacts/search/index/*`、評価レポート。
- **AC**: Top@3 ≥ 既定基準、誤誘導≤閾値。
- **関連**: BG=BG-KMK-04, BG-KMK-06 / HLF=HLF-03, HLF-08

### CR-KMK-04: 往復トレース到達テスト
- **G**: RS↔HLF↔FR/NFR↔CN↔DD↔TEST↔TRACE の往復到達を自動検査。
- **I**: Trace Graph、重要ノードタグ。
- **O**: 不到達ノード/リンク一覧と修正候補。
- **AC**: 重要ノード往復到達100%。
- **関連**: BG=BG-KMK-01, BG-KMK-03 / HLF=HLF-02

### CR-KMK-05: 監査台帳（WORM風）
- **G**: 生成・改版・承認・公開の不可変ログ（WORM）を保全。
- **I**: CIイベント、署名鍵、ハッシュ。
- **O**: 署名/ハッシュ付きイベント、Evidence URI。
- **AC**: 欠落0、改竄検知100%。
- **関連**: BG=BG-KMK-02, BG-KMK-05 / HLF=HLF-05, HLF-06

### CR-KMK-06: 変更差分→影響ハイライト
- **G**: PR差分から上流/下流/横断影響を自動提示。
- **I**: `git diff`、Trace Graph、参照関係。
- **O**: 影響候補（ファイル/ID/関係）一覧。
- **AC**: 既知ケースのヒット率≥0.9、誤通知≤0.1。
- **関連**: BG=BG-KMK-01, BG-KMK-03 / HLF=HLF-01, HLF-02

### CR-KMK-07: ID整合と重複検出/修復案
- **G**: 安定IDの重複/欠番/断リンクを検出し自動修復案を提示。
- **I**: FrontMatter, Trace Graph。
- **O**: 重複集合、候補ID、リンク再配線案。
- **AC**: 重複検出再現率≥0.99、誤修復≤0.5%。
- **関連**: BG=BG-KMK-01 / HLF=HLF-02

### CR-KMK-08: 多言語対訳整合
- **G**: ja/en のID同等性・参照整合を検査。
- **I**: 対訳表 or 規約。
- **O**: 差異レポート、同期スクリプト提案。
- **AC**: 差異の機械抽出100%、誤検知≤5%。
- **関連**: BG=BG-KMK-01 / HLF=HLF-07

### CR-KMK-09: セキュリティ/機密情報ブロック
- **G**: PII/秘密情報を検知→PR Failで公開事故を防止。
- **I**: 秘匿パターン、許容リスト。
- **O**: 検知レポート、サンプル周辺抜粋。
- **AC**: 既知パターン検知100%、誤検知≤2%。
- **関連**: BG=BG-KMK-05, BG-KMK-02 / HLF=HLF-04, HLF-06

### CR-KMK-10: CIゲート & 公開フロー
- **G**: DocLint/Indexing/Trace をPRで実行し、合格時のみ公開。
- **I**: 各CRのレポート、Gate規則。
- **O**: Gateサマリ、公開Artifacts/Pages。
- **AC**: CI合計<10分、決定的（非フレーク）。
- **関連**: BG=BG-KMK-01, BG-KMK-03 / HLF=HLF-01, HLF-06

### CR-KMK-11: 可観測性（メトリクス/ログ/アーティファクト）
- **G**: すべての検査に構造化メトリクスを付与し、Artifacts/WORMへ保全。
- **I**: CIログ、検査出力。
- **O**: `metrics.jsonl`、長期保存（≥180日）。
- **AC**: 欠測0、保存≥180日。
- **関連**: BG=BG-KMK-01, BG-KMK-02, BG-KMK-06 / HLF=HLF-05

### CR-KMK-12: 生成AI差分パッチ提案
- **G**: LLM出力は unified diff で提示、PRレビューに直結。
- **I**: PR差分、Lintヒント。
- **O**: `*.patch` 提案、採用率レポート。
- **AC**: 採用率≥60%、NG再発≤5%/週。
- **関連**: BG=BG-KMK-03, BG-KMK-01 / HLF=HLF-01, HLF-05

### CR-KMK-13: Embedding/ANNコネクタ差替え
- **G**: IF固定で FAISS/ScaNN/Annoy 等へ差替え可能。
- **I**: ベンチ用クエリ/コーパス。
- **O**: ベンチ結果、互換IFアダプタ。
- **AC**: 差替え後もTop@3率劣化≤3pt。
- **関連**: BG=BG-KMK-04, BG-KMK-06 / HLF=HLF-03, HLF-08

### CR-KMK-14: スケール試験（300→1k）
- **G**: 文書数増加時のCI時間増分と品質を測定しボトルネック提示。
- **I**: サンプルコーパス、CI構成。
- **O**: スケール曲線、改善PR候補。
- **AC**: 1kでCI<60分（nightly）、重大違反0。
- **関連**: BG=BG-KMK-06, BG-KMK-04 / HLF=HLF-08, HLF-03

### CR-KMK-15: 承認フローと自動マージ禁止条件
- **G**: クリティカル変更で手動承認を必須化し、自動マージ抑止。
- **I**: approval_rules.yml、PRイベント。
- **O**: `needs-approval` ラベル、WORMイベント。
- **AC**: ルール逸脱0、監査指摘0。
- **関連**: BG=BG-KMK-02, BG-KMK-03, BG-KMK-05 / HLF=HLF-06


## 8. ガバナンス（承認・公開・監査）
- **承認**（CR-15）：クリティカル変更は手動承認必須／Automerge抑止
- **公開**（CR-10）：ゲート通過のみ公開
- **監査**（CR-05）：WORM台帳で改竄検知100%

## 9. トレース俯瞰（入口／往復）
`RS↔HLF↔FR/NFR↔CN↔DD↔TEST↔TRACE` の往復到達を、親（本ページ）から子CRへ連結して検証します（CR-02/04）。
BG/HLFは**重要ノード**として扱います。

## 10. BG ⇄ HLF ⇄ CR 対応

| BG | 目的 | 主要HLF | 主対応CR |
|---|---|---|---|
| BG-KMK-01 | 品質一貫性 | HLF-01/05 | CR-01,10,11 |
| BG-KMK-02 | 監査・改竄検知 | HLF-05/06 | CR-05,11,15 |
| BG-KMK-03 | リードタイム短縮 | HLF-01/06 | CR-10,15 |
| BG-KMK-04 | 検索精度 | HLF-03/08 | CR-03,13,14 |
| BG-KMK-05 | セキュ事故ゼロ | HLF-04/06 | CR-09,15,05 |
| BG-KMK-06 | スケール/コスト | HLF-08/03/05 | CR-14,03,11 |

## 11. KPI／SLO

| 指標ID | 説明 | 収集元 | 目標 |
|---|---|---|---|
| KPI-QLT-01 | DocLint重大エラー率/PR | `artifacts/doclint/report.json` | ≤2% |
| KPI-OPS-01 | PR→公開リードタイム中央値 | CIメトリクス | -30%/Q |
| KPI-SRC-01 | Hit@3（評価セット） | CR-03評価 | +5pt |
| KPI-SEC-01 | 公開後検知件数 | CR-09/WORM | 0 |
| KPI-OBS-01 | メトリクス欠測率 | CR-11 | 0 |
| KPI-SCL-01 | CI時間@1k docs | CR-14レポート | <60m |

## 12. ロードマップ（2週スプリント）
- **MVP**：CR-01/02/10/11/09/07
- **v1.0**：残余CR、検索強化、スケール試験（CR-14）

> 目的：MVPを8週で確定、その後は検索/スケール/ガバナンスを強化して v1.0 に到達。
> 入口：BG/HLFを“上位要求”ノードとして、各スプリントで CR要件の達成証跡（Artifacts） を増分で積み上げます。

#### 事前準備（任意）：Sprint 0（準備週）
期間：09-02 〜 09-07
目的/範囲：CIランナー・Secrets・Pages・mkdocs.yml・DocLintルールの土台整備
対応CR：CR-10/11（基盤）, CR-01（ルール雛形）
Exit：PRで artifacts/metrics/* 出力、docs/index.md 自動再生成が決定的に通る

#### スプリント計画（2週 × 8本）
| Sprint | 期間                | 主要テーマ / 到達点                                        | 対応CR                          | 主要Artifacts（増分）                                                                         | Exit（AC/Gate）                         |
| ------ | ----------------- | -------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------------------------- | ------------------------------------- |
| **1**  | **09-08 → 09-21** | DocLintとテンプレの**一気通貫（最小）**。FM必須/ID形式/参照チェック開始       | CR-01 / CR-10 / CR-11         | `artifacts/doclint/*`, `artifacts/gate/summary.json`, `artifacts/metrics/metrics.jsonl` | Gateで**DocLint重大=0**を必須化、CI決定性の初期検証   |
| **2**  | **09-22 → 10-05** | \*\*Trace Graph（入口）\*\*可視化、`canonical_parent`の一括整備 | CR-02 / CR-07                 | `artifacts/trace/graph.json(.md)`                                                       | **入口到達100%**、`unknown_refs=0`         |
| **3**  | **10-06 → 10-19** | \*\*セキュリティ検査（Fail-close）\*\*導入、許容リストWORM連携         | CR-09 / CR-05                 | `artifacts/secscan/findings.json`, `artifacts/approval/audit_event.jsonl`               | **致命検知=Fail**、例外はWORM台帳必須             |
| **4**  | **10-20 → 11-02** | **Gate統合**（DocLint/Trace/SecScan）で**MVP Gate**完成   | CR-10 / CR-11                 | `artifacts/gate/summary.json`（合否集約）                                                     | **MVP確定**：PR時CI<10分/決定的、Gate=Passのみ公開 |
| **5**  | **11-03 → 11-16** | \*\*検索基盤（BM25+ANN）\*\*初版＋評価ループ開始                   | CR-03 / CR-11                 | `artifacts/search/index/*`, `eval/report.json`                                          | Hit\@3の**ベースライン確立**                   |
| **6**  | **11-17 → 11-30** | **ANN差替えIF**（FAISS/ScaNN/Annoy）と回帰比較、ID重複修復の自動提案   | CR-13 / CR-07 / CR-03         | `search/index/manifest.json`, 重複レポート                                                    | 差替え後**劣化≤3pt**、ID重複再現率≥0.99           |
| **7**  | **12-01 → 12-14** | **往復到達テスト**（RS↔…↔TRACE）・**多言語整合**導入                | CR-04 / CR-08                 | 逆到達結果（traceレポート増強）、対訳差分レポート                                                             | **重要ノード往復100%**、対訳誤検知≤5%              |
| **8**  | **12-15 → 12-28** | **スケール試験（300→1k）**、LLM差分パッチの採用率トラッキング、v1.0準備       | CR-14 / CR-12 / CR-11 / CR-10 | スケール曲線、`*.patch`採用率、安定メトリクス                                                             | 1kで**CI<60分(nightly)**、採用率≥60%        |

> MVP：Sprint 1〜4 完了時点（CR-01/02/09/10/11/07 の実効ゲート）。
> v1.0候補：Sprint 8 完了時点（検索/差替え/往復/多言語/スケールを含む）。

#### 各スプリントの品質・受入（共通）
DocLint：major+critical=0
Trace：unknown_refs=0、（Sprint7以降）往復到達100%
SecScan：critical=0、例外は台帳記録必須
Gate：合否が単一真偽で決まり、Passのみ公開
Metrics：metrics.jsonl 欠測0（全ジョブ）
決定性：同一コミットで再実行=同一結果

#### リスク&バッファ（運用メモ）
検索評価データの熟成不足 → Sprint5〜6でゴールデンセット固定（回帰比較の基準に）。
ANN差替え時の劣化 → しきい値（劣化>3pt）でGate Fail、FAISSをデフォルトに回帰できるIFを維持。
SecScan誤検知 → ルールABテスト＋許容リストのWORM審査で**誤検知≤2%**へ。
年末進行 → Sprint8はハードニング優先（機能投入は最小限）。

#### トレースの観点（BG/HLF接続）
BG：Sprintごとに該当BGのKPI更新をArtifactsで確認（例：KPI-QLT-01, KPI-OPS-01）。
HLF：HLF-01（パイプライン）→ Sprint1–4、HLF-03/08（検索/スケール）→ Sprint5–8、HLF-06（ガバナンス）→ Sprint3–4/6。
CR：各SprintのExitはArtifacts更新＋Gate基準達成で“到達”扱い。
 例）Sprint7終了＝CR-04のAC満たす（重要ノード往復100%）。

---

## 13. リスクと軽減策
- 誤検知過多 → ルール調整ABテスト
- ANN差替え劣化 → CR-13でTop@3維持策（評価セット充実）

## 14. 変更管理プロセス
変更申請→PR→ゲート→承認→公開→WORM記録を標準フローとして固定化します。

## 15. 用語集（ピン留め）
DocLint / WORM / FrontMatter / ANN / BM25 / Hit@3 / SLO