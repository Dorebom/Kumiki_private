# tools/docops_cli/connectors/embedding/local_mini.py
import numpy as np, hashlib, struct, random
from typing import List
from .base import EmbeddingProvider

class LocalMiniEmbedding(EmbeddingProvider):
    def __init__(self, dim: int = 256, seed: int = 42):
        self.dim = dim
        random.seed(seed)
        # Stable random projection matrix using seed
        rng = np.random.default_rng(seed)
        self.P = rng.normal(0, 1.0/np.sqrt(dim), size=(dim, 2048)).astype(np.float32)

    def _feats(self, text: str) -> np.ndarray:
        # Token hash bag of chars (cheap & deterministic)
        vec = np.zeros((2048,), dtype=np.float32)
        for ch in text:
            h = int(hashlib.blake2b(ch.encode('utf-8'), digest_size=4).hexdigest(), 16) % 2048
            vec[h] += 1.0
        return vec

    def embed(self, texts: List[str]) -> np.ndarray:
        X = np.stack([self._feats(t) for t in texts], axis=0) # (N, 2048)
        Y = X @ self.P.T  # (N, dim)
        # L2 normalize for cosine/IP equivalence
        norms = np.linalg.norm(Y, axis=1, keepdims=True) + 1e-8
        return (Y / norms).astype(np.float32)

    def name(self) -> str:
        return "local-mini"
