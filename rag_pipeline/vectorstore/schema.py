"""
Weaviate schema definition
"""
from typing import Dict, Any


class WeaviateSchema:
    """Weaviate schema definitions for MITRE techniques"""
    
    @staticmethod
    def get_mitre_technique_schema(class_name: str = "MitreTechnique") -> Dict[str, Any]:
        """
        Get Weaviate schema for MITRE technique class
        
        Args:
            class_name: Name of the Weaviate class
            
        Returns:
            Schema dictionary for Weaviate
        """
        return {
            "class": class_name,
            "description": "MITRE ATT&CK technique or sub-technique",
            "vectorizer": "none",  # We'll provide our own vectors
            "properties": [
                {
                    "name": "technique_id",
                    "dataType": ["text"],
                    "description": "MITRE technique ID (e.g., T1001, T1001.001)"
                },
                {
                    "name": "name",
                    "dataType": ["text"],
                    "description": "Technique name"
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Technique description"
                },
                {
                    "name": "url",
                    "dataType": ["text"],
                    "description": "MITRE ATT&CK URL"
                },
                {
                    "name": "platforms",
                    "dataType": ["text[]"],
                    "description": "Supported platforms"
                },
                {
                    "name": "kill_chain_phases",
                    "dataType": ["text[]"],
                    "description": "MITRE kill chain phases"
                },
                {
                    "name": "data_sources",
                    "dataType": ["text[]"],
                    "description": "Detection data sources"
                },
                {
                    "name": "detection",
                    "dataType": ["text"],
                    "description": "Detection guidance"
                }
            ]
        }
