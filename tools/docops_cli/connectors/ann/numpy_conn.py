# tools/docops_cli/connectors/ann/numpy_conn.py
import numpy as np, os, json
from typing import List, Tuple
from .base import ANNConnector

class NumpyExactANN(ANNConnector):
    def __init__(self, dim: int, metric: str = "ip"):
        super().__init__(dim, metric)
        self.X = None
        self.ids = []

    def _score(self, Q):
        if self.metric == "ip" or self.metric == "cos":
            return Q @ self.X.T
        elif self.metric == "l2":
            # negative L2 for ranking
            Q2 = (Q**2).sum(axis=1, keepdims=True)
            X2 = (self.X**2).sum(axis=1, keepdims=True).T
            return -(Q2 - 2*Q@self.X.T + X2)
        else:
            raise ValueError("unknown metric")

    def fit(self, vectors: np.ndarray, ids: List[str]) -> None:
        self.X = vectors.astype(np.float32)
        self.ids = list(ids)

    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        if self.X is None:
            self.fit(vectors, ids); return
        self.X = np.vstack([self.X, vectors.astype(np.float32)])
        self.ids.extend(ids)

    def search(self, queries: np.ndarray, topk: int) -> List[List[Tuple[str, float]]]:
        scores = self._score(queries.astype(np.float32))
        idx = np.argpartition(-scores, kth=min(topk-1, scores.shape[1]-1), axis=1)[:, :topk]
        # refine ordering
        out = []
        for i in range(scores.shape[0]):
            order = idx[i][np.argsort(-scores[i, idx[i]])]
            out.append([(self.ids[j], float(scores[i, j])) for j in order])
        return out

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        np.save(os.path.join(path, "vecs.npy"), self.X)
        with open(os.path.join(path, "ids.json"), "w", encoding="utf-8") as f:
            json.dump(self.ids, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        self.X = np.load(os.path.join(path, "vecs.npy")).astype(np.float32)
        import json
        with open(os.path.join(path, "ids.json"), "r", encoding="utf-8") as f:
            self.ids = json.load(f)
