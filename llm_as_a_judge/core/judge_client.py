import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Set

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

from .prompt_utils import create_judge_prompt


class JudgeClient:
    """Client LLM pour la validation croisée des techniques MITRE"""

    def __init__(self, api_key: str, model_config: Optional[Dict] = None):
        """
        Initialise le client de llm-as-a-judge

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

    def validate_techniques_cross_reference(
        self,
        original_chunk: str,
        rag_techniques: List[str],
        llm_techniques: List[str],
        chunk_id: str,
        iocs: str = "",
    ) -> Dict:
        """
        Valide les techniques en croisant RAG et LLM par rapport au chunk original

        Args:
            original_chunk: Texte original du chunk CTI
            rag_techniques: Techniques proposées par le RAG/RAS
            llm_techniques: Techniques proposées par le premier LLM
            chunk_id: Identifiant du chunk
            iocs: Indicateurs de compromission

        Returns:
            Dictionnaire contenant la validation croisée
        """
        if not original_chunk.strip():
            return self._create_error_result(chunk_id, "Empty original chunk")

        # Nettoyage et validation des techniques
        rag_clean = self._clean_techniques(rag_techniques)
        llm_clean = self._clean_techniques(llm_techniques)

        # Création des ensembles pour l'analyse
        rag_set = set(rag_clean)
        llm_set = set(llm_clean)

        # Techniques communes (intersection)
        common_techniques = list(rag_set.intersection(llm_set))

        # Techniques uniquement dans RAG
        rag_only = list(rag_set - llm_set)

        # Techniques uniquement dans LLM
        llm_only = list(llm_set - rag_set)

        # Union de toutes les techniques à analyser
        all_techniques = list(rag_set.union(llm_set))

        prompt = create_judge_prompt(
            original_text=original_chunk,
            iocs=iocs,
            common_techniques=common_techniques,
            rag_only_techniques=rag_only,
            llm_only_techniques=llm_only,
            all_techniques=all_techniques,
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
                    judge_result = self._parse_judge_response(content)
                    return self._create_success_result(
                        chunk_id=chunk_id,
                        original_chunk=original_chunk,
                        iocs=iocs,
                        rag_techniques=rag_clean,
                        llm_techniques=llm_clean,
                        common_techniques=common_techniques,
                        rag_only=rag_only,
                        llm_only=llm_only,
                        validation=judge_result,
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

    def _clean_techniques(self, techniques: List[str]) -> List[str]:
        """Nettoie et valide la liste des techniques"""
        if not isinstance(techniques, list):
            return []

        cleaned = []
        for tech in techniques:
            if isinstance(tech, str) and tech.strip():
                # Validation basique du format T1234 ou T1234.001
                tech = tech.strip().upper()
                if tech.startswith("T") and any(c.isdigit() for c in tech):
                    cleaned.append(tech)

        return cleaned

    def _parse_judge_response(self, response: str) -> Dict:
        """Parse la réponse du LLM de jugement"""
        try:
            # Essaie de parser comme JSON d'abord
            if response.startswith("{") and response.endswith("}"):
                return json.loads(response)

            # Extraction manuelle si pas de JSON valide
            validation = {
                "validated_techniques": [],
                "rejected_techniques": [],
                "technique_analysis": {},
                "reasoning": response,
                "confidence_scores": {},
            }

            # Extraction basique des techniques validées
            import re

            techniques_found = re.findall(r"T\d+(?:\.\d+)?", response)
            validation["validated_techniques"] = list(set(techniques_found))

            return validation

        except json.JSONDecodeError:
            return {
                "validated_techniques": [],
                "rejected_techniques": [],
                "technique_analysis": {},
                "reasoning": response,
                "parse_error": True,
            }

    def _create_success_result(
        self,
        chunk_id: str,
        original_chunk: str,
        iocs: str,
        rag_techniques: List[str],
        llm_techniques: List[str],
        common_techniques: List[str],
        rag_only: List[str],
        llm_only: List[str],
        validation: Dict,
    ) -> Dict:
        """Crée un résultat de succès"""
        return {
            "chunk_id": chunk_id,
            "original_chunk": original_chunk,
            "iocs": iocs,
            "input_analysis": {
                "rag_techniques": rag_techniques,
                "llm_techniques": llm_techniques,
                "common_techniques": common_techniques,
                "rag_only_techniques": rag_only,
                "llm_only_techniques": llm_only,
                "total_unique_techniques": len(set(rag_techniques + llm_techniques)),
            },
            "judge_result": validation,
            "final_validated_techniques": validation.get("validated_techniques", []),
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
