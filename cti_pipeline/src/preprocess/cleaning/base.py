"""
Base Text Cleaning Module

This module contains the base cleaning class with common text cleaning operations.
"""

import re
import os
import sys

# Handle imports for both package and standalone usage
try:
    from .cleaning_patterns import BOILERPLATE_PATTERNS, NON_ASCII_PATTERNS
except ImportError:
    # If relative import fails, try absolute import
    try:
        from cleaning_patterns import BOILERPLATE_PATTERNS, NON_ASCII_PATTERNS
    except ImportError:
        # If that fails, try importing from the same directory
        import importlib.util
        current_dir = os.path.dirname(os.path.abspath(__file__))
        patterns_path = os.path.join(current_dir, 'cleaning_patterns.py')
        spec = importlib.util.spec_from_file_location("cleaning_patterns", patterns_path)
        patterns_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(patterns_module)
        BOILERPLATE_PATTERNS = patterns_module.BOILERPLATE_PATTERNS
        NON_ASCII_PATTERNS = patterns_module.NON_ASCII_PATTERNS


class BaseCleaning():
    """
    Base class for text cleaning operations.
    """

    def __init__(self):
        """ Initialize the base cleaner. """
        self.non_ascii_patterns = NON_ASCII_PATTERNS
        self.boilerplate_patterns = BOILERPLATE_PATTERNS
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_boilerplate_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                            for pattern in self.boilerplate_patterns]
        self.compiled_non_ascii_patterns = [re.compile(pattern) for pattern in self.non_ascii_patterns]
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove boilerplate content"""
        try:
            for pattern in self.compiled_boilerplate_patterns:
                text = pattern.sub('', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing boilerplate: {e}")
            return text

    def clean_whitespace(self, text: str) -> str:
        """Clean up whitespace and formatting"""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error cleaning whitespace: {e}")
            return text
    
    def remove_non_ascii(self, text: str) -> str:
        """Remove non-ASCII characters including emojis"""
        try:
            for pattern in self.compiled_non_ascii_patterns:
                text = pattern.sub(' ', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing non-ASCII characters: {e}")
            return text
    
    def clean(self, text: str) -> str:
        """ Main cleaning function that applies all cleaning steps """
        try:
            print("[Clean] Starting text cleaning...")
            
            original_length = len(text)
            
            # Apply cleaning steps
            text = self.remove_boilerplate(text)
            text = self.remove_non_ascii(text)
            text = self.clean_whitespace(text) 
            
            final_length = len(text)
            print(f"[Clean] Text cleaning completed. Length: {original_length} -> {final_length}")
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error in text cleaning: {e}")
            return text

# Convenience function for direct usage
def clean_base_text(text: str) -> str:
    cleaner = BaseCleaning()
    return cleaner.clean(text)