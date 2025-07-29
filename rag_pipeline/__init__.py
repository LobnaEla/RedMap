"""
MITRE ATT&CK RAG Retriever for CTI

A modular Python package that identifies relevant MITRE ATT&CK techniques
from CTI report chunks using Retrieval-Augmented Generation (RAG).
"""

from .config import Config

__version__ = "0.1.0"
__all__ = ["Config"]
