"""
Pattern management for anonymization
"""

import re
import requests
from typing import Dict, List, Pattern


def fetch_malware_names_from_malpedia() -> List[str]:
    """
    Fetch malware names from Malpedia to avoid manual list updates.
    Auto-loads current malware family names for preservation during anonymization.
    """
    try:
        url = "https://malpedia.caad.fkie.fraunhofer.de/families/"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[Pattern Util] Failed to fetch malware names from Malpedia: HTTP {response.status_code}")
            return []

        # Extract malware names from <a href="/details/xyz">xyz</a>
        pattern = re.compile(r'<a href="/details/[^"]+">([^<]+)</a>')
        names = pattern.findall(response.text)
        
        # Clean and deduplicate
        names = list(set(name.strip() for name in names if name.strip()))
        print(f"[Pattern Util] Successfully fetched {len(names)} malware names from Malpedia")
        return names
        
    except Exception as e:
        print(f"[Pattern Util] Error fetching malware names from Malpedia: {e}")
        return []

class PatternManager:
    """Manages regex patterns for anonymization"""
    
    def __init__(self):
        self.patterns = {
            # Personal Information
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            
            # Technical Indicators (IoCs)
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
            'hash_md5': r'\b[a-fA-F0-9]{32}\b',
            'hash_sha1': r'\b[a-fA-F0-9]{40}\b',
            'hash_sha256': r'\b[a-fA-F0-9]{64}\b',
            'hash_sha512': r'\b[a-fA-F0-9]{128}\b',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'domain': r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b',
            
            # Cryptocurrency
            'bitcoin_address': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
            'ethereum_address': r'\b0x[a-fA-F0-9]{40}\b',
            
            # Names (basic patterns)
            'person_name': r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            'person_name_with_title': r'\b(?:Dr|Mr|Mrs|Ms|Agent|Detective|Officer)\.\s+[A-Z][a-z]+ [A-Z][a-z]+\b',
            
            # Organizations (basic patterns)
            'organization': r'\b[A-Z][a-zA-Z\s&]+(?:Inc|Corp|Corporation|Company|LLC|Ltd|Group|Systems|Solutions|Technologies|Services|International)\b',
        }
        
        self.compiled_patterns: Dict[str, Pattern] = {}
        self.malware_names: List[str] = []
        self._compile_patterns()
        self._load_malware_names()
    
    def _load_malware_names(self):
        """Load malware names from various sources"""
        malpedia_names = fetch_malware_names_from_malpedia()
        self.malware_names = malpedia_names
    
    def get_malware_names(self) -> List[str]:
        """Get list of known malware names"""
        return self.malware_names
    
    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        try:
            for name, pattern in self.patterns.items():
                self.compiled_patterns[name] = re.compile(pattern)
        except re.error as e:
            print(f"[Pattern Util] Error compiling pattern {name}: {e}")
    
    def get_pattern(self, name: str) -> Pattern:
        """Get a compiled pattern by name"""
        return self.compiled_patterns.get(name)
    
    def add_pattern(self, name: str, pattern: str):
        """Add a new pattern"""
        try:
            self.patterns[name] = pattern
            self.compiled_patterns[name] = re.compile(pattern)
        except re.error as e:
            print(f"[Pattern Util] Error adding pattern {name}: {e}")
    
    def get_all_patterns(self) -> Dict[str, Pattern]:
        """Get all compiled patterns"""
        return self.compiled_patterns.copy()
    
    def find_matches(self, text: str, pattern_name: str) -> List[str]:
        """Find all matches for a specific pattern"""
        pattern = self.get_pattern(pattern_name)
        if pattern:
            return pattern.findall(text)
        return []
