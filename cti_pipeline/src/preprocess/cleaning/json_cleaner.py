"""
JSON Text Cleaning Module

This module contains JSON-specific text cleaning operations.
"""

import os
import sys
import re

from .base import BaseCleaning
from .cleaning_patterns import NAV_PATTERNS, NAV_PREFIXES, NAV_TERMS

# Handle imports for both package and standalone usage
# try:
#     from .base import BaseCleaning
#     from .cleaning_patterns import NAV_PATTERNS, NAV_PREFIXES, NAV_TERMS
# except ImportError:
#     try:
#         from base import BaseCleaning
#         from cleaning_patterns import NAV_PATTERNS, NAV_PREFIXES, NAV_TERMS
#     except ImportError:
#         import importlib.util
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         # Import base module
#         base_path = os.path.join(current_dir, 'base.py')
#         spec = importlib.util.spec_from_file_location("base", base_path)
#         base_module = importlib.util.module_from_spec(spec)
#         spec.loader.exec_module(base_module)
#         BaseCleaning = base_module.BaseCleaning
#         # Import cleaning_patterns module
#         patterns_path = os.path.join(current_dir, 'cleaning_patterns.py')
#         spec2 = importlib.util.spec_from_file_location("cleaning_patterns", patterns_path)
#         patterns_module = importlib.util.module_from_spec(spec2)
#         spec2.loader.exec_module(patterns_module)
#         NAV_PATTERNS = patterns_module.NAV_PATTERNS
#         NAV_PREFIXES = patterns_module.NAV_PREFIXES
#         NAV_TERMS = patterns_module.NAV_TERMS

class JSONCleaning(BaseCleaning):
    """ JSON-specific text cleaning class. """

    def __init__(self):
        """Initialize the JSON cleaner."""
        super().__init__()

    def remove_nav_patterns(self, text: str) -> str:
        """Remove navigation patterns, prefixes, and terms from text."""
        # Remove NAV_PATTERNS (regex)
        for pattern in NAV_PATTERNS:
            try:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
            except Exception as e:
                print(f"[Clean] Error removing NAV_PATTERN '{pattern}': {e}")
        # Remove lines starting with NAV_PREFIXES
        lines = text.splitlines()
        filtered_lines = []
        for line in lines:
            line_strip = line.strip().lower()
            if any(line_strip.startswith(prefix) for prefix in NAV_PREFIXES):
                continue
            # Remove lines that are exactly a NAV_TERM
            if line_strip in NAV_TERMS:
                continue
            filtered_lines.append(line)
        return '\n'.join(filtered_lines)

    def clean(self, text: str, filename: str = None) -> str:
        """ Main cleaning function that applies all cleaning steps, with blog-specific nav cleaning. """
        text = super().clean(text)
        if filename and 'blog' in filename.lower():
            text = self.remove_nav_patterns(text)
        return text


# Convenience function for direct usage
def clean_json_text(text: str, filename: str = None) -> str:
    cleaner = JSONCleaning()
    return cleaner.clean(text, filename=filename)
    
