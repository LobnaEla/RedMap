"""
Text Normalization Module for CTI Preprocessing Pipeline

This module handles the normalization step of the preprocessing pipeline:
- Standardize text encoding to UTF-8
- Normalize Unicode characters
- Convert case consistently
- Unify date/time formats
- Standardize punctuation and spacing
- Fix common text artifacts
"""

import re
import unicodedata
import os
import sys

# Add the core directory to the path to import utils
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, core_dir)

from utils.preservers import PreservationManager

class TextNormalizer:
    """
    Handles text normalization operations for CTI documents
    """
    
    def __init__(self):
        # Date patterns to normalize
        self.date_patterns = [
            (r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})\b', r'\3-\2-\1'),  # DD/MM/YYYY -> YYYY-MM-DD
            (r'\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})\b', r'20\3-\2-\1'),  # DD/MM/YY -> YYYY-MM-DD
            (r'\b(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})\b', r'\1-\2-\3'),  # YYYY/MM/DD -> YYYY-MM-DD
        ]
        
        # Time patterns to normalize
        self.time_patterns = [
            (r'\b(\d{1,2}):(\d{2}):(\d{2})\s*(AM|PM)\b', r'\1:\2:\3 \4'),  # Normalize AM/PM
            (r'\b(\d{1,2}):(\d{2})\s*(AM|PM)\b', r'\1:\2:00 \3'),  # Add seconds
        ]
        
        # Punctuation normalization
        self.punctuation_patterns = [
            (r'["""]', '"'),  # Normalize quotes
            (r"[''']", "'"),  # Normalize apostrophes
            (r'[–—]', '-'),  # Normalize dashes
            (r'…', '...'),  # Normalize ellipsis
            (r'[«»]', '"'),  # Normalize guillemets
        ]
        
        # Common text artifacts to fix
        self.artifact_patterns = [
            (r'\s+', ' '),  # Multiple spaces to single space
            (r'\n\s*\n', '\n\n'),  # Multiple newlines to double newline
            (r'\t', ' '),  # Tabs to spaces
            (r'\r\n', '\n'),  # Windows line endings to Unix
            (r'\r', '\n'),  # Old Mac line endings to Unix
        ]
        
        # Case normalization for important terms
        self.preservation_manager = PreservationManager()
        
        # Compile patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_date_patterns = [(re.compile(pattern), replacement) 
                                     for pattern, replacement in self.date_patterns]
        self.compiled_time_patterns = [(re.compile(pattern, re.IGNORECASE), replacement) 
                                     for pattern, replacement in self.time_patterns]
        self.compiled_punctuation_patterns = [(re.compile(pattern), replacement) 
                                            for pattern, replacement in self.punctuation_patterns]
        self.compiled_artifact_patterns = [(re.compile(pattern), replacement) 
                                         for pattern, replacement in self.artifact_patterns]
    
    def fix_encoding(self, text: str) -> str:
        """Fix text encoding issues"""
        try:
            # Replace common problematic characters
            replacements = {
                '\u00c2\u00a0': ' ',  # Non-breaking space
                '\u00c2\u00ab': '"',  # Left guillemet
                '\u00c2\u00bb': '"',  # Right guillemet
                '\u00e2\u0080\u0099': "'",  # Right single quotation mark
                '\u00e2\u0080\u009c': '"',  # Left double quotation mark
                '\u00e2\u0080\u009d': '"',  # Right double quotation mark
                '\u00e2\u0080\u0093': '-',  # En dash
                '\u00e2\u0080\u0094': '-',  # Em dash
            }
            
            for bad_char, good_char in replacements.items():
                text = text.replace(bad_char, good_char)
            
            # Ensure UTF-8 encoding
            if isinstance(text, bytes):
                text = text.decode('utf-8', errors='replace')
            
            return text
            
        except Exception as e:
            print(f"[Normalize] Error fixing encoding: {e}")
            return text
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters to consistent form"""
        try:
            normalized = unicodedata.normalize('NFC', text)
            normalized = re.sub(r'[\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]', '', normalized)
            normalized = normalized.replace('\u00a0', ' ')
            normalized = re.sub(r'[\u2000-\u200a\u2028\u2029\u3000]', ' ', normalized)
            
            return normalized
            
        except Exception as e:
            print(f"[Normalize] Error normalizing Unicode: {e}")
            return text
    
    def normalize_dates(self, text: str) -> str:
        """Normalize date formats to ISO format (YYYY-MM-DD)"""
        try:
            for pattern, replacement in self.compiled_date_patterns:
                text = pattern.sub(replacement, text)
            return text
        except Exception as e:
            print(f"[Normalize] Error normalizing dates: {e}")
            return text
    
    def normalize_times(self, text: str) -> str:
        """Normalize time formats"""
        try:
            for pattern, replacement in self.compiled_time_patterns:
                text = pattern.sub(replacement, text)
            return text
        except Exception as e:
            print(f"[Normalize] Error normalizing times: {e}")
            return text
    
    def normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks to standard forms"""
        try:
            for pattern, replacement in self.compiled_punctuation_patterns:
                text = pattern.sub(replacement, text)
            return text
        except Exception as e:
            print(f"[Normalize] Error normalizing punctuation: {e}")
            return text
    
    def fix_artifacts(self, text: str) -> str:
        """Fix common text artifacts like multiple spaces, line endings"""
        try:
            for pattern, replacement in self.compiled_artifact_patterns:
                text = pattern.sub(replacement, text)
            return text.strip()
        except Exception as e:
            print(f"[Normalize] Error fixing artifacts: {e}")
            return text
    
    def normalize_case(self, text: str) -> str:
        """
        Normalize text case while preserving technical terms and IOCs
        """
        try:
            words = text.split()
            normalized_words = []

            for word in words:
                clean_word = re.sub(r'[^\w]', '', word)

                if self.preservation_manager and (
                    self.preservation_manager.should_preserve_text(clean_word)
                    or self.preservation_manager.is_ioc(clean_word)
                ):
                    # Preserve original case
                    normalized_words.append(word)
                else:
                    # Normalize to lowercase
                    normalized_words.append(word.lower())

            return ' '.join(normalized_words)

        except Exception as e:
            print(f"[Normalize] Error normalizing case: {e}")
            return text

    def normalize_ioc_formats(self, text: str) -> str:
        """
        Normalize IoC formats in a conservative way:
        - Fix malformed IPs
        - Normalize defanged URLs (e.g., www.example.com → http://www.example.com)
        - Preserve anything recognized as an IOC by the preservation manager
        """
        try:
            def preserve_match(match):
                token = match.group(0)
                if self.preservation_manager and self.preservation_manager.is_ioc(token):
                    return token  # Don't modify recognized IOCs
                return f"http://{token}"  # Normalize only non-IOC "www" patterns

            # Fix malformed IPs with leading zeroes
            text = re.sub(r'\b0{2,}(\d+)\.0{2,}(\d+)\.0{2,}(\d+)\.0{2,}(\d+)\b', r'\1.\2.\3.\4', text)

            # Normalize www.* to http://www.* unless recognized as an IOC
            text = re.sub(r'\bwww\.([a-zA-Z0-9.-]+)', preserve_match, text)

            return text

        except Exception as e:
            print(f"[Normalize] Error normalizing IoC formats: {e}")
            return text
    
    def normalize(self, text: str) -> str:
        """Main normalization function that applies all normalization steps"""
        try:
            print("[Normalize] Starting text normalization...")
            
            original_length = len(text)
            
            # Apply normalization steps
            text = self.fix_encoding(text)
            text = self.normalize_unicode(text)
            text = self.fix_artifacts(text)
            text = self.normalize_punctuation(text)
            text = self.normalize_dates(text)
            text = self.normalize_times(text)
            text = self.normalize_ioc_formats(text)
            text = self.normalize_case(text)
            
            final_length = len(text)
            print(f"[Normalize] Text normalization completed. Length: {original_length} -> {final_length}")
            
            return text
            
        except Exception as e:
            print(f"[Normalize] Error in text normalization: {e}")
            return text


# Convenience function
def normalize_text(text: str) -> str:
    """Quick normalization function"""
    normalizer = TextNormalizer()
    return normalizer.normalize(text)
