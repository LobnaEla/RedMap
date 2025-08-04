"""
Tests unitaires pour les métriques
"""

import unittest
import sys

sys.path.append("/opt/project/cti_pipeline")

from llm_as_a_judge.utils.metrics import EvaluationMetrics


class TestEvaluationMetrics(unittest.TestCase):

    def test_calculate_aggregate_scores(self):
        """Test le calcul des scores agrégés"""
        evaluations = [
            {
                "success": True,
                "evaluation": {
                    "winner": "rag",
                    "rag_score": 0.8,
                    "icl_score": 0.6,
                    "accuracy_rag": 0.9,
                    "accuracy_icl": 0.7,
                    "coverage_rag": 0.8,
                    "coverage_icl": 0.6,
                    "relevance_rag": 0.7,
                    "relevance_icl": 0.5,
                    "specificity_rag": 0.8,
                    "specificity_icl": 0.6,
                },
            },
            {
                "success": True,
                "evaluation": {
                    "winner": "icl",
                    "rag_score": 0.6,
                    "icl_score": 0.8,
                    "accuracy_rag": 0.7,
                    "accuracy_icl": 0.9,
                    "coverage_rag": 0.6,
                    "coverage_icl": 0.8,
                    "relevance_rag": 0.5,
                    "relevance_icl": 0.7,
                    "specificity_rag": 0.6,
                    "specificity_icl": 0.8,
                },
            },
            {"success": False, "error": "Test error"},
        ]

        metrics = EvaluationMetrics.calculate_aggregate_scores(evaluations)

        # Vérifications
        self.assertEqual(metrics["sample_size"], 2)
        self.assertEqual(metrics["overall_metrics"]["rag_wins"], 1)
        self.assertEqual(metrics["overall_metrics"]["icl_wins"], 1)
        self.assertEqual(metrics["overall_metrics"]["ties"], 0)

        # Vérification des moyennes
        self.assertAlmostEqual(
            metrics["overall_metrics"]["mean_rag_score"], 0.7, places=2
        )
        self.assertAlmostEqual(
            metrics["overall_metrics"]["mean_icl_score"], 0.7, places=2
        )

        # Vérification des métriques détaillées
        self.assertAlmostEqual(
            metrics["detailed_metrics"]["accuracy"]["rag_mean"], 0.8, places=2
        )
        self.assertAlmostEqual(
            metrics["detailed_metrics"]["accuracy"]["icl_mean"], 0.8, places=2
        )

    def test_calculate_aggregate_scores_empty(self):
        """Test avec des évaluations vides"""
        evaluations = [
            {"success": False, "error": "Error 1"},
            {"success": False, "error": "Error 2"},
        ]

        metrics = EvaluationMetrics.calculate_aggregate_scores(evaluations)

        self.assertIn("error", metrics)
        self.assertEqual(metrics["error"], "No successful evaluations to aggregate")


if __name__ == "__main__":
    unittest.main()
