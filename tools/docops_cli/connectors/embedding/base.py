# tools/docops_cli/connectors/embedding/base.py
from abc import ABC, abstractmethod
from typing import List
import numpy as np

class EmbeddingProvider(ABC):
    dim: int

    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
