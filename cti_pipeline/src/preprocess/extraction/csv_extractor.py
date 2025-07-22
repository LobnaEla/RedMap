"""
CSV Text Extraction Module

This module contains CSV-specific text extraction operations.
"""

import os
import sys
import csv

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


class CSVExtraction(BaseExtraction):
    """
    CSV-specific text extraction class.
    
    This class inherits from BaseExtraction and implements CSV-specific
    extraction methods.
    """
    
    def __init__(self):
        """Initialize the CSV extractor"""
        super().__init__()
        self.supported_formats = {'.csv'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from CSV file"""
        return self._extract_csv(file_path)
    
    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join("; ".join(row) for row in reader)
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, newline="", encoding="latin1") as f:
                    reader = csv.reader(f)
                    return "\n".join("; ".join(row) for row in reader)
            except Exception as e:
                raise Exception(f"[Extract] CSV file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] CSV extraction error: {str(e)}")


# Convenience function for direct usage
def extract_csv_text(file_path: str) -> str:
    """Extract text from a CSV file"""
    extractor = CSVExtraction()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""
