"""
CTI Pipeline Preprocessing Module

This package provides a modular, extensible architecture for Cyber Threat Intelligence (CTI) document preprocessing.
It supports extraction, cleaning, normalization, chunking, and shared utilities, with robust error handling and test coverage.

Main Components:
- Extraction: Extract text from various file formats (PDF, HTML, JSON, CSV, TXT)
- Cleaning: Clean and preprocess extracted text (remove noise, fix encoding, etc.)
- Normalizing: Normalize and standardize text for downstream processing
- Chunking: Split text into logical chunks for LLMs or analytics
- Shared: Common utilities, error handling, regex patterns, and preservation logic

Usage Examples:

    # Quick usage for files
    from cti_pipeline.src.preprocess.extraction import extract_text_from_file
    text = extract_text_from_file("threat_report.pdf")

    # Cleaning and normalization
    from cti_pipeline.src.preprocess.cleaning import clean_text
    from cti_pipeline.src.preprocess.normalizing import normalize_text
    cleaned = clean_text(text)
    normalized = normalize_text(cleaned)

    # Chunking
    from cti_pipeline.src.preprocess.chunking import CTIChunker
    chunker = CTIChunker()
    chunks = chunker.chunk(normalized)

    # Full pipeline (custom orchestrator)
    # See test_full_pipeline.py for integration examples
"""

# Core components (simplified structure)
from .shared import *

# Main preprocessing components (moved to core/)
from .extraction import extract_text

# Individual processing components (moved to core/)
from .cleaning import clean_text
from .normalizing import normalize_text
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
    'ErrorHandler'
    
    # Extraction
    'extract_text',

    # Individual components
    'clean_text', 'normalize_text', 'CTIChunker',
]