"""
CTI Text Processor Module

Main processing class that provides fixed-size text chunking for CTI reports.
"""
import logging
from typing import List, Dict, Any
from .chunker import FixedSizeChunker

logger = logging.getLogger(__name__)

class CTITextProcessor:
    """
    CTI chunking processor using fixed-size chunking.
    """
    
    def __init__(self, chunk_size: int = 8, overlap: int = 2):
        """
        Initialize the chunker with fixed-size parameters.
        
        Args:
            chunk_size: Number of sentences per chunk (default: 8)
            overlap: Number of overlapping sentences between chunks (default: 2)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        try:
            self.chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=overlap)
        except Exception as e:
            print(f"[CTITextProcessor] Failed to initialize FixedSizeChunker: {e}")
            self.chunker = None

    def chunk(self, text: str, print_stats: bool = False) -> List[Dict[str, Any]]:
        """
        Main chunking method that processes text using fixed-size chunks.
        
        Args:
            text: Input text to chunk
            print_stats: Whether to print basic statistics
            
        Returns:
            A list of chunk dictionaries with metadata
        """
        if not text or not text.strip():
            print("[CTIChunker] Empty or whitespace-only text provided.")
            return []
        
        if not self.chunker:
            print("[CTIChunker] TextChunker not available. Cannot process text.")
            return []
        
        try:
            chunks = self.chunker.generate_chunks(text, print_stats=False) 
            
            total_length = len(text)
            chunk_count = len(chunks)
            print(f"Total document length: {total_length} characters")
            print(f"Number of chunks: {chunk_count}")
            
            return chunks
        except Exception as e:
            print(f"[CTIChunker] Chunking failed: {e}")
            return []


    def get_comprehensive_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Basic chunk statistics for DAG compatibility."""
        if not chunks:
            return {"total_chunks": 0, "total_length": 0, "average_length": 0, "min_length": 0, "max_length": 0}
        
        chunk_lengths = [chunk.get("chunk_length", len(chunk.get("chunk", ""))) for chunk in chunks]
        total_length = sum(chunk_lengths)
        
        return {
            "total_chunks": len(chunks),
            "total_length": total_length,
            "average_length": round(total_length / len(chunks), 2),
            "min_length": min(chunk_lengths),
            "max_length": max(chunk_lengths)
        }

    # Backward compatibility methods - simplified
    def extract_iocs_only(self, text: str) -> List[Dict[str, str]]:
        """DEPRECATED: Returns empty list for backward compatibility."""
        return []

    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy method for backward compatibility."""
        if not chunks:
            return {"total_chunks": 0, "total_length": 0, "average_length": 0, "ioc_types": {}}
        
        total_chunks = len(chunks)
        total_length = sum(chunk.get("chunk_length", len(chunk.get("chunk", ""))) for chunk in chunks)
        
        return {
            "total_chunks": total_chunks,
            "total_length": total_length,
            "average_length": total_length / total_chunks,
            "ioc_types": {"fixed_size_chunk": total_chunks}
        }
