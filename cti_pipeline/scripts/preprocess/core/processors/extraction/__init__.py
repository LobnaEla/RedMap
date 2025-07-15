"""
Extraction Processors

This package contains text extraction components for various file formats.
"""

from .extraction import (
    TextExtractor, 
    ExtractionResult,
    extract_text_from_file,
    extract_with_result
)

__all__ = [
    'TextExtractor',
    'ExtractionResult',
    'extract_text_from_file',
    'extract_with_result'
]
