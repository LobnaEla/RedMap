"""
OCR Text Cleaning Module

This module contains OCR-specific text cleaning operations.
"""

import re
import os
import sys

# Handle imports for both package and standalone usage
try:
    from .base import BaseCleaning
    from .cleaning_patterns import OCR_PATTERNS
except ImportError:
    # If relative import fails, try absolute import
    try:
        from base import BaseCleaning
        from cleaning_patterns import OCR_PATTERNS
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
        
        # Import patterns module
        patterns_path = os.path.join(current_dir, 'cleaning_patterns.py')
        spec = importlib.util.spec_from_file_location("cleaning_patterns", patterns_path)
        patterns_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patterns_module)
        OCR_PATTERNS = patterns_module.OCR_PATTERNS


class OCRCleaning(BaseCleaning):
    """
    OCR-specific text cleaning class.
    
    This class inherits from BaseCleaning and adds OCR-specific
    cleaning methods for processing OCR-extracted text.
    """
    
    def __init__(self):
        """ Initialize the OCR cleaner. """
        super().__init__()
        self.ocr_patterns = OCR_PATTERNS
        self._compile_ocr_patterns()

    def _compile_ocr_patterns(self):
        self.compiled_ocr_patterns = [re.compile(pattern) for pattern in self.ocr_patterns]

    def fix_ocr_artifacts(self, text: str) -> str:
        """Fix OCR artifacts and noise"""
        try:
            for pattern in self.compiled_ocr_patterns:
                text = pattern.sub(' ', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error fixing OCR artifacts: {e}")
            return text
    
    def clean(self, text: str) -> str:
        """ Main cleaning function that applies all cleaning steps """
        try:
            print("[Clean] Starting text cleaning...")
            
            original_length = len(text)
            
            # Apply cleaning steps
            text = super().clean(text)
            text = self.fix_ocr_artifacts(text)

            final_length = len(text)
            print(f"[Clean] Text cleaning completed. Length: {original_length} -> {final_length}")
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error in text cleaning: {e}")
            return text


# Convenience function for direct usage
def clean_ocr_text(text: str) -> str:
    cleaner = OCRCleaning()
    return cleaner.clean(text)
        
