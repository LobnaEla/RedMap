import os
import json
from datetime import datetime
from typing import Dict

# Import des dépendances
from .anthropic_client import AnthropicClient


class ChunkProcessor:
    def __init__(self, api_key: str = None):
        """
        Processeur de chunks CTI pour le mapping MITRE

        Args:
            api_key: Clé API Anthropic (optionnelle)
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        # Configuration LLM
        self.llm_config = {
            "model": "claude-opus-4-20250514",
            "max_tokens": 200,
            "temperature": 0.1,
            "max_retries": 3,
            "batch_size": 10,
            "request_delay": 0.5,
            "file_delay": 2,
        }

        self.client = AnthropicClient(self.api_key, self.llm_config)

    def process_chunk(self, chunk: Dict, source_file: str) -> Dict:
        """
        Traite un seul chunk CTI pour le mapping MITRE

        Args:
            chunk: Dictionnaire contenant les données du chunk
            source_file: Nom du fichier source du chunk

        Returns:
            Dictionnaire contenant les résultats du mapping
        """
        # Validation des entrées
        if not isinstance(chunk, dict):
            return self._error_result("unknown", "Chunk must be a dictionary")

        chunk_id = chunk.get("chunk_id", "unknown")
        text = chunk.get("text", "")
        iocs = chunk.get("iocs", "")  # Default to empty string

        if not text.strip():
            return self._error_result(chunk_id, "Empty text content")

        if not isinstance(iocs, str):  # Changed validation to check for string
            return self._error_result(chunk_id, "IOCs must be a string")

        try:
            # Traitement du chunk
            mapping = self.client.map_to_mitre(
                text=text,
                iocs=iocs,  # Passing string IOCs
                chunk_id=chunk_id,
            )

            # Ajout des métadonnées
            mapping["source_file"] = source_file
            mapping["processing_time"] = datetime.now().isoformat()

            return mapping

        except Exception as e:
            return self._error_result(chunk_id, f"Processing error: {str(e)}")

    def _error_result(self, chunk_id: str, error: str) -> Dict:
        """Crée un résultat d'erreur standardisé"""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
