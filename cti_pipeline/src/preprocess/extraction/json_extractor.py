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
        self.supported_formats = {'.json', '.jsonl'}
    
    def _extract_text(self, file_path: str, extension: str) -> str:
        """Extract text from JSON file"""
        return self._extract_json(file_path)
    
    def _extract_json(self, file_path: str) -> str:
        texts = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        # Extract only the "content" field if it exists
                        content = obj.get("content", "")
                        if content:
                            texts.append(content)
                    except json.JSONDecodeError as e:
                        print(f"[DEBUG] JSON decode error in line: {line[:100]} | {e}")
                        continue
            extracted_text = "\n".join(texts)
            print(f"[DEBUG] Extracted text length: {len(extracted_text)}")
            return extracted_text
        except Exception as e:
            print(f"[ERROR] Exception during JSON extraction: {e}")
            raise

# Convenience function for direct usage
def extract_json_from_file(file_path: str) -> str:
    """Extract text from a JSON file"""
    extractor = JSONExtraction()
    result = extractor.extract_from_file(file_path)
    print(f"[Extract] Extracted text from JSON file: {file_path}")
    print(f"[Extract] Result: {result.success}, Text Length: {len(result.text) if result.text else 0}")
    return result.text if result.success else ""
