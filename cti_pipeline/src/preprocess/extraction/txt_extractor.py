"""
TXT Text Extraction Module

This module contains TXT-specific text extraction operations.
"""

import os
import sys

# Handle imports for both package and standalone usage
try:
    from .base import BaseExtraction
except ImportError:
    # If relative import fails, try absolute import
    try:
        from base import BaseExtraction
    except ImportError:
        # If that fails, try importing from the same directory
        import importlib.util
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Import base module
        base_path = os.path.join(current_dir, 'base.py')
        spec = importlib.util.spec_from_file_location("base", base_path)
        base_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(base_module)
        BaseExtraction = base_module.BaseExtraction


class TXTExtraction(BaseExtraction):
    """
    TXT-specific text extraction class.
    
    This class inherits from BaseExtraction and implements TXT-specific
    extraction methods.
    """
    
    def __init__(self):
        """Initialize the TXT extractor"""
        super().__init__()
        self.supported_formats = {'.txt'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from TXT file"""
        return self._extract_txt(file_path)
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin1") as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"[Extract] Text file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] Text file extraction error: {str(e)}")


# Convenience function for direct usage
def extract_txt_text(file_path: str) -> str:
    """Extract text from a TXT file"""
    extractor = TXTExtraction()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""
