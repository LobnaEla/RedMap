"""
Base vector store abstract class
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np


@dataclass
class SearchResult:
    """Represents a search result from vector store"""
    id: str
    score: float
    metadata: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"SearchResult(id={self.id}, score={self.score:.3f})"


class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    def add_documents(
        self, 
        ids: List[str], 
        embeddings: np.ndarray, 
        metadata: List[Dict[str, Any]]
    ) -> None:
        """
        Add documents to the vector store
        
        Args:
            ids: List of document IDs
            embeddings: Document embeddings (shape: [n_docs, embedding_dim])
            metadata: List of metadata dictionaries for each document
        """
        pass
    
    @abstractmethod
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score (optional)
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    def delete_all(self) -> None:
        """Delete all documents from the vector store"""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Return the number of documents in the vector store"""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if the vector store is healthy and accessible"""
        pass
