"""
HTML Text Cleaning Module

This module contains HTML-specific text cleaning operations.
"""

import html
import re
import os
import sys

# Handle imports for both package and standalone usage
try:
    from .base import BaseCleaning
    from .cleaning_patterns import (
        BUTTON_PATTERNS,
        HTML_PATTERNS,
        AD_PATTERNS,
        NAV_PATTERNS,
        NAV_PREFIXES,
        NAV_TERMS,
    )
except ImportError:
    # If relative import fails, try absolute import
    try:
        from base import BaseCleaning
        from cleaning_patterns import (
            BUTTON_PATTERNS,
            HTML_PATTERNS,
            AD_PATTERNS,
            NAV_PATTERNS,
            NAV_PREFIXES,
            NAV_TERMS,
        )
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
        BUTTON_PATTERNS = patterns_module.BUTTON_PATTERNS
        HTML_PATTERNS = patterns_module.HTML_PATTERNS
        AD_PATTERNS = patterns_module.AD_PATTERNS
        NAV_PATTERNS = patterns_module.NAV_PATTERNS
        NAV_PREFIXES = patterns_module.NAV_PREFIXES
        NAV_TERMS = patterns_module.NAV_TERMS


class HTMLCleaning(BaseCleaning):
    """ HTML-specific text cleaning class. """
    
    def __init__(self):
        """ Initialize the HTML cleaner. """
        super().__init__()
        self.html_patterns = HTML_PATTERNS
        self.ad_patterns = AD_PATTERNS
        self.nav_patterns = NAV_PATTERNS
        self.button_patterns = BUTTON_PATTERNS
        self._compile_html_patterns()

    def _compile_html_patterns(self):
        self.compiled_html_patterns = [re.compile(pattern) for pattern in self.html_patterns]
        self.compiled_ad_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                   for pattern in self.ad_patterns]
        self.compiled_nav_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                    for pattern in self.nav_patterns]
        self.compiled_button_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                       for pattern in self.button_patterns]
    
    def remove_html(self, text: str) -> str:
        """Remove HTML tags and entities"""
        try:
            # Use BeautifulSoup for better HTML parsing if available
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, 'html.parser')
                text = soup.get_text()
            except ImportError:
                # Fallback to regex
                for pattern in self.compiled_html_patterns:
                    text = pattern.sub('', text)
            
            # Decode HTML entities
            text = html.unescape(text)
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing HTML: {e}")
            return text
    
    def remove_ads(self, text: str) -> str:
        """Remove advertisement content"""
        try:
            for pattern in self.compiled_ad_patterns:
                text = pattern.sub('', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing ads: {e}")
            return text
    
    def remove_navigation(self, text: str) -> str:
        """Remove navigation elements"""
        try:
            # First apply regex patterns
            for pattern in self.compiled_nav_patterns:
                text = pattern.sub('', text)
            
            # Then apply line-by-line cleaning for better accuracy
            text = self._remove_nav_lines(text)
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing navigation: {e}")
            return text
    
    def _remove_nav_lines(self, text: str) -> str:
        """Remove navigation lines using line-by-line processing"""
        try:
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                line_lower = line_stripped.lower()
                
                # Skip empty lines (keep them)
                if not line_stripped:
                    cleaned_lines.append(line)
                    continue
                
                # Skip if line matches navigation terms exactly
                if line_lower in NAV_TERMS:
                    continue
                
                # Skip if line starts with common navigation patterns
                if any(line_lower.startswith(prefix) for prefix in NAV_PREFIXES):
                    continue
                
                # Keep the line
                cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            print(f"[Clean] Error in line-by-line navigation removal: {e}")
            return text
    
    def remove_buttons(self, text: str) -> str:
        """Remove button and action elements"""
        try:
            for pattern in self.compiled_button_patterns:
                text = pattern.sub('', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing buttons: {e}")
            return text
    
    def clean(self, text: str) -> str:
        """ Main HTML cleaning method. """
        try:
            print("[Clean] Starting text cleaning...")
            
            original_length = len(text)
            
            # Apply cleaning steps
            text = self.remove_html(text)
            text = self.remove_ads(text)
            text = self.remove_navigation(text)
            text = self.remove_buttons(text)
            text = super().clean(text)
            
            final_length = len(text)
            print(f"[Clean] Text cleaning completed. Length: {original_length} -> {final_length}")
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error in text cleaning: {e}")
            return text
        
# Convenience function 
def clean_html_text(text) : 
    html_cleaner = HTMLCleaning()
    return html_cleaner.clean(text)
