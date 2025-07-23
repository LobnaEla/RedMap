"""
HTML Text Extraction Module

This module contains HTML-specific text extraction operations.
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

from bs4 import BeautifulSoup


class HTMLExtraction(BaseExtraction):
    """
    HTML-specific text extraction class.
    
    This class inherits from BaseExtraction and implements HTML-specific
    extraction methods using BeautifulSoup.
    """
    
    def __init__(self):
        """Initialize the HTML extractor"""
        super().__init__()
        self.supported_formats = {'.html', '.htm'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from HTML file using BeautifulSoup"""
        return self._extract_html(file_path)
    
    def _extract_html(self, file_path: str) -> str:
        """Extract text from HTML file using BeautifulSoup"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                return soup.get_text(separator="\n")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin1") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    return soup.get_text(separator="\n")
            except Exception as e:
                raise Exception(f"[Extract] HTML file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] HTML extraction error: {str(e)}")


# Convenience function for direct usage
def extract_html_from_file(file_path: str) -> str:
    """Extract text from an HTML file"""
    extractor = HTMLExtraction()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""
