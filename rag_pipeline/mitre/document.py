"""
MITRE ATT&CK document structure
"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class MitreDocument:
    """Represents a MITRE ATT&CK technique or sub-technique"""
    
    id: str  # e.g., "T1001", "T1001.001"
    name: str  # e.g., "Data Obfuscation"
    description: str  # Main description text
    url: str  # MITRE ATT&CK URL
    platforms: List[str]  # e.g., ["Linux", "macOS", "Windows"]
    kill_chain_phases: List[str]  # e.g., ["Command and Control"]
    data_sources: List[str]  # Detection data sources
    detection: str  # Detection guidance
    
    def __post_init__(self):
        """Convert comma-separated strings to lists"""
        if isinstance(self.platforms, str):
            self.platforms = [p.strip() for p in self.platforms.split(",")]
        if isinstance(self.kill_chain_phases, str):
            self.kill_chain_phases = [p.strip() for p in self.kill_chain_phases.split(",")]
        if isinstance(self.data_sources, str):
            self.data_sources = [p.strip() for p in self.data_sources.split(",")]
    
    @property
    def content_for_embedding(self) -> str:
        """Get text content for embedding generation"""
        return f"{self.name}. {self.description}"
    
    @property
    def metadata(self) -> dict:
        """Get metadata for vector store"""
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "platforms": self.platforms,
            "kill_chain_phases": self.kill_chain_phases,
            "data_sources": self.data_sources
        }
    
    def __str__(self) -> str:
        return f"MitreDocument(id={self.id}, name={self.name})"
