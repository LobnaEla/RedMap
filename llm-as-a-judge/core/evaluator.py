import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from .judge_client import JudgeClient
from .config import JUDGE_CONFIG, PATH_CONFIG


class TechniqueEvaluator:
    """Évaluateur principal pour comparer RAG vs ICL"""

    def __init__(self, api_key: str = None):
        """
        Initialise l'évaluateur

        Args:
            api_key: Clé API Gemini
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        self.judge_client = JudgeClient(self.api_key, JUDGE_CONFIG)

    def evaluate_single_chunk(
        self, chunk_data: Dict, rag_results: List[str], icl_results: List[str]
    ) -> Dict:
        """
        Évalue un seul chunk

        Args:
            chunk_data: Données du chunk original
            rag_results: Résultats du RAG
            icl_results: Résultats de l'ICL

        Returns:
            Résultats de l'évaluation
        """
        chunk_id = chunk_data.get("chunk_id", "unknown")
        original_text = chunk_data.get("text", "")

        if not original_text.strip():
            return self._create_error_result(chunk_id, "Empty chunk text")

        try:
            evaluation = self.judge_client.evaluate_techniques(
                original_chunk=original_text,
                rag_output=rag_results,
                icl_output=icl_results,
                chunk_id=chunk_id,
            )

            # Ajouter des métadonnées supplémentaires
            evaluation["chunk_metadata"] = {
                "iocs": chunk_data.get("iocs", ""),
                "source_file": chunk_data.get("source_file", ""),
                "processing_time": datetime.now().isoformat(),
            }

            return evaluation

        except Exception as e:
            return self._create_error_result(chunk_id, f"Evaluation error: {str(e)}")

    def batch_evaluate(
        self,
        chunks: List[Dict],
        rag_results_list: List[List[str]],
        icl_results_list: List[List[str]],
    ) -> Dict:
        """
        Évalue un batch de chunks

        Args:
            chunks: Liste des chunks
            rag_results_list: Liste des résultats RAG
            icl_results_list: Liste des résultats ICL

        Returns:
            Résultats agrégés de l'évaluation
        """
        if not (len(chunks) == len(rag_results_list) == len(icl_results_list)):
            raise ValueError("Length mismatch between inputs")

        evaluations = []
        stats = {
            "total_chunks": len(chunks),
            "successful_evaluations": 0,
            "rag_wins": 0,
            "icl_wins": 0,
            "ties": 0,
            "errors": 0,
            "start_time": datetime.now().isoformat(),
        }

        for i, (chunk, rag_results, icl_results) in enumerate(
            zip(chunks, rag_results_list, icl_results_list)
        ):
            print(f"Evaluating chunk {i+1}/{len(chunks)}")

            evaluation = self.evaluate_single_chunk(chunk, rag_results, icl_results)
            evaluations.append(evaluation)

            # Mise à jour des statistiques
            if evaluation.get("success", False):
                stats["successful_evaluations"] += 1
                winner = evaluation.get("evaluation", {}).get("winner", "unknown")

                if winner == "rag":
                    stats["rag_wins"] += 1
                elif winner == "icl":
                    stats["icl_wins"] += 1
                elif winner == "tie":
                    stats["ties"] += 1
            else:
                stats["errors"] += 1

        stats["end_time"] = datetime.now().isoformat()
        stats["success_rate"] = stats["successful_evaluations"] / stats["total_chunks"]

        return {
            "evaluations": evaluations,
            "statistics": stats,
            "metadata": {
                "evaluation_config": JUDGE_CONFIG,
                "generated_at": stats["end_time"],
            },
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Crée un résultat d'erreur"""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
