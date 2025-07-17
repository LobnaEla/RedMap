"""
Replacement logic for anonymization
"""

from typing import Dict, Any
import sys
import os

# Use relative import for utils
from ..utils.utilities import get_content_hash

class ReplacementManager:
    """Manages consistent replacement of anonymized content"""
    
    def __init__(self):
        self.replacement_map: Dict[str, str] = {}
        self.replacement_counters: Dict[str, int] = {
            'email': 0,
            'phone': 0,
            'name': 0,
            'organization': 0,
            'address': 0
        }
    
    def generate_replacement(self, text: str, replacement_type: str) -> str:
        """Generate a consistent replacement for anonymized text"""
        # Check if we already have a replacement for this text
        if text in self.replacement_map:
            return self.replacement_map[text]
        
        # Use utilities.py for consistent hashing
        content_hash = get_content_hash(text, "generic")
        hash_short = content_hash[:8]
        
        # Generate replacements based on type
        if replacement_type == 'email':
            # Increment counter for uniqueness
            self.replacement_counters['email'] += 1
            replacement = f"user{self.replacement_counters['email']}_{hash_short}@example.com"
        
        elif replacement_type == 'phone':
            replacement = f"555-{hash_short[:3]}-{hash_short[3:7]}"
        
        elif replacement_type == 'name':
            self.replacement_counters['name'] += 1
            replacement = f"Person_{self.replacement_counters['name']}_{hash_short}"
        
        elif replacement_type == 'organization':
            self.replacement_counters['organization'] += 1
            replacement = f"Organization_{self.replacement_counters['organization']}_{hash_short}"
        
        elif replacement_type == 'address':
            self.replacement_counters['address'] += 1
            replacement = f"Address_{self.replacement_counters['address']}_{hash_short}"
        
        elif replacement_type == 'ssn':
            replacement = f"XXX-XX-{hash_short[:4]}"
        
        elif replacement_type == 'credit_card':
            replacement = f"XXXX-XXXX-XXXX-{hash_short[:4]}"
        
        else:
            replacement = f"REDACTED_{hash_short}"
        
        # Store the replacement for consistency
        self.replacement_map[text] = replacement
        return replacement
    
    def get_replacement_stats(self) -> Dict[str, Any]:
        """Get statistics about replacements made"""
        return {
            'total_replacements': len(self.replacement_map),
            'by_type': self.replacement_counters.copy(),
            'replacement_map_size': len(self.replacement_map)
        }
    
    def clear_replacements(self):
        """Clear all replacement mappings"""
        self.replacement_map.clear()
        for key in self.replacement_counters:
            self.replacement_counters[key] = 0
