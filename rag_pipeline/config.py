"""
Configuration management for RAG Pipeline
"""
import os
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration class for RAG Pipeline"""
    
    # MITRE ATT&CK data
    mitre_csv_path: str = "data/MITRE_ATT&CK/enterprise-attack.csv"
    
    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_batch_size: int = 32
    
    # Weaviate
    weaviate_url: str = "http://localhost:8080"
    weaviate_class_name: str = "MitreTechnique"
    
    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        return cls(
            mitre_csv_path=os.getenv("MITRE_CSV_PATH", cls.mitre_csv_path),
            embedding_model=os.getenv("EMBEDDING_MODEL", cls.embedding_model),
            embedding_batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", str(cls.embedding_batch_size))),
            weaviate_url=os.getenv("WEAVIATE_URL", cls.weaviate_url),
            weaviate_class_name=os.getenv("WEAVIATE_CLASS_NAME", cls.weaviate_class_name),
            top_k=int(os.getenv("TOP_K", str(cls.top_k))),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", str(cls.similarity_threshold))),
            log_level=os.getenv("LOG_LEVEL", cls.log_level),
        )
    
    def get_mitre_csv_path(self, base_path: Optional[str] = None) -> Path:
        """Get absolute path to MITRE CSV file"""
        mitre_path = Path(self.mitre_csv_path)
        
        # If path is already absolute, return as-is
        if mitre_path.is_absolute():
            return mitre_path
        
        # If base_path provided, use it
        if base_path:
            return Path(base_path) / mitre_path
        
        # Try to resolve relative to current working directory
        return mitre_path.resolve()
