"""
Base embedder abstract class
"""
from abc import ABC, abstractmethod
from typing import List
import numpy as np


class BaseEmbedder(ABC):
    """Abstract base class for text embedders"""
    
    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of text strings
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            Embedding matrix as numpy array (batch_size, embedding_dim)
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this embedder"""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name/identifier of the embedding model"""
        pass
