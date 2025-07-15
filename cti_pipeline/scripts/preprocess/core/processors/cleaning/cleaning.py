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

class TextCleaner:
    """
    Handles text cleaning operations for CTI documents
    """
    
    def __init__(self):
        # HTML/Web content patterns to remove
        self.html_patterns = [
            r'<[^>]+>',  # HTML tags
            r'&[a-zA-Z0-9#]+;',  # HTML entities
            r'javascript:[^"\']*',  # JavaScript URLs
            r'onclick="[^"]*"',  # JavaScript events
            r'style="[^"]*"',  # Inline styles
            r'class="[^"]*"',  # CSS classes
        ]
        
        # Boilerplate patterns commonly found in CTI documents
        self.boilerplate_patterns = [
            r'This document is TLP:[A-Z]+.*?(?=\n\n|\.$)',
            r'Classification:\s*[A-Z\s]+.*?(?=\n\n|\.$)',
            r'Distribution:\s*[A-Z\s]+.*?(?=\n\n|\.$)',
            r'Page\s+\d+\s+of\s+\d+',
            r'Table\s+of\s+Contents.*?(?=\n\n|\w)',
            r'All\s+rights\s+reserved.*?(?=\n\n|\.$)',
            r'©\s*\d{4}.*?(?=\n\n|\.$)',
            r'Copyright\s*\d{4}.*?(?=\n\n|\.$)',
        ]
        
        # Advertisement patterns
        self.ad_patterns = [
            r'Advertisement.*?(?=\n\n|\.$)',
            r'Sponsored\s+by.*?(?=\n\n|\.$)',
            r'Click\s+here.*?(?=\n\n|\.$)',
            r'Subscribe\s+to.*?(?=\n\n|\.$)',
            r'Follow\s+us.*?(?=\n\n|\.$)',
            r'Like\s+us.*?(?=\n\n|\.$)',
            r'Share\s+this.*?(?=\n\n|\.$)',
        ]
        
        # OCR artifacts and noise
        self.ocr_patterns = [
            r'[|]{2,}',  # Multiple pipes
            r'[=]{3,}',  # Multiple equals
            r'[~]{3,}',  # Multiple tildes
            r'[_]{3,}',  # Multiple underscores
            r'\.{4,}',   # Multiple dots
            r'\s+\.\s+',  # Floating dots
            r'\s+,\s+',   # Floating commas
        ]
        
        # Compile patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_html_patterns = [re.compile(pattern) for pattern in self.html_patterns]
        self.compiled_boilerplate_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                            for pattern in self.boilerplate_patterns]
        self.compiled_ad_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                   for pattern in self.ad_patterns]
        self.compiled_ocr_patterns = [re.compile(pattern) for pattern in self.ocr_patterns]
    
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
    
    def fix_ocr_artifacts(self, text: str) -> str:
        """Fix OCR artifacts and noise"""
        try:
            for pattern in self.compiled_ocr_patterns:
                text = pattern.sub(' ', text)
            return text
            
        except Exception as e:
            print(f"[Clean] Error fixing OCR artifacts: {e}")
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
    
    def remove_short_lines(self, text: str, min_length: int = 10) -> str:
        """Remove lines that are too short to be meaningful"""
        try:
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                if len(line.strip()) >= min_length or line.strip() == '':
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            print(f"[Clean] Error removing short lines: {e}")
            return text
    
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
            text = self.fix_ocr_artifacts(text)
            text = self.clean_whitespace(text)
            text = self.remove_short_lines(text)
            
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
