---
id: STD-KMK-00_INDEX
title: Standards Index（Kumiki 標準の親）
version: "1.0"
status: draft
children: ["STD-KMK-FM-01", "STD-KMK-ID-01", "STD-KMK-VOC-01", "STD-KMK-TRACE-01", "STD-KMK-LINT-01", "STD-KMK-REG-01", "STD-KMK-CI-01", "STD-KMK-MKDOCS-01"]
---
# Kumiki 標準インデックス

このページは Kumiki の **標準（STD）群の親** です。子として各標準ドキュメントをぶら下げ、FrontMatter の `parent` ルール（正規親は1つ）を満たします。

## 子ドキュメント（現状: 作成済）
- STD-KMK-FM-01 — FrontMatter 運用標準（Kumiki）
- STD-KMK-ID-01 — ドキュメントID・命名標準（Kumiki）
- STD-KMK-VOC-01 — 語彙・関係語彙標準（Kumiki）
- STD-KMK-TRACE-01 — トレーサビリティ標準（Kumiki）
- STD-KMK-LINT-01 — DocLintルール標準（Kumiki）
- STD-KMK-REG-01 — IDレジストリ標準（Kumiki）
- STD-KMK-CI-01 — DocOps CIゲート標準（Kumiki）
- STD-KMK-MKDOCS-01 — サイト構成・公開標準（Kumiki）

---

## 標準MVPパック（6本）
> まず最優先で整備し、FM/ID/VOCと併せて DocOps の土台を固めます。

- [x] **STD-KMK-FM-01 — FrontMatter 運用標準**
- [x] **STD-KMK-ID-01 — ドキュメントID・命名標準**
- [x] **STD-KMK-VOC-01 — 語彙・関係語彙標準**
- [x] **STD-KMK-TRACE-01 — トレーサビリティ標準**
- [x] **STD-KMK-LINT-01 — DocLintルール標準**
- [x] **STD-KMK-REG-01 — IDレジストリ標準**
- [x] **STD-KMK-CI-01 — DocOps CIゲート標準**
- [x] **STD-KMK-MKDOCS-01 — サイト構成・公開標準**

> 進行中に `children` に登録するのは **作成済みになったタイミング**で行います（unknown_refs回避）。

---

## 拡張パック（将来）
> 実運用を盤石にするための追加標準。作成が決まり次第、順次着手。

- [ ] **STD-KMK-OBS-01 — Obsidian連携標準**
- [ ] **STD-KMK-TPL-01 — ドキュメント雛形標準**
- [ ] **STD-KMK-DIAG-01 — 図表スタイル（PlantUML）標準**
- [ ] **STD-KMK-VERSION-01 — 版管理・状態遷移標準**
- [ ] **STD-KMK-CHANGE-01 — 変更管理・ADR標準**
- [ ] **STD-KMK-LOCK-01 — docops.lock スキーマ標準**

---

## 運用メモ
- 新しい Standard を作成したら、各ファイルの FM に `parent: STD-KMK-00_INDEX` を付与し、本ページの `children` と本節のチェックリストを更新。  
- 未作成IDを `children` に入れると CI で `unknown_refs` が発生するため、**チェックリストのみ**で管理します。
