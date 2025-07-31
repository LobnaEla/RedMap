import os
import json
from datetime import datetime
from typing import Dict

# Import du client Gemini
from .gemini_client import GeminiClient
from .config import LLM_CONFIG

class ChunkProcessor:
    def __init__(self, api_key: str):
        """
        Processeur de chunks CTI pour le mapping MITRE via Gemini

        Args:
            api_key: Clé API Gemini (obligatoire)
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        # Utilise la configuration centralisée
        self.llm_config = LLM_CONFIG
        self.client = GeminiClient(self.api_key, self.llm_config)

    def process_chunk(self, chunk: Dict, source_file: str) -> Dict:
        """
        Traite un seul chunk CTI pour le mapping MITRE

        Args:
            chunk: Dictionnaire contenant les données du chunk
            source_file: Nom du fichier source du chunk

        Returns:
            Dictionnaire contenant les résultats du mapping
        """
        if not isinstance(chunk, dict):
            return self._error_result("unknown", "Chunk must be a dictionary")

        chunk_id = chunk.get("chunk_id", "unknown")
        text = chunk.get("text", "")
        iocs = chunk.get("iocs", "")

        if not text.strip():
            return self._error_result(chunk_id, "Empty text content")

        if not isinstance(iocs, str):
            return self._error_result(chunk_id, "IOCs must be a string")

        try:
            mapping = self.client.map_to_mitre(
                text=text,
                iocs=iocs,
                chunk_id=chunk_id,
            )

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
