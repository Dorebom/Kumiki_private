# Kumiki

> 既存リポジトリに“あと付け”できる DocOps アドオン  
> FrontMatter に基づく **検証・トレース・検索** を追加し、公開は GitHub Pages/Actions と連携。

!!! info
    このページは Kumiki ドキュメントサイトの**ホーム**です。  
    左のナビが表示されない／リンクが壊れる場合は、`site_url` や相対リンク設定を見直してください。

## はじめに

- **概要**：Kumiki の目的と全体像… → [Kumiki 概要](00_overview/RS-00_overview.md)
- **要件**：HLF/FR/NFR/CN … →
  - [HLF](02_requirements/RS-HLF.md) /
    [FR](02_requirements/RS-FR.md) /
    [NFR](02_requirements/RS-NFR.md) /
    [CN](02_requirements/RS-constraints.md)
- **設計**：アーキテクチャ … → [Architecture](03_design/DD-03.1_arch_overview.md)
- **テスト**：戦略/ケース … → [Test Overview](04_test/overview.md)

## 使い方（最短）

1. 既存リポに `kumiki/` を**サブモジュール追加**  
2. `kumiki/config/sources.yml` で**探索範囲**を宣言  
3. CLI: `python kumiki/cli/kumiki_cli.py --check --graph`  
4. Pages: `pages.yml` で **GitHub Pages に公開**

詳細は [README（使い方）](../README.md) を参照。

## よくあるトラブル

- **リンクが 404** → ルート相対 `/path` を相対リンクに修正。`site_url` を `https://<user>.github.io/<repo>/` に設定。
- **トップページが出ない** → この `index.md` を置くか、`nav` の**先頭**に `index.md` を追加。

---

_最終更新: 2025-08-31_
