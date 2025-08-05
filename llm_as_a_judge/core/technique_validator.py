import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from .judge_client import JudgeClient
from .config import VALIDATION_CONFIG, PATH_CONFIG


class TechniqueValidator:
    """Validateur principal pour le llm-as-a-judge"""

    def __init__(self, api_key: str = None):
        """
        Initialise le judge

        Args:
            api_key: Clé API Gemini
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        self.judge_client = JudgeClient(self.api_key, VALIDATION_CONFIG)

    def validate_single_chunk(
        self, chunk_data: Dict, rag_results: List[str], llm_results: List[str]
    ) -> Dict:
        """
        Valide un seul chunk

        Args:
            chunk_data: Données du chunk original
            rag_results: Résultats du RAG/RAS
            llm_results: Résultats du premier LLM

        Returns:
            Résultats de la validation
        """
        chunk_id = chunk_data.get("chunk_id", "unknown")
        original_text = chunk_data.get("text", "")
        iocs = chunk_data.get("iocs", "")

        if not original_text.strip():
            return self._create_error_result(chunk_id, "Empty chunk text")

        try:
            validation = self.judge_client.validate_techniques_cross_reference(
                original_chunk=original_text,
                rag_techniques=rag_results,
                llm_techniques=llm_results,
                chunk_id=chunk_id,
                iocs=iocs,
            )

            # Ajouter des métadonnées supplémentaires
            if validation.get("success", False):
                validation["chunk_metadata"] = {
                    "source_file": chunk_data.get("source_file", ""),
                    "processing_time": datetime.now().isoformat(),
                    "validation_config": VALIDATION_CONFIG,
                }

            return validation

        except Exception as e:
            return self._create_error_result(chunk_id, f"Validation error: {str(e)}")

    def batch_validate(
        self,
        chunks: List[Dict],
        rag_results_list: List[List[str]],
        llm_results_list: List[List[str]],
    ) -> Dict:
        """
        Valide un batch de chunks

        Args:
            chunks: Liste des chunks
            rag_results_list: Liste des résultats RAG
            llm_results_list: Liste des résultats LLM

        Returns:
            Résultats agrégés de la validation
        """
        if not (len(chunks) == len(rag_results_list) == len(llm_results_list)):
            raise ValueError("Length mismatch between inputs")

        validations = []
        stats = {
            "total_chunks": len(chunks),
            "successful_validations": 0,
            "total_techniques_analyzed": 0,
            "total_techniques_validated": 0,
            "average_validation_rate": 0.0,
            "consensus_accuracy": 0.0,
            "errors": 0,
            "start_time": datetime.now().isoformat(),
        }

        validation_rates = []
        consensus_scores = []

        for i, (chunk, rag_results, llm_results) in enumerate(
            zip(chunks, rag_results_list, llm_results_list)
        ):
            print(f"Validating chunk {i+1}/{len(chunks)}")

            validation = self.validate_single_chunk(chunk, rag_results, llm_results)
            validations.append(validation)

            # Mise à jour des statistiques
            if validation.get("success", False):
                stats["successful_validations"] += 1

                # Analyse des techniques
                input_analysis = validation.get("input_analysis", {})
                judge_result = validation.get("judge_result", {})

                total_analyzed = input_analysis.get("total_unique_techniques", 0)
                validated_count = len(validation.get("final_validated_techniques", []))

                stats["total_techniques_analyzed"] += total_analyzed
                stats["total_techniques_validated"] += validated_count

                if total_analyzed > 0:
                    validation_rate = validated_count / total_analyzed
                    validation_rates.append(validation_rate)

                # Analyse du consensus (techniques communes validées)
                common_techniques = input_analysis.get("common_techniques", [])
                validated_techniques = validation.get("final_validated_techniques", [])

                if common_techniques:
                    common_validated = len(
                        set(common_techniques).intersection(set(validated_techniques))
                    )
                    consensus_score = common_validated / len(common_techniques)
                    consensus_scores.append(consensus_score)
            else:
                stats["errors"] += 1

        # Calcul des moyennes
        if validation_rates:
            stats["average_validation_rate"] = sum(validation_rates) / len(
                validation_rates
            )

        if consensus_scores:
            stats["consensus_accuracy"] = sum(consensus_scores) / len(consensus_scores)

        stats["end_time"] = datetime.now().isoformat()
        stats["success_rate"] = stats["successful_validations"] / stats["total_chunks"]

        return {
            "validations": validations,
            "statistics": stats,
            "metadata": {
                "validation_config": VALIDATION_CONFIG,
                "generated_at": stats["end_time"],
            },
        }

    def extract_final_techniques(self, judge_results: Dict) -> Dict[str, List[str]]:
        """
        Extrait les techniques finales validées pour chaque chunk

        Args:
            judge_results: Résultats du jugement batch

        Returns:
            Dictionnaire chunk_id -> techniques validées
        """
        final_techniques = {}

        for validation in judge_results.get("validations", []):
            if validation.get("success", False):
                chunk_id = validation.get("chunk_id")
                validated_techniques = validation.get("final_validated_techniques", [])
                final_techniques[chunk_id] = validated_techniques

        return final_techniques

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Crée un résultat d'erreur"""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
