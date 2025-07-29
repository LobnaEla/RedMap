"""
HuggingFace embedder implementation
"""
import logging
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from .base import BaseEmbedder

logger = logging.getLogger(__name__)


class HuggingFaceEmbedder(BaseEmbedder):
    """HuggingFace Sentence Transformers embedder"""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize HuggingFace embedder
        
        Args:
            model_name: Name of the sentence transformer model
            device: Device to run on ('cpu', 'cuda', etc.). Auto-detected if None
            batch_size: Batch size for embedding generation
        """
        self._model_name = model_name
        self.batch_size = batch_size
        
        logger.info(f"Loading HuggingFace model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dimension}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        embeddings = self.model.encode([text], convert_to_numpy=True)
        return embeddings[0]
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of text strings
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            Embedding matrix as numpy array (batch_size, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        logger.debug(f"Embedding batch of {len(texts)} texts")
        embeddings = self.model.encode(
            texts, 
            batch_size=self.batch_size,
            convert_to_numpy=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings
    
    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this embedder"""
        return self.model.get_sentence_embedding_dimension()
    
    @property
    def model_name(self) -> str:
        """Return the name/identifier of the embedding model"""
        return self._model_name
