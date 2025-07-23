"""
JSON Text Extraction Module

This module contains JSON-specific text extraction operations.
"""

import os
import sys
import json

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


class JSONExtraction(BaseExtraction):
    """
    JSON-specific text extraction class.
    
    This class inherits from BaseExtraction and implements JSON-specific
    extraction methods.
    """
    
    def __init__(self):
        """Initialize the JSON extractor"""
        super().__init__()
        self.supported_formats = {'.json'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from JSON file"""
        return self._extract_json(file_path)
    
    def _extract_json(self, file_path: str) -> str:
        """Extract text from JSON or JSONL file"""
        try:
            texts = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        # You can control what text to extract — for now just flatten:
                        flat = json.dumps(obj, ensure_ascii=False)
                        texts.append(flat)
                    except json.JSONDecodeError:
                        continue
            return "\n".join(texts)
        except Exception as e:
            raise Exception(f"[Extract] JSON extraction error: {str(e)}")


# Convenience function for direct usage
def extract_json_from_file(file_path: str) -> str:
    """Extract text from a JSON file"""
    extractor = JSONExtraction()
    result = extractor.extract_from_file(file_path)
    print(f"[Extract] Extracted text from JSON file: {file_path}")
    return result.text if result.success else ""
