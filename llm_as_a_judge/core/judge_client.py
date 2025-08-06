# llm_as_a_judge/core/technique_validator.py

import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from .judge_client import JudgeClient
from .config import VALIDATION_CONFIG


class TechniqueValidator:
    """Validateur principal pour le système LLM-as-a-Judge de validation croisée.

    Intégration Pipeline:
    Chunks CTI → RAG System → Techniques RAG
         ↓            ↓
         → LLM ICL → Techniques LLM
                        ↓
                  LLM-as-a-Judge
                        ↓
                Techniques Validées
    """

    def __init__(self, api_key: str = None):
        """
        Initialise le validateur.

        Args:
            api_key: Clé API Gemini. Si non fournie, utilise GEMINI_API_KEY.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not configured. Set it in environment or pass as argument."
            )

        self.judge_client = JudgeClient(
            api_key=self.api_key, model_config=VALIDATION_CONFIG
        )

    def validate_single_chunk(
        self, chunk_data: Dict, rag_results: List[str], llm_results: List[str]
    ) -> Dict:
        """
        Valide un seul chunk en croisant les résultats RAG et LLM.

        Args:
            chunk_data: Données du chunk CTI (text, iocs, chunk_id, etc.)
            rag_results: Techniques MITRE extraites par le système RAG/RAS
            llm_results: Techniques MITRE prédites par le LLM (via ICL)

        Returns:
            Dictionnaire contenant les résultats de validation croisée.
        """
        chunk_id = chunk_data.get("chunk_id", "unknown")
        original_text = chunk_data.get("text", "")
        iocs = chunk_data.get("iocs", "")

        if not original_text.strip():
            return self._create_error_result(chunk_id, "Empty chunk text")

        try:
            # Appel au juge pour validation croisée
            validation_result = self.judge_client.validate_techniques_cross_reference(
                original_chunk=original_text,
                rag_techniques=rag_results,
                llm_techniques=llm_results,
                chunk_id=chunk_id,
                iocs=iocs,
            )

            # Ajouter les métadonnées du chunk
            if validation_result.get("success", False):
                validation_result["chunk_metadata"] = {
                    "source_file": chunk_data.get("source_file", ""),
                    "processing_time": datetime.now().isoformat(),
                    "validation_config": VALIDATION_CONFIG.copy(),
                }

            return validation_result

        except Exception as e:
            return self._create_error_result(chunk_id, f"Validation error: {str(e)}")

    def batch_validate(
        self,
        chunks: List[Dict],
        rag_results_list: List[List[str]],
        llm_results_list: List[List[str]],
    ) -> Dict:
        """
        Valide un batch de chunks.

        Args:
            chunks: Liste des chunks CTI
            rag_results_list: Liste des techniques RAG pour chaque chunk
            llm_results_list: Liste des techniques LLM pour chaque chunk

        Returns:
            Résultats agrégés avec statistiques.
        """
        if not (len(chunks) == len(rag_results_list) == len(llm_results_list)):
            raise ValueError(
                "Length mismatch between chunks, rag_results_list, and llm_results_list"
            )

        validations = []
        stats = {
            "total_chunks": len(chunks),
            "successful_validations": 0,
            "total_techniques_analyzed": 0,
            "total_techniques_validated": 0,
            "average_validation_rate": 0.0,
            "consensus_accuracy": 0.0,
            "rag_only_contribution": 0.0,
            "llm_only_contribution": 0.0,
            "errors": 0,
            "start_time": datetime.now().isoformat(),
        }

        validation_rates = []
        consensus_scores = []
        rag_only_contributions = []
        llm_only_contributions = []

        for i, (chunk, rag_results, llm_results) in enumerate(
            zip(chunks, rag_results_list, llm_results_list)
        ):
            print(
                f"🟡 Validating chunk {i+1}/{len(chunks)} - ID: {chunk.get('chunk_id', 'N/A')}"
            )

            validation = self.validate_single_chunk(chunk, rag_results, llm_results)
            validations.append(validation)

            if validation.get("success", False):
                stats["successful_validations"] += 1

                input_analysis = validation.get("input_analysis", {})
                validated_techniques = set(
                    validation.get("final_validated_techniques", [])
                )

                total_analyzed = input_analysis.get("total_unique_techniques", 0)
                validated_count = len(validated_techniques)

                stats["total_techniques_analyzed"] += total_analyzed
                stats["total_techniques_validated"] += validated_count

                if total_analyzed > 0:
                    validation_rates.append(validated_count / total_analyzed)

                # Consensus accuracy: % of common techniques validated
                common_techniques = set(input_analysis.get("common_techniques", []))
                if common_techniques:
                    consensus_validated = len(
                        common_techniques.intersection(validated_techniques)
                    )
                    consensus_scores.append(
                        consensus_validated / len(common_techniques)
                    )

                # RAG-only contribution
                rag_only = set(input_analysis.get("rag_only_techniques", []))
                if rag_only:
                    rag_only_validated = len(
                        rag_only.intersection(validated_techniques)
                    )
                    rag_only_contributions.append(rag_only_validated / len(rag_only))

                # LLM-only contribution
                llm_only = set(input_analysis.get("llm_only_techniques", []))
                if llm_only:
                    llm_only_validated = len(
                        llm_only.intersection(validated_techniques)
                    )
                    llm_only_contributions.append(llm_only_validated / len(llm_only))
            else:
                stats["errors"] += 1

        # Compute averages
        stats["average_validation_rate"] = (
            sum(validation_rates) / len(validation_rates) if validation_rates else 0.0
        )
        stats["consensus_accuracy"] = (
            sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
        )
        stats["rag_only_contribution"] = (
            sum(rag_only_contributions) / len(rag_only_contributions)
            if rag_only_contributions
            else 0.0
        )
        stats["llm_only_contribution"] = (
            sum(llm_only_contributions) / len(llm_only_contributions)
            if llm_only_contributions
            else 0.0
        )

        stats["end_time"] = datetime.now().isoformat()
        stats["success_rate"] = stats["successful_validations"] / stats["total_chunks"]

        return {
            "validations": validations,
            "statistics": stats,
            "metadata": {
                "validation_config": VALIDATION_CONFIG,
                "generated_at": stats["end_time"],
                "total_processed": len(chunks),
            },
        }

    def extract_final_techniques(self, judge_results: Dict) -> Dict[str, List[str]]:
        """
        Extrait les techniques finales validées pour chaque chunk.

        Args:
            judge_results: Résultats de `batch_validate()`

        Returns:
            Dictionnaire: chunk_id → liste des techniques validées
        """
        return {
            validation["chunk_id"]: validation.get("final_validated_techniques", [])
            for validation in judge_results.get("validations", [])
            if validation.get("success", False)
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Crée un résultat d'erreur standardisé."""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
