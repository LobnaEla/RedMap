"""
Weaviate vector store implementation for v4 client
"""

from urllib.parse import urlparse
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import weaviate
from weaviate.collections.classes.config import Configure

from .base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class WeaviateVectorStore(BaseVectorStore):
    """Weaviate implementation of vector store using v4 client"""

    def __init__(
        self, url: str = "http://weaviate:5000", class_name: str = "MitreTechnique"
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
            parsed = urlparse(self.url)
            host = parsed.hostname or "weaviate"
            port = parsed.port or 5000

            # Connect using v4 client
            self.client = weaviate.connect_to_local(host=host, port=port)

            logger.info(f"Connected to Weaviate at {url}")

            # Ensure schema exists
            self._ensure_schema()

        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            raise

    def _ensure_schema(self) -> None:
        """Ensure the MITRE technique schema exists"""
        try:
            if not self.client.collections.exists(self.class_name):
                logger.info(f"Creating Weaviate collection: {self.class_name}")

                collection = self.client.collections.create(
                    name=self.class_name,
                    vector_config=Configure.Vectors.self_provided(),
                )
                logger.info(
                    f"Collection {self.class_name} created successfully with vector configuration"
                )
            else:
                logger.debug(f"Collection {self.class_name} already exists")
        except Exception as e:
            logger.error(f"Failed to create/check schema: {e}")
            raise

    def add_documents(
        self, ids: List[str], embeddings: np.ndarray, metadata: List[Dict[str, Any]]
    ) -> None:
        if len(ids) != len(metadata) or len(embeddings) != len(ids):
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

                    # Remove 'embedding' key if present in meta
                    if "embedding" in meta:
                        del meta["embedding"]

                    def safe_list(val):
                        # Convert numpy arrays, None, or single values to list of strings
                        if val is None:
                            return []
                        if isinstance(val, np.ndarray):
                            return [str(x) for x in val.tolist()]
                        if isinstance(val, (list, tuple)):
                            return [str(x) for x in val]
                        return [str(val)]

                    def safe_str(val):
                        if val is None:
                            return ""
                        if isinstance(val, (list, tuple, np.ndarray)):
                            return ", ".join([str(x) for x in val])
                        return str(val)

                    properties = {
                        "technique_id": safe_str(meta.get("id", doc_id)),
                        "name": safe_str(meta.get("name", "")),
                        "description": safe_str(meta.get("description", "")),
                        "url": safe_str(meta.get("url", "")),
                        "platforms": safe_list(meta.get("platforms", [])),
                        "kill_chain_phases": safe_list(
                            meta.get("kill_chain_phases", [])
                        ),
                        "data_sources": safe_list(meta.get("data_sources", [])),
                        "detection": safe_str(meta.get("detection", "")),
                    }

                    # Ensure embedding is a list for Weaviate
                    if hasattr(embedding, "tolist"):
                        vector_data = embedding.tolist()
                    elif isinstance(embedding, list):
                        vector_data = embedding
                    else:
                        vector_data = list(embedding)
                    batch.add_object(
                        collection=self.class_name,
                        properties=properties,
                        vector=vector_data,
                    )

            logger.info("All objects inserted successfully using dynamic batch.")

        except Exception as e:
            logger.error(f"Failed to add documents to Weaviate: {e}")
            raise

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
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
            # Print the query embedding for debugging
            logger.info(
                f"Query embedding (first 10 values): {query_embedding[:10] if hasattr(query_embedding, '__getitem__') else query_embedding}"
            )
            # Ensure query_embedding is a list of floats
            if isinstance(query_embedding, np.ndarray):
                query_vector = query_embedding.tolist()
            elif isinstance(query_embedding, list):
                query_vector = query_embedding
            else:
                raise ValueError("query_embedding must be a numpy array or a list")
            # Always use score_threshold=None for debugging
            response = collection.query.near_vector(
                near_vector=query_vector,
                limit=top_k,
                return_metadata=weaviate.classes.query.MetadataQuery(
                    score=True, distance=True
                ),
            )
            logger.debug(
                f"Raw Weaviate response: {len(response.objects)} objects returned"
            )
            results = []
            for i, obj in enumerate(response.objects):
                distance = (
                    obj.metadata.distance if obj.metadata.distance is not None else 1.0
                )
                similarity = max(0.0, 1.0 - distance)
                logger.debug(
                    f"Object {i}: distance={distance}, similarity={similarity}, score_threshold={score_threshold}"
                )
                # Do not filter by score_threshold for debugging
                metadata = dict(obj.properties)
                metadata["id"] = obj.properties.get("technique_id", "")
                result = SearchResult(
                    id=obj.properties.get("technique_id", ""),
                    score=similarity,
                    metadata=metadata,
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
