import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

from .prompt_utils import create_judge_prompt


class JudgeClient:
    """Client LLM pour l'évaluation comparative des techniques MITRE"""

    def __init__(self, api_key: str, model_config: Optional[Dict] = None):
        """
        Initialise le client Judge

        Args:
            api_key: Clé API Gemini
            model_config: Configuration du modèle
        """
        genai.configure(api_key=api_key)
        self.config = model_config or {
            "model": "gemini-2.0-flash",
            "temperature": 0.1,
            "max_retries": 3,
        }
        self.model = genai.GenerativeModel(self.config["model"])

    def evaluate_techniques(
        self,
        original_chunk: str,
        rag_output: List[str],
        icl_output: List[str],
        chunk_id: str,
    ) -> Dict:
        """
        Évalue et compare les techniques MITRE proposées par RAG vs ICL

        Args:
            original_chunk: Texte original du chunk CTI
            rag_output: Techniques proposées par le RAG
            icl_output: Techniques proposées par l'ICL
            chunk_id: Identifiant du chunk

        Returns:
            Dictionnaire contenant l'évaluation comparative
        """
        if not original_chunk.strip():
            return self._create_error_result(chunk_id, "Empty original chunk")

        # Validation des inputs
        rag_techniques = self._validate_techniques(rag_output)
        icl_techniques = self._validate_techniques(icl_output)

        prompt = create_judge_prompt(
            original_text=original_chunk,
            rag_techniques=rag_techniques,
            icl_techniques=icl_techniques,
        )

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
                    evaluation = self._parse_judge_response(content)
                    return self._create_success_result(
                        chunk_id=chunk_id,
                        original_chunk=original_chunk,
                        rag_techniques=rag_techniques,
                        icl_techniques=icl_techniques,
                        evaluation=evaluation,
                    )
                else:
                    return self._create_error_result(
                        chunk_id, "Empty response from Judge LLM"
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

    def _validate_techniques(self, techniques: List[str]) -> List[str]:
        """Valide et nettoie la liste des techniques"""
        if not isinstance(techniques, list):
            return []

        validated = []
        for tech in techniques:
            if isinstance(tech, str) and tech.strip():
                # Validation basique du format T1234 ou T1234.001
                tech = tech.strip().upper()
                if tech.startswith("T") and any(c.isdigit() for c in tech):
                    validated.append(tech)

        return validated

    def _parse_judge_response(self, response: str) -> Dict:
        """Parse la réponse du Judge LLM"""
        try:
            # Parse JSON
            if response.startswith("{") and response.endswith("}"):
                return json.loads(response)

            # Else, manual extraction
            evaluation = {
                "winner": "unknown",
                "rag_score": 0.0,
                "icl_score": 0.0,
                "accuracy_rag": 0.0,
                "accuracy_icl": 0.0,
                "coverage_rag": 0.0,
                "coverage_icl": 0.0,
                "relevance_rag": 0.0,
                "relevance_icl": 0.0,
                "reasoning": response,
            }

            # Extraction basique du gagnant
            response_lower = response.lower()
            if "rag" in response_lower and "better" in response_lower:
                evaluation["winner"] = "rag"
            elif "icl" in response_lower and "better" in response_lower:
                evaluation["winner"] = "icl"
            elif "tie" in response_lower or "equal" in response_lower:
                evaluation["winner"] = "tie"

            return evaluation

        except json.JSONDecodeError:
            return {
                "winner": "unknown",
                "rag_score": 0.0,
                "icl_score": 0.0,
                "reasoning": response,
                "parse_error": True,
            }

    def _create_success_result(
        self,
        chunk_id: str,
        original_chunk: str,
        rag_techniques: List[str],
        icl_techniques: List[str],
        evaluation: Dict,
    ) -> Dict:
        """Crée un résultat de succès"""
        return {
            "chunk_id": chunk_id,
            "original_chunk": original_chunk,
            "rag_techniques": rag_techniques,
            "icl_techniques": icl_techniques,
            "evaluation": evaluation,
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
