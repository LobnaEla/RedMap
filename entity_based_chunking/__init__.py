"""
CTI Entity-Based Chunking System

A robust pipeline for extracting Indicators of Compromise (IOCs) from 
Cyber Threat Intelligence (CTI) reports and intelligently chunking text 
based on detected IOCs.

Main API Functions:
    - process_cti_text: Process text directly
    - process_cti_file: Process file and return chunks
    - extract_iocs_only: Extract IOCs without chunking
    - create_processor: Create reusable processor instance

Example Usage:
    ```python
    from entity_chunking import process_cti_text, extract_iocs_only
    
    # Process text with chunking
    chunks = process_cti_text("Your CTI report text here...")
    
    # Extract IOCs only
    iocs = extract_iocs_only("Malware connects to 192.168.1.1...")
    ```
"""

# Import main API functions
from .main import (
    process_cti_text,
    process_cti_file,
    extract_iocs_only,
    create_processor
)

# Import core classes for advanced usage
from .chunking.processor import CTIProcessor
from .chunking.llm_client import LLMClient
from .chunking.text_chunker import TextChunker
from .utils.config import load_config, validate_config
from .utils.ioc_validator import IOCValidator

# Version information
__version__ = "2.0.0"
__author__ = "RedMap"

# Define what gets imported with "from entity_chunking import *"
__all__ = [
    # Main API functions
    "process_cti_text",
    "process_cti_file", 
    "extract_iocs_only",
    "create_processor",
    
    # Core classes
    "CTIProcessor",
    "LLMClient",
    "TextChunker",
    "IOCValidator",
    
    # Utility functions
    "load_config",
    "validate_config",
    
    # Version info
    "__version__",
    "__author__"
]
