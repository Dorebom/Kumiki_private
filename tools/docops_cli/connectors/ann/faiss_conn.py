# tools/docops_cli/connectors/ann/faiss_conn.py
import numpy as np, os, json
from typing import List, Tuple
from .base import ANNConnector
try:
    import faiss
except Exception as e:
    faiss = None

class FaissFlatANN(ANNConnector):
    def __init__(self, dim: int, metric: str = "ip"):
        super().__init__(dim, metric)
        if faiss is None:
            raise RuntimeError("faiss is not installed")
        if metric == "ip" or metric == "cos":
            self.index = faiss.IndexFlatIP(dim)
        elif metric == "l2":
            self.index = faiss.IndexFlatL2(dim)
        else:
            raise ValueError("metric must be ip|l2|cos")
        self.ids = []

    def fit(self, vectors: np.ndarray, ids: List[str]) -> None:
        self.index.reset()
        self.add(vectors, ids)

    def add(self, vectors: np.ndarray, ids: List[str]) -> None:
        self.index.add(vectors.astype(np.float32))
        self.ids.extend(ids)

    def search(self, queries: np.ndarray, topk: int) -> List[List[Tuple[str, float]]]:
        D, I = self.index.search(queries.astype(np.float32), topk)
        out = []
        for i in range(I.shape[0]):
            out.append([(self.ids[int(j)], float(D[i, k])) for k, j in enumerate(I[i]) if j != -1])
        return out

    def save(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "ids.json"), "w", encoding="utf-8") as f:
            json.dump(self.ids, f, ensure_ascii=False)

    def load(self, path: str) -> None:
        self.index = faiss.read_index(os.path.join(path, "index.faiss"))
        with open(os.path.join(path, "ids.json"), "r", encoding="utf-8") as f:
            self.ids = json.load(f)
