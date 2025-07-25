"""
PDF Text Cleaning Module

This module contains PDF-specific text cleaning operations.
"""

import os
import sys

# Handle imports for both package and standalone usage
try:
    from .base import BaseCleaning
except ImportError:
    # If relative import fails, try absolute import
    try:
        from base import BaseCleaning
    except ImportError:
        # If that fails, try importing from the same directory
        import importlib.util
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Import base module
        base_path = os.path.join(current_dir, 'base.py')
        spec = importlib.util.spec_from_file_location("base", base_path)
        base_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(base_module)
        BaseCleaning = base_module.BaseCleaning

from typing import Optional, Dict, Any


class PDFCleaning(BaseCleaning):
    """
    PDF-specific text cleaning class.
    
    This class inherits from BaseCleaning and adds PDF-specific
    cleaning methods for processing PDF-extracted text.
    """
    
    def __init__(self):
        """Initialize the PDF cleaner."""
        super().__init__()


# Convenience function for direct usage
def clean_pdf_text(text: str) -> str:
    cleaner = PDFCleaning()
    return cleaner.clean(text)
