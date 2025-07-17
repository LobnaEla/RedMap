"""
CTI Preprocessing Core - Simplified Architecture

This package provides a clean, simplified architecture for CTI document preprocessing
with comprehensive error handling, metrics collection, and configuration management.

Main Components:
- TextExtractor: Extract text from various file formats (PDF, HTML, JSON, CSV, TXT)
- CTIPreprocessor: Main preprocessing coordinator
- TextCleaner: Clean and normalize text
- TextChunker: Chunk text for processing
- ErrorHandler: Structured error handling and recovery
- PipelineMetrics: Comprehensive metrics and monitoring

Usage Examples:

    # Quick usage for files
    from cti_pipeline.src.preprocess.core import preprocess_cti_file
    processed_text = preprocess_cti_file("threat_report.pdf")
    
    # Detailed usage with configuration
    from cti_pipeline.src.preprocess.core import CTIPreprocessor
    preprocessor = CTIPreprocessor()
    result = preprocessor.process_file("document.pdf")
    
    # Individual components
    from cti_pipeline.src.preprocess.core import TextExtractor, TextCleaner
    extractor = TextExtractor()
    cleaner = TextCleaner()
"""

from typing import Dict, Any
from pathlib import Path

# Core components (simplified structure)
from .utils import *

# Main preprocessing components (moved to core/)
from .extraction import TextExtractor, ExtractionResult, extract_text_from_file, extract_with_result

# Individual processing components (moved to core/)
from .cleaning import TextCleaner, TextNormalizer, clean_text, normalize_text
from .chunking import CTIChunker

# Convenience functions for quick usage
# from .preprocessing import (
#     preprocess_text, preprocess_cti_text,
#     preprocess_file, preprocess_cti_file, 
#     process_file_with_result,
#     create_minimal_preprocessor, create_standard_preprocessor,
#     create_full_preprocessor, create_cti_preprocessor
# )

# Backward compatibility aliases
# extract_text_from_file = extract_text_from_file  # Already imported above

__version__ = "2.0.0"

__all__ = [
    # Error handling (from utils)
    'ErrorHandler', 'MetricsCollector',
    
    # Extraction
    'TextExtractor', 'ExtractionResult', 'extract_text_from_file', 'extract_with_result',
    
    # Individual components
    'TextCleaner', 'TextNormalizer', 'CTIChunker',
    
    # Convenience functions
    'clean_text', 'normalize_text',
    'quick_extract_text', 'quick_clean_text', 'quick_chunk_text'
]


# Module-level convenience functions for easier usage
def quick_extract_text(file_path: str) -> str:
    """
    Quick text extraction from file
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text
    """
    from pathlib import Path
    
    if Path(file_path).exists():
        extractor = TextExtractor()
        return extractor.extract(file_path)
    else:
        raise FileNotFoundError(f"File not found: {file_path}")


def quick_clean_text(text: str) -> str:
    """
    Quick text cleaning
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    cleaner = TextCleaner()
    return cleaner.clean(text)


def quick_chunk_text(text: str, window: int = 2) -> list:
    """
    Quick text chunking
    
    Args:
        text: Text to chunk
        window: Window size for chunking
        
    Returns:
        List of chunks
    """
    chunker = CTIChunker()
    return chunker.chunk(text, window=window)


# Add convenience functions to __all__
__all__.extend(['quick_extract_text', 'quick_clean_text', 'quick_chunk_text'])
