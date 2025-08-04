"""
Tests unitaires pour le ValidationClient
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

    @patch("llm_as_a_judge.core.validation_client.genai")
    def test_validation_client_initialization(self, mock_genai):
        """Test l'initialisation du ValidationClient"""
        mock_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_model

        client = JudgeClient(self.api_key, self.config)

        mock_genai.configure.assert_called_once_with(api_key=self.api_key)
        mock_genai.GenerativeModel.assert_called_once_with("gemini-pro")
        self.assertEqual(client.config, self.config)
        self.assertEqual(client.model, mock_model)

    def test_clean_techniques(self):
        """Test le nettoyage des techniques"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            # Test avec des techniques valides et invalides
            mixed_techniques = [
                "T1001",
                "t1002.001",
                "",
                "INVALID",
                "T1003",
                None,
                "123",
            ]
            result = client._clean_techniques(mixed_techniques)
            expected = ["T1001", "T1002.001", "T1003"]
            self.assertEqual(result, expected)

            # Test avec input non-liste
            result = client._clean_techniques("not_a_list")
            self.assertEqual(result, [])

            # Test avec liste vide
            result = client._clean_techniques([])
            self.assertEqual(result, [])

    def test_parse_judge_response_json(self):
        """Test le parsing des réponses JSON"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            json_response = """{"validated_techniques": ["T1001", "T1002"], "rejected_techniques": ["T1003"]}"""
            result = client._parse_judge_response(json_response)

            expected = {
                "validated_techniques": ["T1001", "T1002"],
                "rejected_techniques": ["T1003"],
            }
            self.assertEqual(
                result["validated_techniques"], expected["validated_techniques"]
            )
            self.assertEqual(
                result["rejected_techniques"], expected["rejected_techniques"]
            )

    def test_parse_judge_response_text(self):
        """Test le parsing des réponses texte"""
        with patch("llm_as_a_judge.core.judge_client.genai"):
            client = JudgeClient(self.api_key, self.config)

            text_response = (
                "After analysis, T1001 and T1002 are validated based on evidence."
            )
            result = client._parse_judge_response(text_response)

            # Doit extraire les techniques du texte
            self.assertIn("T1001", result["validated_techniques"])
            self.assertIn("T1002", result["validated_techniques"])
            self.assertEqual(result["reasoning"], text_response)

    @patch("llm_as_a_judge.core.judge_client.genai")
    def test_validate_techniques_success(self, mock_genai):
        """Test la validation réussie"""
        # Mock de la réponse du modèle
        mock_response = Mock()
        mock_response.text = """{"validated_techniques": ["T1001", "T1059.001"], "rejected_techniques": ["T1002"]}"""

        mock_model = Mock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        client = JudgeClient(self.api_key, self.config)

        result = client.validate_techniques_cross_reference(
            original_chunk="Test CTI content with PowerShell usage",
            rag_techniques=["T1001", "T1059.001"],
            llm_techniques=["T1001", "T1002"],
            chunk_id="test_001",
            iocs="powershell.exe",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["chunk_id"], "test_001")
        self.assertIn("T1001", result["final_validated_techniques"])
        self.assertIn("T1059.001", result["final_validated_techniques"])

        # Vérification de l'analyse des inputs
        input_analysis = result["input_analysis"]
        self.assertEqual(input_analysis["common_techniques"], ["T1001"])
        self.assertEqual(input_analysis["rag_only_techniques"], ["T1059.001"])
        self.assertEqual(input_analysis["llm_only_techniques"], ["T1002"])

    @patch("llm_as_a_judge.core.judge_client.genai")
    def test_validate_techniques_empty_chunk(self, mock_genai):
        """Test avec un chunk vide"""
        client = JudgeClient(self.api_key, self.config)

        result = client.validate_techniques_cross_reference(
            original_chunk="",
            rag_techniques=["T1001"],
            llm_techniques=["T1002"],
            chunk_id="test_002",
        )

        self.assertFalse(result["success"])
        self.assertIn("Empty original chunk", result["error"])


if __name__ == "__main__":
    unittest.main()
