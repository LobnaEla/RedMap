import json
import time
from datetime import datetime
from typing import List, Dict, Optional


# Import des utilitaires de prompt
from .prompt_utils import create_gemini_prompt
from .config import LLM_CONFIG


class GeminiClient:
    def __init__(self, api_key: str, model_config: Optional[Dict] = None):
        """
        Initialise le client Gemini (Google Generative AI)

        Args:
            api_key: Clé API Gemini
            model_config: Configuration du modèle LLM (optionnel, utilise LLM_CONFIG par défaut)
        """
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.config = model_config or LLM_CONFIG
        self.model = genai.GenerativeModel(self.config["model"])

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
        from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
        if not text.strip():
            return self._create_error_result(chunk_id, "Empty text")

        if not isinstance(iocs, str):
            return self._create_error_result(chunk_id, "IOCs must be a string")

        if not chunk_id:
            chunk_id = "unknown"

        prompt = create_gemini_prompt(text, iocs)

        for attempt in range(1, self.config["max_retries"] + 1):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": self.config["temperature"],
                    },
                )

                content = (
                    response.text.strip()
                    if response and hasattr(response, "text")
                    else ""
                )
                if content:
                    mitre_codes = self._parse_llm_response(content)
                    return self._create_success_result(
                        chunk_id, text, iocs, mitre_codes
                    )
                else:
                    return self._create_error_result(
                        chunk_id, "Empty response from LLM"
                    )

            except ResourceExhausted:
                wait_time = 2**attempt
                print(f"Rate limit exceeded. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            except GoogleAPIError as e:
                error_msg = f"API error: {str(e)}"
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
            if response.startswith("[") and response.endswith("]"):
                return json.loads(response)

            import re

            return re.findall(r"T\d+(?:\.\d+)?", response)

        except json.JSONDecodeError:
            return []

    def _create_success_result(
        self, chunk_id: str, text: str, iocs: str, techniques: List[str]
    ) -> Dict:
        return {
            "chunk_id": chunk_id,
            "original_text": text,
            "iocs": iocs,
            "mitre_techniques": techniques,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
