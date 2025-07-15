"""
CTI Chunker Module

Main chunking class that orchestrates IOC extraction and text chunking.
"""

import time
from typing import List, Dict, Any, Optional
from .config import ChunkingConfig, ChunkingResult
from .ioc_extractor import IOCExtractor
from .text_processor import TextProcessor

class CTIChunker:
    """Main CTI chunking processor"""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """Initialize the chunker with configuration"""
        self.config = config or ChunkingConfig()
        self.ioc_extractor = IOCExtractor(self.config)
        self.text_processor = TextProcessor(self.config)
        
        print(f"[Chunker] CTI Chunker initialized with strategy: {self.config.chunk_strategy}")
    
    def chunk(self, text: str) -> ChunkingResult:
        """
        Main chunking method that processes text and returns chunks
        
        Args:
            text: Input text to chunk
            
        Returns:
            ChunkingResult with chunks and metadata
        """
        start_time = time.time()
        
        if not text or not text.strip():
            return ChunkingResult(
                chunks=[],
                original_text=text,
                processing_time=0.0,
                success=False,
                strategy_used=self.config.chunk_strategy,
                errors=["Empty or whitespace-only text provided"]
            )
        
        print(f"[Chunker] Starting chunking with strategy: {self.config.chunk_strategy}")
        
        try:
            if self.config.chunk_strategy == "ioc_based":
                result = self._chunk_ioc_based(text)
            elif self.config.chunk_strategy == "fixed_size":
                result = self._chunk_fixed_size(text)
            else:
                raise ValueError(f"Unknown chunking strategy: {self.config.chunk_strategy}")
            
            result.processing_time = time.time() - start_time
            result.strategy_used = self.config.chunk_strategy
            result.window_size = self.config.window_size
            
            print(f"[Chunker] Chunking completed in {result.processing_time:.3f}s: {result.total_chunks} chunks")
            return result
            
        except Exception as e:
            print(f"[Chunker] Chunking failed: {e}")
            return ChunkingResult(
                chunks=[],
                original_text=text,
                processing_time=time.time() - start_time,
                success=False,
                strategy_used=self.config.chunk_strategy,
                errors=[str(e)]
            )
    
    def _chunk_ioc_based(self, text: str) -> ChunkingResult:
        """Perform IOC-based chunking"""
        extraction_start = time.time()
        
        # Extract IOCs
        ioc_data = self.ioc_extractor.extract_iocs(text)
        extraction_time = time.time() - extraction_start
        
        if not ioc_data:
            print("[Chunker] No IOCs found, falling back to fixed-size chunking")
            # Fallback to fixed-size chunking
            original_strategy = self.config.chunk_strategy
            self.config.chunk_strategy = "fixed_size"
            result = self._chunk_fixed_size(text)
            self.config.chunk_strategy = original_strategy
            result.strategy_used = "fixed_size_fallback"
            result.extraction_time = extraction_time
            return result
        
        # Generate chunks based on IOCs
        chunking_start = time.time()
        chunks = self.text_processor.generate_ioc_based_chunks(text, ioc_data)
        chunking_time = time.time() - chunking_start
        
        return ChunkingResult(
            chunks=chunks,
            original_text=text,
            processing_time=0.0,  # Will be set in main method
            success=True,
            extraction_time=extraction_time,
            chunking_time=chunking_time,
            strategy_used="ioc_based"
        )
    
    def _chunk_fixed_size(self, text: str) -> ChunkingResult:
        """Perform fixed-size chunking"""
        chunking_start = time.time()
        chunks = self.text_processor.generate_fixed_size_chunks(text)
        chunking_time = time.time() - chunking_start
        
        return ChunkingResult(
            chunks=chunks,
            original_text=text,
            processing_time=0.0,  # Will be set in main method
            success=True,
            extraction_time=0.0,
            chunking_time=chunking_time,
            strategy_used="fixed_size"
        )
    
    def extract_iocs_only(self, text: str) -> List[Dict[str, str]]:
        """Extract only IOCs without chunking"""
        try:
            return self.ioc_extractor.extract_iocs(text)
        except Exception as e:
            print(f"[Chunker] IOC extraction failed: {e}")
            return []
    
    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about chunks"""
        if not chunks:
            return {"total_chunks": 0, "average_length": 0, "ioc_types": {}}
        
        # Basic statistics
        total_chunks = len(chunks)
        total_length = sum(len(chunk.get("chunk", "")) for chunk in chunks)
        average_length = total_length / total_chunks if total_chunks > 0 else 0
        
        # IOC type distribution
        ioc_types = {}
        for chunk in chunks:
            ioc_type = chunk.get("type", "unknown")
            ioc_types[ioc_type] = ioc_types.get(ioc_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_length": total_length,
            "average_length": average_length,
            "ioc_types": ioc_types
        }
    
    def update_config(self, **kwargs):
        """Update chunker configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"[Chunker] Updated config: {key} = {value}")
            else:
                print(f"[Chunker] Unknown config parameter: {key}")
        
        # Reinitialize processors with new config
        self.ioc_extractor = IOCExtractor(self.config)
        self.text_processor = TextProcessor(self.config)
