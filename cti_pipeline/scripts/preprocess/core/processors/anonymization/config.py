"""
Configuration module for anonymization settings
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class AnonymizationConfig:
    """Configuration for anonymization behavior"""
    # Basic anonymization settings
    anonymize_emails: bool = True
    anonymize_phones: bool = True
    anonymize_addresses: bool = True
    anonymize_names: bool = True
    anonymize_credit_cards: bool = True
    anonymize_ssn: bool = True
    
    # Preservation settings
    preserve_domain_in_email: bool = True
    preserve_technical_terms: bool = True
    preserve_iocs: bool = True
    preserve_government_domains: bool = True
    preserve_facility_names: bool = True
    preserve_classification_levels: bool = True
    preserve_agency_names: bool = True
    
    # Fine-tuning parameters
    min_name_length: int = 3
    max_name_length: int = 50
    
    # Custom patterns (optional)
    custom_preserve_patterns: Optional[List[str]] = None
    custom_anonymize_patterns: Optional[Dict[str, str]] = None
    
    def __post_init__(self):
        """Initialize custom patterns if not provided"""
        if self.custom_preserve_patterns is None:
            self.custom_preserve_patterns = []
        if self.custom_anonymize_patterns is None:
            self.custom_anonymize_patterns = {}
