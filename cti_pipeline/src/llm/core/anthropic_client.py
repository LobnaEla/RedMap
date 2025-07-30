import json
import time
from datetime import datetime
from anthropic import Anthropic, RateLimitError, APIError
from typing import List, Dict, Optional

# Import des utilitaires de prompt
from .prompt_utils import create_gemini_prompt


class AnthropicClient:
    def __init__(self, api_key: str, model_config: Optional[Dict] = None):
        """
        Initialise le client Anthropic pour l'API Claude

        Args:
            api_key: Clé API Anthropic
            model_config: Configuration du modèle LLM
        """
        self.client = Anthropic(api_key=api_key)
        self.config = model_config or {
            "model": "claude-opus-4-20250514",
            "max_tokens": 200,
            "temperature": 0.1,
            "max_retries": 3,
        }

    def map_to_mitre(self, text: str, iocs: str, chunk_id: str) -> Dict:
        """
        Mappe un texte CTI aux techniques MITRE ATT&CK

        Args:
            text: Texte CTI à analyser
            iocs: Indicateurs de compromission (chaîne de caractères)
            chunk_id: Identifiant unique du chunk

        Returns:
            Dictionnaire contenant les résultats du mapping
        """
        # Validation des entrées
        if not text.strip():
            return self._create_error_result(chunk_id, "Empty text")

        if not isinstance(iocs, str):
            return self._create_error_result(chunk_id, "IOCs must be a string")

        if not chunk_id:
            chunk_id = "unknown"

        # Création du prompt structuré
        prompt = create_gemini_prompt(text, iocs)

        # Tentatives avec gestion des erreurs
        for attempt in range(1, self.config["max_retries"] + 1):
            try:
                response = self.client.messages.create(
                    model=self.config["model"],
                    temperature=self.config["temperature"],
                    max_tokens=self.config["max_tokens"],
                    messages=[{"role": "user", "content": prompt}],
                )

                if response.content and response.content[0].text:
                    content = response.content[0].text.strip()
                    mitre_codes = self._parse_llm_response(content)
                    return self._create_success_result(
                        chunk_id, text, iocs, mitre_codes
                    )
                else:
                    return self._create_error_result(
                        chunk_id, "Empty response from LLM"
                    )

            except RateLimitError:
                wait_time = 2**attempt  # Backoff exponentiel
                print(f"Rate limit exceeded. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            except APIError as e:
                error_msg = f"API error: {e.message}"
                print(error_msg)
                return self._create_error_result(chunk_id, error_msg)

            except Exception as e:
                return self._create_error_result(
                    chunk_id, f"Unexpected error: {str(e)}"
                )

        return self._create_error_result(
            chunk_id, f"Failed after {self.config['max_retries']} attempts"
        )

    def _parse_llm_response(self, response: str) -> List[str]:
        """Parse la réponse du LLM pour extraire les codes MITRE"""
        try:
            # Essayer de parser comme JSON
            if response.startswith("[") and response.endswith("]"):
                return json.loads(response)

            # Fallback: extraction avec regex
            import re

            return re.findall(r"T\d+(?:\.\d+)?", response)

        except json.JSONDecodeError:
            return []

    def _create_success_result(
        self, chunk_id: str, text: str, iocs: str, techniques: List[str]
    ) -> Dict:
        """Crée un résultat de mapping réussi"""
        return {
            "chunk_id": chunk_id,
            "original_text": text,
            "iocs": iocs,
            "mitre_techniques": techniques,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Crée un résultat d'erreur"""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
