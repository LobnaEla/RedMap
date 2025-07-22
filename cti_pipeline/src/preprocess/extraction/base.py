"""
Base Text Extraction Module

This module contains the base extraction class and common data structures.
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExtractionResult:
    """Result of text extraction operation"""
    success: bool
    text: str
    file_path: str
    file_format: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseExtraction:
    """
    Base class for text extraction operations.
    
    This class provides common functionality for extracting text from various
    file formats as part of the CTI preprocessing pipeline.
    """
    
    def __init__(self):
        """Initialize the base extractor"""
        self.supported_formats = set()
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract text from a file based on its format.
        """
        if not os.path.exists(file_path):
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format="unknown",
                error_message=f"[Extract] File not found: {file_path}"
            )
        
        _, extension = os.path.splitext(file_path.lower())
        
        if extension not in self.supported_formats:
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format=extension,
                error_message=f"[Extract] Unsupported file format: {extension}"
            )
        
        try:
            text = self._extract_text(file_path, extension)
            
            return ExtractionResult(
                success=True,
                text=text,
                file_path=file_path,
                file_format=extension,
                metadata={
                    'original_length': len(text),
                    'file_size': os.path.getsize(file_path)
                }
            )
            
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format=extension,
                error_message=f"[Extract] Extraction failed: {str(e)}"
            )
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """
        Extract text from a file. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _extract_text method")


# Convenience function for quick usage
def extract_text_from_file(file_path: str) -> str:
    """
    Quick function to extract text from a file.
    """
    # Import here to avoid circular imports
    from . import extraction
    extractor = extraction.TextExtractor()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""


def extract_with_result(file_path: str) -> ExtractionResult:
    """
    Extract text from a file with detailed result information.
    """
    # Import here to avoid circular imports
    from . import extraction
    extractor = extraction.TextExtractor()
    return extractor.extract_from_file(file_path)
