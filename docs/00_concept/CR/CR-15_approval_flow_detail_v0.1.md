---
id: CR-KMK-15
title: "CR-15: 承認フローと自動マージ禁止条件 — 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr15, approval, governance, automerge, compliance]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-05"]
depends_on: ["CR-KMK-01","CR-KMK-02","CR-KMK-03","CR-KMK-04","CR-KMK-05","CR-KMK-06","CR-KMK-07","CR-KMK-08","CR-KMK-09","CR-KMK-10","CR-KMK-11","CR-KMK-12","CR-KMK-13","CR-KMK-14"]
integrates_with: ["STD-GHA-01","STD-PAGES-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-15: 承認フローと自動マージ禁止条件 — 詳細仕様

> **G**: クリティカル変更で **手動承認** を必須化し、**自動マージを抑止**する。  
> **AC**: **ルール逸脱 0**、**運用監査で指摘 0**。

---

## 1. 目的
- 文書/規約/公開に影響する **クリティカル変更** を自動検出し、**人手承認（Code Owners）** を必須化。  
- 条件を満たさない PR では **自動マージ（automerge）を禁止**。監査台帳（CR-05）へ **不可変ログ** を記録。

---

## 2. スコープ / 非スコープ
### スコープ
- クリティカル条件の定義・検出、PR ステータス判定、**自動マージ抑止**、**承認証跡のWORM保全**。

### 非スコープ
- 組織の GitHub Branch Protection 設定の作成はガイドのみ（適用はリポ管理者の操作）。

---

## 3. クリティカル条件（デフォルト）
- **ファイル種別/パス**: `docs/**/security/**`, `docs/**/policy/**`, `docs/**/std/**`, `.github/**`, `tools/docops_cli/**`。  
- **FrontMatter 変更**: `id/created/updated/canonical_parent` の変更、`status: published` への昇格、`constrains/satisfies` の削除。  
- **検査結果**: `DocLint.errors>0`、`SecScan.high>0`、`Trace.cycles>0`、`IDCheck.duplicates+broken_refs>0`。  
- **差分規模**: 変更行数 > 500 行 or 変更ファイル数 > 30（大規模変更）。  
- **公開に直結**: `CR-10 Gate` ルール/公開ワークフローの改変。

> ルールは `tools/docops_cli/config/approval_rules.yml` で運用可能。

---

## 4. フロー
1. PR 作成/更新 → **Approval Gate**（本CRのチェック）を起動。  
2. クリティカル検知 → `require_manual=true`。`needs-approval` ラベルを付与し **automerge 無効化**。  
3. **Code Owners 承認**（GitHub 標準）＋ `approved:human` ラベル or `/approve` コメント（任意）→ Gate 再実行で **Pass**。  
4. main マージ後：**WORM 台帳（CR-05）へ承認イベント追記**。

---

## 5. 入出力
### 入力
- PR 差分（`git diff`）、GitHub Event（`$GITHUB_EVENT_PATH`）、各 CR のレポート（`artifacts/**`）。
### 出力
- `artifacts/approval/report.json`（schema: `approval_report.json`）  
- `artifacts/approval/audit_event.json`（WORM 追記用の最小イベント）

---

## 6. 判定ロジック（概要）
- `risk = low | medium | critical` を算出し、`require_manual = (risk == critical)`。  
- `can_automerge = (risk == low) AND 全ての必須チェックPass AND 'automerge'ラベルあり`。  
- `approved_by_human = 'approved:human' ラベル` が存在すれば Gate は **Pass**（ただし他チェックが Pass 前提）。

---

## 7. GitHub 設定ガイド（推奨）
- **Branch protection (main)**:  
  - Require pull request before merging  
  - Require approvals: **Require review from Code Owners**（最小 1）  
  - Require status checks: `kumiki_ci_publish`, `docops_secscan`, `approval_gate`（本CR）  
  - Disallow force pushes, linear history 推奨  
- **Auto-merge**: リポ設定で有効。ただし本 Gate が `can_automerge=false` の場合は status fail で抑止。

---

## 8. 受入基準（AC）
- **AC-01**: ルール定義に対する逸脱 0（Gate ロジックは `approval_rules.yml` に従う）。  
- **AC-02**: 監査（CR-05）にて **承認イベントが欠落 0**・ハッシュ整合性 OK・**指摘 0**。

---

## 9. トレース
- **satisfies**: BG-KMK-05（常時公開可能・統制）  
- **depends_on**: CR-05（WORM）, CR-09（SecScan）, CR-10（CIゲート）, CR-11（メトリクス）  
- **constrains**: CN-KMK-01..03
