# tools/docops_cli/connectors/ann/base.py
from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np

class ANNConnector(ABC):
    metric: str  # "ip"|"l2"|"cos"

    def __init__(self, dim: int, metric: str = "ip"):
        self.dim = dim
        self.metric = metric

    @abstractmethod
    def fit(self, vectors: np.ndarray, ids: List[str]) -> None: ...

    @abstractmethod
    def add(self, vectors: np.ndarray, ids: List[str]) -> None: ...

    @abstractmethod
    def search(self, queries: np.ndarray, topk: int) -> List[List[Tuple[str, float]]]: ...

    @abstractmethod
    def save(self, path: str) -> None: ...

    @abstractmethod
    def load(self, path: str) -> None: ...
