"""
PDF Text Extraction Module

This module contains PDF-specific text extraction operations.
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

class PDFExtraction(BaseExtraction):
    """
    PDF-specific text extraction class.
    
    This class inherits from BaseExtraction and implements PDF-specific
    extraction methods using pypdf.
    """
    
    def __init__(self):
        """Initialize the PDF extractor"""
        super().__init__()
        self.supported_formats = {'.pdf'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from PDF file using pypdf"""
        return self._extract_pdf(file_path)
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pypdf"""
        try:
            from pypdf import PdfReader
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text_content = ""
                
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_content += page_text + "\n"
                
                print("[Extract] Extracted text from PDF with {} pages".format(len(reader.pages)))

                return text_content
                
        except Exception as e:
            raise Exception(f"[Extract] PDF extraction error: {str(e)}")


# Convenience function for direct usage
def extract_pdf_from_file(file_path: str) -> str:
    """Extract text from a PDF file"""
    extractor = PDFExtraction()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""
