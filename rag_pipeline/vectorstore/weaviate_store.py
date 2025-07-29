"""
Weaviate vector store implementation for v4 client
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import weaviate
import weaviate.classes as wvc
from weaviate.classes.data import DataObject

from .base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class WeaviateVectorStore(BaseVectorStore):
    """Weaviate implementation of vector store using v4 client"""
    
    def __init__(
        self, 
        url: str = "http://localhost:8080",
        class_name: str = "MitreTechnique"
    ):
        """
        Initialize Weaviate vector store
        
        Args:
            url: Weaviate instance URL
            class_name: Name of the Weaviate class to use
        """
        self.url = url
        self.class_name = class_name
        
        try:
            # Connect using v4 client
            self.client = weaviate.connect_to_local(
                host="localhost",
                port=8080
            )
            logger.info(f"Connected to Weaviate at {url}")
            
            # Ensure schema exists
            self._ensure_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise
    
    def _ensure_schema(self) -> None:
        """Ensure the MITRE technique schema exists"""
        try:
            # Check if collection exists using v4 API
            if not self.client.collections.exists(self.class_name):
                logger.info(f"Creating Weaviate collection: {self.class_name}")
                
                # Create collection using v4 API with proper vector configuration
                collection = self.client.collections.create(
                    name=self.class_name
                )
                logger.info(f"Collection {self.class_name} created successfully")
            else:
                logger.debug(f"Collection {self.class_name} already exists")
        except Exception as e:
            logger.error(f"Failed to create/check schema: {e}")
            raise
    
    def add_documents(
        self, 
        ids: List[str], 
        embeddings: np.ndarray, 
        metadata: List[Dict[str, Any]]
    ) -> None:
        if len(ids) != len(metadata) or embeddings.shape[0] != len(ids):
            raise ValueError("Length mismatch between ids, embeddings, and metadata")

        logger.info(f"Adding {len(ids)} documents to Weaviate")

        try:
            collection = self.client.collections.get(self.class_name)
            
            # Use dynamic batch for v4 API
            logger.info(f"Inserting {len(ids)} objects using dynamic batch")
            with self.client.batch.dynamic() as batch:
                for doc_id, embedding, meta in zip(ids, embeddings, metadata):
                    if embedding is None or len(embedding) == 0:
                        logger.warning(f"Skipping {doc_id}, invalid embedding")
                        continue

                    properties = {
                        "technique_id": meta.get("id", doc_id),
                        "name": meta.get("name", ""),
                        "description": meta.get("description", ""),
                        "url": meta.get("url", ""),
                        "platforms": meta.get("platforms", []),
                        "kill_chain_phases": meta.get("kill_chain_phases", []),
                        "data_sources": meta.get("data_sources", []),
                        "detection": meta.get("detection", "")
                    }
                    
                    batch.add_object(
                        collection=self.class_name,
                        properties=properties,
                        vector=embedding.tolist()
                    )
            
            logger.info("All objects inserted successfully using dynamic batch.")

        except Exception as e:
            logger.error(f"Failed to add documents to Weaviate: {e}")
            raise

    
    def search(
        self, 
        query_embedding: np.ndarray, 
        top_k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Search for similar documents using v4 API
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            
        Returns:
            List of SearchResult objects
        """
        try:
            collection = self.client.collections.get(self.class_name)
            
            # Perform vector search using v4 API with target_vector
            response = collection.query.near_vector(
                near_vector=query_embedding.tolist(),
                limit=top_k,
                target_vector="default",
                return_metadata=weaviate.classes.query.MetadataQuery(score=True, distance=True)
            )
            
            logger.debug(f"Raw Weaviate response: {len(response.objects)} objects returned")
            
            results = []
            for i, obj in enumerate(response.objects):
                # Convert distance to similarity (v4 returns distance, where 0 = perfect match)
                # We convert distance to similarity: similarity = 1 - distance
                distance = obj.metadata.distance if obj.metadata.distance is not None else 1.0
                similarity = max(0.0, 1.0 - distance)  # Ensure similarity is non-negative
                
                logger.debug(f"Object {i}: distance={distance}, similarity={similarity}, score_threshold={score_threshold}")
                
                # Apply score threshold if specified
                if score_threshold and similarity < score_threshold:
                    logger.debug(f"Filtering out object {i} due to low similarity ({similarity} < {score_threshold})")
                    continue
                
                # Create SearchResult with proper metadata mapping
                metadata = dict(obj.properties)
                metadata["id"] = obj.properties.get("technique_id", "")  # Add id field for compatibility
                
                result = SearchResult(
                    id=obj.properties.get("technique_id", ""),
                    score=similarity,
                    metadata=metadata
                )
                results.append(result)
            
            logger.debug(f"Returning {len(results)} results after filtering")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def count(self) -> int:
        """Get total number of documents"""
        try:
            collection = self.client.collections.get(self.class_name)
            response = collection.aggregate.over_all(total_count=True)
            return response.total_count if response.total_count else 0
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0
    
    def delete_all(self) -> None:
        """Delete all documents from collection"""
        try:
            logger.info(f"Deleting all documents from collection {self.class_name}")
            self.client.collections.delete(self.class_name)
            logger.info("All documents deleted successfully")
            
            # Recreate the collection
            self._ensure_schema()
            
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if Weaviate is healthy"""
        try:
            return self.client.is_ready()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the Weaviate connection"""
        try:
            self.client.close()
            logger.info("Weaviate connection closed")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
