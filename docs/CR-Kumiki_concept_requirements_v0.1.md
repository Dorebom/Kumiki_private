---
id: CR-KMK-00
title: "Kumiki 概念要件 提案 v0.1"
type: concept_requirements
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept]
canonical_parent: ""
refines: []
satisfies: ["BG-KMK-01", "BG-KMK-02", "BG-KMK-03", "BG-KMK-04", "BG-KMK-05"]
depends_on: ["STD-KMK-FM-01", "STD-KMK-ID-01"]
integrates_with: ["STD-GHA-01", "STD-OBSIDIAN-01", "STD-PAGES-01"]
constrains: ["CN-KMK-01", "CN-KMK-02", "CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# Kumiki 概念要件（Concept Requirements）

> **Kumiki** は、ソフトウェア開発向けの「ドキュメント自動生成・管理（DocOps）」プラットフォーム。Obsidian 互換の Markdown、フラット FrontMatter、安定 ID、トレース、自動インデクシング、AI 補助編集、CI ゲート、静的公開までを**一貫プロセス**として提供する。

---

## 1. ビジョン / 目的
- **V1**: ドキュメントを「生成→紐付け→検証→公開」するまでを**機械可読**にし、エンジニアの負担を削減する。
- **V2**: ロボティクス/IoT/クラウド連携の**安全・再現性志向**の開発文化に適合し、仕様・設計・試験・運用の**双方向トレース**を常時維持する。
- **V3**: 日本語ドキュメントでの**検索性と可読性**を高水準で両立させる。

### 1.1 事業ゴール（BG）
- **BG-KMK-01**: ドキュメント作成/更新の所要時間を **50%** 以上削減。
- **BG-KMK-02**: 仕様↔設計↔試験のトレース欠落を **0件/リリース** へ。
- **BG-KMK-03**: 日本語/英語混在環境での用語統制と検索リコール **≥0.90** を実現。
- **BG-KMK-04**: 生成 AI の変更提案を **差分パッチ**として審査可能にし、採用率 **≥60%**。
- **BG-KMK-05**: CI で DocOps ゲートを実施し、**常に公開可能（release-ready）** な状態を維持。

---

## 2. ペルソナ / 主要ユースケース
- **P1: プロジェクトリード/PM** — マイルストーン時に**トレースと網羅性**を即時確認。
- **P2: システム/ソフトウェア設計者** — 仕様変更から**影響範囲**と**更新候補**を自動提示。
- **P3: QA/テストエンジニア** — 仕様→試験ケース→結果の**往復参照**と**欠落検知**。
- **P4: ドキュメント担当** — **日本語検索**の精度とセクション粒度の**差分レビュー**。
- **P5: DevOps** — **CI/CD 内での DocOps ゲート**（lint/trace/coverage/リンク健全性）。

---

## 3. スコープ / 非スコープ
### 3.1 スコープ（MVP→拡張）
- Obsidian 互換 **フラット FrontMatter** 準拠のテンプレート群（RS/HLF/FR/NFR/CN/ADR/TRACE）。
- **安定 ID**（HID/TID 等）と**入口トレース**自動付与（refines/satisfies/depends_on…）。
- **自動インデクシング**（Lexical + Embedding）。日本語形態素対応（Kuromoji/Sudachi 等）＋ n-gram フォールバック。
- **LLM 補助**: 差分生成、パッチ提案、トレース欠落の埋め草案、要約/表生成。
- **DocLint**: FrontMatter/リンク/ID/参照整合、PlantUML シンタックス検証、外部リンク健全性。
- **CI 連携**（GitHub Actions）: PR 最小ゲート、Nightly、Release、Pages/Artifacts 公開。
- **静的サイト公開**: Pagefind 等のクライアント検索を前提に日本語対応を強化。

### 3.2 非スコープ（MVP段階）
- リアルタイム共同編集（Google Docs 的機能）。
- 企業横断 SSO/権限管理の統合（将来拡張で検討）。
- 外部ナレッジベース（Confluence/Jira）全面同期（局所インポートのみに限定）。

---

## 4. 成果物（アーティファクト）
- **テンプレート**: `docs/` 配下の雛形（CR/RS/HLF/FR/NFR/CN/ADR/TRACE）。
- **CLI**: `docops_cli`（FM→Graph→BM25/ANN スケルトン、差分/Lint/Trace ツール）。
- **CI 設定**: `.github/workflows/`（PR 最小ゲート、静的公開）。
- **スタイルガイド**: FrontMatter 運用規約、ID 体系、語彙 `_vocabulary.yml`。

---

## 5. 機能要件（MVP 重点）
> **FR-KMK-xx** は後続の RS/HLF/FR 文書へ分割する前の概念レベル要求。

- **FR-KMK-01: FrontMatter 準拠チェック**  
  必須キー（id/title/status/version/…）と固定語彙（refines/satisfies/…）を検証し、
  未充足は PR を **fail**。  
  **受入基準**: 誤検知 ≤ 1%／100ファイル、検査時間 ≤ 60s／1,000ファイル。

- **FR-KMK-02: 安定 ID 付与/整合**  
  既存 ID と重複/欠番/リンク切れを検知し、**自動修復案（パッチ）**を提示。  
  **受入基準**: 重複検出再現率 ≥ 0.99、誤修復 ≤ 1/200件。

- **FR-KMK-03: 入口トレース自動生成**  
  ファイル内容から `refines/satisfies/depends_on` 候補を抽出し FrontMatter へ追記提案。  
  **受入基準**: トレース候補の適合率/再現率 ≥ 0.8/0.85（サンプル 200 リンク）。

- **FR-KMK-04: 日本語検索（ページ内/サイト内）**  
  形態素 + n-gram のハイブリッド索引を生成し、**アルファベットは従来通り、
  日本語も正しくヒット**。  
  **受入基準**: JP クエリの Top10 リコール ≥ 0.90、F1 ≥ 0.88。

- **FR-KMK-05: LLM 差分提案ワークフロー**  
  指定ファイルの**差分パッチ（unified diff）**を PR コメントとして提示。  
  **受入基準**: 人手レビュー採用率 ≥ 60%、NG 提案再発 ≤ 5%/週。

- **FR-KMK-06: DocLint/Links/PlantUML**  
  PlantUML 構文検証、画像/相対リンク/外部リンクの健全性チェック。  
  **受入基準**: 断リンク 0、UML 構文エラー自動検知率 100%。

- **FR-KMK-07: CI ゲート/公開**  
  PR で FR-KMK-01..06 を実行、合格時のみ Pages へ **自動公開**。  
  **受入基準**: フル実行時間 ≤ 10 分、再実行で**決定的**（非フレーク）。

---

## 6. 非機能要件（NFR 概念レベル）
- **NFR-KMK-01 再現性**: 同一コミットで**決定的**結果。乱数/LLM は seed/プロンプト固定。
- **NFR-KMK-02 性能**: 1,000 ファイルで 10 分以内、10,000 ファイルで 60 分以内の nightly。
- **NFR-KMK-03 可観測性**: すべての検査でメトリクス/ログ/アーティファクト保存（WORM）。
- **NFR-KMK-04 拡張容易性**: ルール/語彙/テンプレを**設定ファイル差し替え**で切替可能。
- **NFR-KMK-05 国際化**: 日本語/英語混在を前提（検索・体裁・禁則処理）。
- **NFR-KMK-06 信頼性**: CI 実行失敗の自己診断と**再試行**、外部依存の**デグレード運用**。
- **NFR-KMK-07 セキュリティ/法務**: 秘密情報の誤公開防止（denylist/PII 検出、PR ブロック）。

---

## 7. 制約 / 前提（CN 概念レベル）
- **CN-KMK-01**: Markdown（.md）と Obsidian 表示に**完全整合**。FrontMatter は**フラット 1 段**。
- **CN-KMK-02**: `refines/satisfies/depends_on/integrates_with/constrains/conflicts_with/supersedes` のみ使用。配列は**文字列 ID のみ**。
- **CN-KMK-03**: GitHub Actions と GitHub Pages を**標準実装**とする（他 CI/CD は拡張）。

---

## 8. 成功指標（KPI/KSF）
- DocLint での**初回合格率 ≥ 85%**（テンプレ利用時）。
- 重要ファイルの**トレース欠落 0**（リリース分岐時）。
- JP クエリでの**検索満足度 ≥ 4.2/5**（月次サーベイ）。
- PR→公開の**平均リードタイム 50% 削減**。

---

## 9. リスクと軽減策
- **R1**: 日本語検索の分かち書き差異 → **形態素 × n-gram** の二重化、辞書チューニング。
- **R2**: LLM 提案の品質ばらつき → ルール/プロンプト固定、**評価セット回帰**、Human-in-the-loop。
- **R3**: 大規模リポジトリの実行時間 → **差分実行/並列化/キャッシュ**。
- **R4**: 公開事故 → 機密検知 + 承認フロー + **リリースブランチ限定公開**。

---

## 10. ロードマップ（MVP → v1.0）
- **Phase 0: 設計の負債先潰し**（2 週）  
  FrontMatter 規約/ID 体系/語彙 `_vocabulary.yml`、テンプレ初期群。
- **Phase 1: MVP（4–6 週）**  
  FR-01..07 の最小実装、`docops_cli` スケルトン、PR 最小ゲート、Pages 公開。
- **Phase 2: JP 検索強化 & トレース品質**（3–4 週）  
  形態素×n-gram、本番サンプルでの P/R チューニング、入口トレース精度改善。
- **Phase 3: v1.0 ハードニング**（2–3 週）  
  可観測性/安全対策/WORM ログ、回帰評価セット、テンプレの業務領域拡張（ロボット/IoT）。

---

## 11. 入口トレース（初期案）
- **CR-KMK-00** satisfies **BG-KMK-01..05**  
- **CR-KMK-00** constrains **RS/HLF/FR/NFR/CN** の各章における ID 体系・FrontMatter 規約。

---

## 12. 付録 A: 最小フォルダ構成（提案）
```
.
├─ docs/
│  ├─ 00_concept/ CR-Kumiki_concept_requirements.md
│  ├─ 10_requirements/ (RS/HLF/FR/NFR/CN)
│  ├─ 20_design/
│  ├─ 30_test/
│  ├─ 40_ops/
│  ├─ adr/ ADR-000-template.md
│  └─ trace/ TRACE-index.md
├─ tools/ docops_cli/
└─ .github/workflows/ docops_min.yml
```

## 13. 付録 B: 用語
- **DocOps**: Docs-as-Code を CI/CD に統合し、生成・検証・公開まで自動化する運用。
- **入口トレース**: 要求各層（RS/HLF/FR/NFR/CN）への出入口リンクを FrontMatter で維持する方式。
- **WORM**: Write Once Read Many。監査用の不可変ログ保全。

---

> 次ステップ：この CR を基に **RS/HLF/NFR/CN** の初版スケルトンを分割生成し、`docops_cli` の MVP を接続する。
