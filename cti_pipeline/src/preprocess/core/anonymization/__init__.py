"""
Anonymization Module for CTI Preprocessing Pipeline

This module provides a modular, configurable anonymization system that:
- Preserves technical terms and CTI-specific vocabulary
- Maintains IoCs and threat intelligence indicators
- Uses conservative approach to avoid over-anonymization
- Follows DRY principles with modular components
"""

from .config import AnonymizationConfig
from .anonymizer import TextAnonymizer
from ..utils.patterns import PatternManager
from ..utils.preservers import PreservationManager
from .replacers import ReplacementManager

# Convenience functions
def anonymize_text(text: str, config: AnonymizationConfig = None) -> str:
    """Quick anonymization function"""
    anonymizer = TextAnonymizer(config)
    return anonymizer.anonymize(text)

def anonymize_cti_text(text: str) -> str:
    """Anonymize text with CTI-optimized settings"""
    config = AnonymizationConfig(
        preserve_technical_terms=True,
        preserve_iocs=True,
        preserve_domain_in_email=True,
        preserve_government_domains=True,
        preserve_facility_names=True,
        preserve_classification_levels=True,
        preserve_agency_names=True
    )
    return anonymize_text(text, config)

__all__ = [
    'AnonymizationConfig',
    'TextAnonymizer',
    'PatternManager',
    'PreservationManager',
    'ReplacementManager',
    'anonymize_text',
    'anonymize_cti_text'
]
