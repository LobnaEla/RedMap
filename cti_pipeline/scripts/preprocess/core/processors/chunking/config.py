"""
Chunking Configuration

Configuration classes for the CTI chunking module.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import os


@dataclass
class ChunkingConfig:
    """Configuration for CTI chunking operations"""
    
    # Chunking parameters
    window_size: int = 2
    chunk_strategy: str = "ioc_based"  # "ioc_based" or "fixed_size"
    fixed_chunk_size: int = 5  # sentences per chunk for fixed strategy
    overlap: int = 1  # sentence overlap for fixed strategy
    
    # IOC extraction parameters
    use_llm_extraction: bool = True
    fallback_to_regex: bool = True
    
    # LLM API configuration
    api_key: Optional[str] = None
    api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    model: str = "llama3-70b-8192"
    temperature: float = 0.1
    max_retries: int = 3
    retry_delay: int = 1
    
    # Output configuration
    include_metadata: bool = True
    save_chunks: bool = True
    deduplicate_chunks: bool = True
    
    # IOC types to extract
    ioc_types: List[str] = None
    
    def __post_init__(self):
        """Initialize default IOC types and API key"""
        if self.ioc_types is None:
            self.ioc_types = [
                "ipv4", "ipv6", "domain", "url", "email", 
                "md5", "sha1", "sha256", "sha512",
                "cve", "mitre_technique", "bitcoin"
            ]
        
        # Try to get API key from environment if not provided
        if self.api_key is None:
            self.api_key = os.getenv("GROQ_API_KEY")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "window_size": self.window_size,
            "chunk_strategy": self.chunk_strategy,
            "fixed_chunk_size": self.fixed_chunk_size,
            "overlap": self.overlap,
            "use_llm_extraction": self.use_llm_extraction,
            "fallback_to_regex": self.fallback_to_regex,
            "api_url": self.api_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "include_metadata": self.include_metadata,
            "save_chunks": self.save_chunks,
            "deduplicate_chunks": self.deduplicate_chunks,
            "ioc_types": self.ioc_types
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ChunkingConfig':
        """Create configuration from dictionary"""
        return cls(**config_dict)


@dataclass
class ChunkingResult:
    """Result of chunking operation"""
    
    # Core results
    chunks: List[Dict[str, Any]]
    original_text: str
    processing_time: float
    success: bool
    
    # Metadata
    total_chunks: int = 0
    iocs_found: int = 0
    strategy_used: str = ""
    window_size: int = 0
    
    # Processing details
    extraction_time: float = 0.0
    chunking_time: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        """Initialize calculated fields"""
        if self.errors is None:
            self.errors = []
        
        self.total_chunks = len(self.chunks)
        self.iocs_found = len(set(chunk.get("ioc", "") for chunk in self.chunks if chunk.get("ioc")))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the chunking results"""
        return {
            "total_chunks": self.total_chunks,
            "iocs_found": self.iocs_found,
            "strategy_used": self.strategy_used,
            "window_size": self.window_size,
            "processing_time": self.processing_time,
            "extraction_time": self.extraction_time,
            "chunking_time": self.chunking_time,
            "success": self.success,
            "error_count": len(self.errors)
        }
    
    def get_chunks_by_ioc_type(self, ioc_type: str) -> List[Dict[str, Any]]:
        """Get chunks filtered by IOC type"""
        return [chunk for chunk in self.chunks if chunk.get("type") == ioc_type]
    
    def get_unique_iocs(self) -> List[str]:
        """Get list of unique IOCs found"""
        return list(set(chunk.get("ioc", "") for chunk in self.chunks if chunk.get("ioc")))
