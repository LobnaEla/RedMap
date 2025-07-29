"""
RAG Engine for MITRE ATT&CK technique retrieval
"""
import logging
from typing import List, Optional

from embeddings import BaseEmbedder
from vectorstore import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG Engine that combines embedding and vector search for MITRE technique retrieval"""
    
    def __init__(
        self, 
        embedder: BaseEmbedder,
        vector_store: BaseVectorStore
    ):
        """
        Initialize RAG Engine
        
        Args:
            embedder: Text embedder instance
            vector_store: Vector store instance
        """
        self.embedder = embedder
        self.vector_store = vector_store
        
        logger.info(f"RAG Engine initialized with {embedder.model_name} embedder")
    
    def retrieve_techniques(
        self, 
        query: str, 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Retrieve relevant MITRE techniques for a given query
        
        Args:
            query: Input text (e.g., CTI report chunk)
            top_k: Number of techniques to retrieve
            score_threshold: Minimum similarity score (optional)
            
        Returns:
            List of SearchResult objects with relevant techniques
        """
        logger.debug(f"Retrieving techniques for query: {query[:100]}...")
        
        # Generate embedding for the query
        query_embedding = self.embedder.embed_text(query)
        
        # Search for similar techniques
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            score_threshold=score_threshold
        )
        
        logger.info(f"Retrieved {len(results)} techniques for query")
        return results
    
    def get_technique_by_id(self, technique_id: str) -> Optional[SearchResult]:
        """
        Get a specific technique by its MITRE ID
        
        Args:
            technique_id: MITRE technique ID (e.g., "T1001")
            
        Returns:
            SearchResult object if found, None otherwise
        """
        # This is a simple implementation - in practice, you might want to
        # add a separate index for exact ID lookups
        results = self.vector_store.search(
            query_embedding=self.embedder.embed_text(technique_id),
            top_k=50  # Get more results to find exact match
        )
        
        for result in results:
            if result.metadata.get("id") == technique_id:
                return result
        
        return None
    
    def batch_retrieve(
        self, 
        queries: List[str], 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[List[SearchResult]]:
        """
        Retrieve techniques for multiple queries
        
        Args:
            queries: List of input texts
            top_k: Number of techniques to retrieve per query
            score_threshold: Minimum similarity score (optional)
            
        Returns:
            List of lists containing SearchResult objects for each query
        """
        logger.info(f"Batch retrieving techniques for {len(queries)} queries")
        
        results = []
        for i, query in enumerate(queries):
            query_results = self.retrieve_techniques(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold
            )
            results.append(query_results)
            
            if (i + 1) % 10 == 0:
                logger.debug(f"Processed {i + 1}/{len(queries)} queries")
        
        return results
