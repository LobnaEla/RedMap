"""
IOC Validation and Utility Functions
"""

import re
import logging
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

class IOCValidator:
    """Utility class for validating and categorizing IOCs."""
    
    # Regex patterns for different IOC types
    PATTERNS = {
        'ipv4': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        'ipv6': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
        'domain': r'\b[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',
        'url': r'https?://[^\s<>"{}|\\^`\[\]]+',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'md5': r'\b[a-fA-F0-9]{32}\b',
        'sha1': r'\b[a-fA-F0-9]{40}\b',
        'sha256': r'\b[a-fA-F0-9]{64}\b',
        'sha512': r'\b[a-fA-F0-9]{128}\b',
        'cve': r'CVE-\d{4}-\d{4,}',
        'mitre_technique': r'T\d{4}(\.\d{3})?',
        'bitcoin': r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',
    }
    
    @classmethod
    def validate_ioc(cls, ioc: str, ioc_type: str) -> bool:
        """Validate an IOC against its expected pattern."""
        ioc = ioc.strip()
        ioc_type = ioc_type.lower()
        
        # Map common type names to our patterns
        type_mapping = {
            'ip': 'ipv4',
            'ip_address': 'ipv4',
            'hash': 'md5', 
            'file_hash': 'md5',
            'vulnerability': 'cve',
            'technique': 'mitre_technique',
            'cryptocurrency': 'bitcoin',
        }
        
        pattern_key = type_mapping.get(ioc_type, ioc_type)
        pattern = cls.PATTERNS.get(pattern_key)
        
        if not pattern:
            # If no pattern, assume it's valid (custom IOC type)
            return True
        
        return bool(re.match(pattern, ioc))
    
    @classmethod
    def auto_detect_type(cls, ioc: str) -> str:
        """Automatically detect the type of an IOC."""
        ioc = ioc.strip()
        
        for ioc_type, pattern in cls.PATTERNS.items():
            if re.match(pattern, ioc):
                return ioc_type
        
        return 'unknown'
    
    @classmethod
    def clean_iocs(cls, iocs: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Clean and validate a list of IOCs."""
        cleaned = []
        seen = set()
        
        for ioc_data in iocs:
            ioc = ioc_data.get('ioc', '').strip()
            ioc_type = ioc_data.get('type', '').strip()
            
            if not ioc or not ioc_type:
                continue
            
            # Normalize IOC
            ioc_lower = ioc.lower()
            if ioc_lower in seen:
                continue
            
            # Validate IOC
            if cls.validate_ioc(ioc, ioc_type):
                cleaned.append({
                    'ioc': ioc,
                    'type': ioc_type
                })
                seen.add(ioc_lower)
            else:
                logger.debug(f"Invalid IOC filtered out: {ioc} (type: {ioc_type})")
        
        return cleaned
