from typing import Dict, List
import numpy as np


class EvaluationMetrics:
    """Calculs de métriques pour l'évaluation"""

    @staticmethod
    def calculate_aggregate_scores(evaluations: List[Dict]) -> Dict:
        """
        Calcule les scores agrégés pour tous les chunks évalués

        Args:
            evaluations: Liste des évaluations

        Returns:
            Métriques agrégées
        """
        successful_evals = [
            eval_data for eval_data in evaluations if eval_data.get("success", False)
        ]

        if not successful_evals:
            return {"error": "No successful evaluations to aggregate"}

        # Extraction des scores
        rag_scores = []
        icl_scores = []
        accuracy_rag = []
        accuracy_icl = []
        coverage_rag = []
        coverage_icl = []
        relevance_rag = []
        relevance_icl = []
        specificity_rag = []
        specificity_icl = []

        for eval_data in successful_evals:
            evaluation = eval_data.get("evaluation", {})

            rag_scores.append(evaluation.get("rag_score", 0.0))
            icl_scores.append(evaluation.get("icl_score", 0.0))
            accuracy_rag.append(evaluation.get("accuracy_rag", 0.0))
            accuracy_icl.append(evaluation.get("accuracy_icl", 0.0))
            coverage_rag.append(evaluation.get("coverage_rag", 0.0))
            coverage_icl.append(evaluation.get("coverage_icl", 0.0))
            relevance_rag.append(evaluation.get("relevance_rag", 0.0))
            relevance_icl.append(evaluation.get("relevance_icl", 0.0))
            specificity_rag.append(evaluation.get("specificity_rag", 0.0))
            specificity_icl.append(evaluation.get("specificity_icl", 0.0))

        return {
            "overall_metrics": {
                "mean_rag_score": np.mean(rag_scores),
                "mean_icl_score": np.mean(icl_scores),
                "std_rag_score": np.std(rag_scores),
                "std_icl_score": np.std(icl_scores),
                "rag_wins": sum(
                    1
                    for eval_data in successful_evals
                    if eval_data.get("evaluation", {}).get("winner") == "rag"
                ),
                "icl_wins": sum(
                    1
                    for eval_data in successful_evals
                    if eval_data.get("evaluation", {}).get("winner") == "icl"
                ),
                "ties": sum(
                    1
                    for eval_data in successful_evals
                    if eval_data.get("evaluation", {}).get("winner") == "tie"
                ),
            },
            "detailed_metrics": {
                "accuracy": {
                    "rag_mean": np.mean(accuracy_rag),
                    "icl_mean": np.mean(accuracy_icl),
                    "rag_std": np.std(accuracy_rag),
                    "icl_std": np.std(accuracy_icl),
                },
                "coverage": {
                    "rag_mean": np.mean(coverage_rag),
                    "icl_mean": np.mean(coverage_icl),
                    "rag_std": np.std(coverage_rag),
                    "icl_std": np.std(coverage_icl),
                },
                "relevance": {
                    "rag_mean": np.mean(relevance_rag),
                    "icl_mean": np.mean(relevance_icl),
                    "rag_std": np.std(relevance_rag),
                    "icl_std": np.std(relevance_icl),
                },
                "specificity": {
                    "rag_mean": np.mean(specificity_rag),
                    "icl_mean": np.mean(specificity_icl),
                    "rag_std": np.std(specificity_rag),
                    "icl_std": np.std(specificity_icl),
                },
            },
            "sample_size": len(successful_evals),
        }
