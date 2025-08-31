# tools/docops_cli/connectors/ann/scann_conn.py
# Optional: requires 'scann' package; skeleton only.
import numpy as np, os, json
from typing import List, Tuple
from .base import ANNConnector
try:
    import scann
except Exception as e:
    scann = None

class ScannANN(ANNConnector):
    def __init__(self, dim: int, metric: str = "ip", leaves: int = 2000, reordering: int = 100):
        super().__init__(dim, metric)
        if scann is None:
            raise RuntimeError("scann is not installed")
        self.searcher = None
        self.ids = []
        self.leaves = leaves
        self.reordering = reordering

    def fit(self, vectors: np.ndarray, ids: List[str]) -> None:
        if self.metric in ("ip","cos"):
            dist = "dot_product"
        elif self.metric == "l2":
            dist = "squared_l2"
        else:
            raise ValueError("metric must be ip|l2|cos")
        self.ids = list(ids)
        self.searcher = scann.scann_ops_pybind.builder(vectors.astype(np.float32), 10, dist)            .tree(num_leaves=self.leaves, num_leaves_to_search=100)            .score_ah(2, anisotropic_quantization_threshold=0.2)            .reorder(self.reordering)            .build()

    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        raise NotImplementedError("ScaNN dynamic add not supported in this stub")

    def search(self, queries: np.ndarray, topk: int):
        out = []
        for q in queries.astype(np.float32):
            idx, dists = self.searcher.search(q, final_num_neighbors=topk)
            out.append([(self.ids[int(i)], float(-d)) for i, d in zip(idx, dists)])
        return out

    def save(self, path: str) -> None:
        # ScaNN python builder doesn't have a trivial save in this stub
        pass

    def load(self, path: str) -> None:
        # Not implemented
        pass
