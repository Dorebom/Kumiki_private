# tools/docops_cli/connectors/ann/annoy_conn.py
import numpy as np, os, json
from typing import List, Tuple
from .base import ANNConnector
try:
    from annoy import AnnoyIndex
except Exception as e:
    AnnoyIndex = None

class AnnoyANN(ANNConnector):
    def __init__(self, dim: int, metric: str = "ip", n_trees: int = 50, search_k: int = 0):
        # Annoy supports 'angular' (cosine) or 'euclidean'
        if AnnoyIndex is None:
            raise RuntimeError("annoy is not installed")
        if metric in ("ip","cos"):
            metric = "angular"
        elif metric == "l2":
            metric = "euclidean"
        else:
            raise ValueError("metric must be ip|l2|cos")
        super().__init__(dim, metric)
        self.metric = metric
        self.index = AnnoyIndex(dim, metric)
        self.ids = []
        self._built = False
        self.n_trees = n_trees
        self.search_k = search_k

    def fit(self, vectors: np.ndarray, ids: List[str]) -> None:
        self.index.unbuild()
        self.index = AnnoyIndex(self.dim, self.metric)
        self.ids = []
        for i, (vec, _id) in enumerate(zip(vectors.astype(np.float32), ids)):
            self.index.add_item(i, vec.tolist())
            self.ids.append(_id)
        self.index.build(self.n_trees)
        self._built = True

    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        base = len(self.ids)
        for i, (vec, _id) in enumerate(zip(vectors.astype(np.float32), ids)):
            self.index.add_item(base + i, vec.tolist())
            self.ids.append(_id)
        # rebuild to include new items
        self.index.build(self.n_trees)
        self._built = True

    def search(self, queries: np.ndarray, topk: int) -> List[List[Tuple[str, float]]]:
        if not self._built: self.index.build(self.n_trees); self._built=True
        out = []
        for q in queries.astype(np.float32):
            idxs = self.index.get_nns_by_vector(q.tolist(), topk, search_k=self.search_k, include_distances=True)
            ids = [self.ids[i] for i in idxs[0]]
            # Annoy returns distance; convert to score (negative dist for euclidean, 1-dist for angular approx)
            dists = idxs[1]
            if self.metric == "euclidean":
                scores = [-float(d) for d in dists]
            else:
                scores = [1.0 - float(d) for d in dists]
            out.append(list(zip(ids, scores)))
        return out

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        self.index.save(os.path.join(path, "index.ann"))
        with open(os.path.join(path, "ids.json"), "w", encoding="utf-8") as f:
            json.dump(self.ids, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        self.index = AnnoyIndex(self.dim, self.metric)
        self.index.load(os.path.join(path, "index.ann"))
        with open(os.path.join(path, "ids.json"), "r", encoding="utf-8") as f:
            self.ids = json.load(f)
        self._built = True
