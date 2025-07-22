"""
Text Cleaning Module for CTI Preprocessing Pipeline

This module handles the cleaning step of the preprocessing pipeline:
- Remove HTML tags and entities
- Remove ads and boilerplate content
- Remove generic/irrelevant content
- Clean up formatting and whitespace
"""

import re
import html
from .cleaning_patterns import (
    HTML_PATTERNS,
    BOILERPLATE_PATTERNS,
    AD_PATTERNS,
    NAV_PATTERNS,
    BUTTON_PATTERNS,
    OCR_PATTERNS,
    NON_ASCII_PATTERNS,
    NAV_TERMS,
    NAV_PREFIXES
)

class TextCleaner:
    """
    Handles text cleaning operations for CTI documents
    """
    
    def __init__(self):
        # Import patterns from cleaning_patterns module
        self.html_patterns = HTML_PATTERNS
        self.boilerplate_patterns = BOILERPLATE_PATTERNS
        self.ad_patterns = AD_PATTERNS
        self.nav_patterns = NAV_PATTERNS
        self.button_patterns = BUTTON_PATTERNS
        self.ocr_patterns = OCR_PATTERNS
        self.non_ascii_patterns = NON_ASCII_PATTERNS
        
        # Compile patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_html_patterns = [re.compile(pattern) for pattern in self.html_patterns]
        self.compiled_boilerplate_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                            for pattern in self.boilerplate_patterns]
        self.compiled_ad_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                   for pattern in self.ad_patterns]
        self.compiled_nav_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
                                    for pattern in self.nav_patterns]
        self.compiled_button_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                       for pattern in self.button_patterns]
        self.compiled_ocr_patterns = [re.compile(pattern) for pattern in self.ocr_patterns]
        self.compiled_non_ascii_patterns = [re.compile(pattern) for pattern in self.non_ascii_patterns]
    
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
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove boilerplate content"""
        try:
            for pattern in self.compiled_boilerplate_patterns:
                text = pattern.sub('', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error removing boilerplate: {e}")
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
    
    def fix_ocr_artifacts(self, text: str) -> str:
        """Fix OCR artifacts and noise"""
        try:
            for pattern in self.compiled_ocr_patterns:
                text = pattern.sub(' ', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error fixing OCR artifacts: {e}")
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
    
    # def remove_short_lines(self, text: str, min_length: int = 5) -> str:
    #     """Remove lines that are too short to be meaningful"""
    #     try:
    #         lines = text.split('\n')
    #         cleaned_lines = []
            
    #         for line in lines:
    #             line_stripped = line.strip()
    #             # Keep empty lines and lines with minimum content
    #             if line_stripped == '' or len(line_stripped) >= min_length:
    #                 cleaned_lines.append(line)
    #             else:
    #                 # Skip very short lines that are likely noise
    #                 print(f"[Clean] Removing short line: '{line_stripped}'")
            
    #         return '\n'.join(cleaned_lines)
            
    #     except Exception as e:
    #         print(f"[Clean] Error removing short lines: {e}")
    #         return text
    
    def clean(self, text: str) -> str:
        """
        Main cleaning function that applies all cleaning steps
        """
        try:
            print("[Clean] Starting text cleaning...")
            
            original_length = len(text)
            
            # Apply cleaning steps
            text = self.remove_html(text)
            text = self.remove_boilerplate(text)
            text = self.remove_ads(text)
            text = self.remove_navigation(text)
            text = self.remove_buttons(text)
            text = self.remove_non_ascii(text)
            text = self.fix_ocr_artifacts(text)
            text = self.clean_whitespace(text)  # Final whitespace cleanup
            
            final_length = len(text)
            print(f"[Clean] Text cleaning completed. Length: {original_length} -> {final_length}")
            
            return text
            
        except Exception as e:
            print(f"[Clean] Error in text cleaning: {e}")
            return text


# Convenience function
def clean_text(text: str) -> str:
    """Quick cleaning function"""
    cleaner = TextCleaner()
    return cleaner.clean(text)
