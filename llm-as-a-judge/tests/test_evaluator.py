"""
Tests unitaires pour le TechniqueEvaluator
"""

import unittest
from unittest.mock import Mock, patch
import sys

sys.path.append("/opt/project/cti_pipeline")

from llm_as_a_judge.core.evaluator import TechniqueEvaluator


class TestTechniqueEvaluator(unittest.TestCase):

    def setUp(self):
        """Configuration des tests"""
        self.api_key = "test_api_key"

    @patch("llm_as_a_judge.core.evaluator.JudgeClient")
    def test_evaluator_initialization(self, mock_judge_client):
        """Test l'initialisation de l'évaluateur"""
        evaluator = TechniqueEvaluator(self.api_key)

        mock_judge_client.assert_called_once()
        self.assertEqual(evaluator.api_key, self.api_key)

    def test_evaluator_no_api_key(self):
        """Test l'erreur sans clé API"""
        with self.assertRaises(ValueError):
            TechniqueEvaluator(api_key=None)

    @patch("llm_as_a_judge.core.evaluator.JudgeClient")
    def test_evaluate_single_chunk(self, mock_judge_client):
        """Test l'évaluation d'un chunk unique"""
        # Mock du JudgeClient
        mock_client_instance = Mock()
        mock_client_instance.evaluate_techniques.return_value = {
            "success": True,
            "evaluation": {"winner": "rag", "rag_score": 0.8},
        }
        mock_judge_client.return_value = mock_client_instance

        evaluator = TechniqueEvaluator(self.api_key)

        chunk_data = {
            "chunk_id": "test_001",
            "text": "Test CTI content",
            "iocs": "test.exe",
            "source_file": "test.pdf",
        }

        result = evaluator.evaluate_single_chunk(
            chunk_data=chunk_data, rag_results=["T1001"], icl_results=["T1002"]
        )

        self.assertTrue(result["success"])
        self.assertIn("chunk_metadata", result)
        mock_client_instance.evaluate_techniques.assert_called_once()

    @patch("llm_as_a_judge.core.evaluator.JudgeClient")
    def test_batch_evaluate(self, mock_judge_client):
        """Test l'évaluation en batch"""
        # Mock du JudgeClient
        mock_client_instance = Mock()
        mock_client_instance.evaluate_techniques.side_effect = [
            {"success": True, "evaluation": {"winner": "rag"}},
            {"success": True, "evaluation": {"winner": "icl"}},
            {"success": False, "error": "Test error"},
        ]
        mock_judge_client.return_value = mock_client_instance

        evaluator = TechniqueEvaluator(self.api_key)

        chunks = [
            {"chunk_id": "001", "text": "Content 1"},
            {"chunk_id": "002", "text": "Content 2"},
            {"chunk_id": "003", "text": "Content 3"},
        ]

        rag_results = [["T1001"], ["T1002"], ["T1003"]]
        icl_results = [["T1001"], ["T1002"], ["T1003"]]

        result = evaluator.batch_evaluate(chunks, rag_results, icl_results)

        # Vérifications
        self.assertEqual(result["statistics"]["total_chunks"], 3)
        self.assertEqual(result["statistics"]["successful_evaluations"], 2)
        self.assertEqual(result["statistics"]["rag_wins"], 1)
        self.assertEqual(result["statistics"]["icl_wins"], 1)
        self.assertEqual(result["statistics"]["errors"], 1)
        self.assertEqual(len(result["evaluations"]), 3)

    @patch("llm_as_a_judge.core.evaluator.JudgeClient")
    def test_batch_evaluate_length_mismatch(self, mock_judge_client):
        """Test l'erreur de longueur différente"""
        evaluator = TechniqueEvaluator(self.api_key)

        chunks = [{"chunk_id": "001"}]
        rag_results = [["T1001"], ["T1002"]]  # Longueur différente
        icl_results = [["T1001"]]

        with self.assertRaises(ValueError):
            evaluator.batch_evaluate(chunks, rag_results, icl_results)


if __name__ == "__main__":
    unittest.main()
