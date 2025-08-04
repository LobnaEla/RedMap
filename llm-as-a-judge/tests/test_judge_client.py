"""
Tests unitaires pour le JudgeClient
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append("/opt/project/cti_pipeline")

from llm_as_a_judge.core.judge_client import JudgeClient


class TestJudgeClient(unittest.TestCase):

    def setUp(self):
        """Configuration des tests"""
        self.api_key = "test_api_key"
        self.config = {"model": "gemini-pro", "temperature": 0.1, "max_retries": 2}

    @patch("llm_as_a_judge.core.judge_client.genai")
    def test_judge_client_initialization(self, mock_genai):
        """Test l'initialisation du JudgeClient"""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model

        client = JudgeClient(self.api_key, self.config)

        mock_genai.configure.assert_called_once_with(api_key=self.api_key)
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        self.assertEqual(client.config, self.config)
        self.assertEqual(client.model, mock_model)

    def test_validate_techniques(self):
        """Test la validation des techniques"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            # Test avec des techniques valides
            valid_techniques = ["T1001", "T1002.001", "t1003"]
            result = client._validate_techniques(valid_techniques)
            expected = ["T1001", "T1002.001", "T1003"]
            self.assertEqual(result, expected)

            # Test avec des techniques invalides
            invalid_techniques = ["", "INVALID", "123", None]
            result = client._validate_techniques(invalid_techniques)
            self.assertEqual(result, [])

            # Test avec input non-liste
            result = client._validate_techniques("not_a_list")
            self.assertEqual(result, [])

    def test_parse_judge_response_json(self):
        """Test le parsing des réponses JSON"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            json_response = """{"winner": "rag", "rag_score": 0.8, "icl_score": 0.6}"""
            result = client._parse_judge_response(json_response)

            expected = {"winner": "rag", "rag_score": 0.8, "icl_score": 0.6}
            self.assertEqual(result, expected)

    def test_parse_judge_response_text(self):
        """Test le parsing des réponses texte"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            text_response = "RAG performs better than ICL in this case"
            result = client._parse_judge_response(text_response)

            self.assertEqual(result["winner"], "rag")
            self.assertEqual(result["reasoning"], text_response)

    @patch("llm_as_a_judge.core.judge_client.genai")
    def test_evaluate_techniques_success(self, mock_genai):
        """Test l'évaluation réussie"""
        # Mock de la réponse du modèle
        mock_response = Mock()
        mock_response.text = '{"winner": "rag", "rag_score": 0.8, "icl_score": 0.6}'

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = JudgeClient(self.api_key, self.config)

        result = client.evaluate_techniques(
            original_chunk="Test CTI content",
            rag_output=["T1001", "T1002"],
            icl_output=["T1001", "T1003"],
            chunk_id="test_001",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["chunk_id"], "test_001")
        self.assertEqual(result["evaluation"]["winner"], "rag")

    @patch("llm_as_a_judge.core.judge_client.genai")
    def test_evaluate_techniques_empty_chunk(self, mock_genai):
        """Test avec un chunk vide"""
        client = JudgeClient(self.api_key, self.config)

        result = client.evaluate_techniques(
            original_chunk="",
            rag_output=["T1001"],
            icl_output=["T1002"],
            chunk_id="test_002",
        )

        self.assertFalse(result["success"])
        self.assertIn("Empty original chunk", result["error"])


if __name__ == "__main__":
    unittest.main()
