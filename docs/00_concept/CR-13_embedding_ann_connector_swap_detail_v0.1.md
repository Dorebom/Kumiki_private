---
id: CR-KMK-13
title: "CR-13: Embedding/ANNコネクタの差替え — 詳細仕様"
type: concept_requirements_detail
status: draft
version: 0.1.0
created: 2025-08-31
updated: 2025-08-31
owner: "PMO"
tags: [kumiki, docops, concept, cr13, embedding, ann, faiss, scann, annoy, vendor-neutral]
canonical_parent: "CR-KMK-00"
refines: ["CR-KMK-00"]
satisfies: ["BG-KMK-01","BG-KMK-02","BG-KMK-05"]
depends_on: ["CR-KMK-03","CR-KMK-06","CR-KMK-10","CR-KMK-11"]
integrates_with: ["STD-GHA-01"]
constrains: ["CN-KMK-01","CN-KMK-02","CN-KMK-03"]
conflicts_with: []
supersedes: []
---

# CR-13: Embedding/ANNコネクタの差替え — 詳細仕様

> **G**: ベンダーロックインを回避し、**IF固定**で **FAISS / ScaNN / Annoy / NumPy(Exact)** 等へ**差替え可能**にする。  
> **AC**: 差替え後も **Top3率（Hit@3）劣化 ≤ 3pt**。

---

## 1. 目的
- 検索（CR-03）・影響解析（CR-06）等で用いる **埋め込み＆近傍探索**の実装を**プラガブル**にし、運用環境・性能要件に応じて**差替え**できるようにする。

---

## 2. アーキテクチャ（IF固定）

```
embedder: EmbeddingProvider
  - embed(texts: List[str]) -> np.ndarray[float32]  # 形状: (N, D), Dは provider.dim
  - dim: int
  - name(): str

ann: ANNConnector
  - fit(vectors: np.ndarray, ids: List[str]) -> None
  - add(vectors: np.ndarray, ids: List[str]) -> None
  - search(queries: np.ndarray, topk: int) -> List[List[Tuple[str, float]]]
  - save(path: str) -> None
  - load(path: str) -> None
  - metric: "ip"|"l2"|"cos"
```

- **互換要件**: 同じ `embedder.dim` と `ann.metric` を満たせば**相互交換可能**。  
- **提供コネクタ**: `numpy`（Exact）, `faiss_flat`（IndexFlatIP/L2）, `annoy`（Angular/L2）, `scann`（近似; オプション）。

---

## 3. 設定（`ann_connectors.yml`）
- 例：
```yaml
provider:
  name: local-mini
  dim: 256
  seed: 42
ann:
  backend: faiss_flat   # numpy|faiss_flat|annoy|scann
  metric: ip            # ip|l2|cos
  params:
    faiss:
      nprobe: 1
    annoy:
      n_trees: 50
      search_k: 0
    scann:
      leaves: 2000
      reordering: 100
eval:
  topk: 3
  max_queries: 200
  degrade_tolerance: 0.03
```

---

## 4. ベンチマーク／合否
- **Baseline**: `numpy`（全探索）で Hit@3 を算出。  
- **Target**: 指定バックエンドで Hit@3 を算出。  
- **合否**: `Hit@3_target ≥ Hit@3_base - 0.03` を満たすこと。

---

## 5. 可観測性（CR-11連携）
- `kumiki.ann.hit_at_1_ratio`, `hit_at_3_ratio`, `mrr`, `build_time_ms`, `qps`, `degrade_points` を記録。

---

## 6. CI（最小）
- `.github/workflows/docops_ann_swap.yml` で **connector matrix** を回し、劣化 ≤ 3pt を自動判定。FAISS/Annoy は optional install。

---

## 7. 受入基準（AC）
- **AC-01**: いずれのバックエンドに差替えても **Top3率劣化 ≤ 3pt**。  
- **AC-02**: IF（メソッド・引数・返り値）が**不変**である。

---

## 8. トレース
- **satisfies**: BG-KMK-01（工数削減）, BG-KMK-02（品質/性能）, BG-KMK-05（公開運用）  
- **depends_on**: CR-03（検索）, CR-06（影響解析）, CR-10（CI）  
- **constrains**: CN-KMK-01..03
