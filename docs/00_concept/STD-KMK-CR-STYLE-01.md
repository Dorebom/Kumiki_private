---
id: STD-KMK-CR-STYLE-01
title: CRスタイルガイド（G/I/O/ACの推奨粒度）
type: standard
status: draft
version: 0.1.0
created: '2025-08-31'
updated: '2025-09-02'
owner: PMO
tags:
- styleguide
- cr-format
depends_on:
- STD-KMK-FM-01
- STD-KMK-ID-01
---

# CRドキュメント記述スタイル（従来CRスタイル準拠）



> G/I/O（Goal/Input/Output）と AC（受入基準）を明示し、FrontMatterはフラット1段・必須キーを満たす。

## 1. 推奨フォーマット

- 見出し: `CR-XX: <短い要約>`

- ブロック: **G / I / O / AC** を箇条書きで記載

- 参照: `depends_on/refines/satisfies/...` は ID で列挙

## 2. 例

- CR-01: テンプレート自動展開とDocLint — G/I/O/AC を簡潔に