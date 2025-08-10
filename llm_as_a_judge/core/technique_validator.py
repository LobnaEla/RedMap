import os
import json
from datetime import datetime
from typing import Dict, List

from .judge_client import JudgeClient
from .config import VALIDATION_CONFIG


class TechniqueValidator:
    """Main validator for LLM-as-a-Judge cross-validation system."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not configured. Set in environment or pass as argument."
            )

        self.judge_client = JudgeClient(
            api_key=self.api_key, model_config=VALIDATION_CONFIG
        )

    def validate_single_chunk(
        self, chunk_data: Dict, rag_results: List[str], llm_results: List[str]
    ) -> Dict:
        """Validate single chunk by cross-referencing RAG and LLM results."""

        chunk_id = chunk_data.get("chunk_id", "unknown")
        original_text = chunk_data.get("text", "")
        iocs = chunk_data.get("iocs", "")

        if not original_text.strip():
            return self._create_error_result(chunk_id, "Empty chunk text")

        try:
            validation_result = self.judge_client.validate_llm_predictions(
                original_chunk=original_text,
                llm_predicted_techniques=llm_results,
                ras_evidence_techniques=rag_results,
                chunk_id=chunk_id,
                iocs=iocs,
            )

            return validation_result

        except Exception as e:
            return self._create_error_result(chunk_id, f"Validation error: {str(e)}")

    def batch_validate(
        self,
        chunks: List[Dict],
        rag_results_list: List[List[str]],
        llm_results_list: List[List[str]],
    ) -> Dict:
        """Validate batch of chunks - simplified without stats."""

        if not (len(chunks) == len(rag_results_list) == len(llm_results_list)):
            raise ValueError("Length mismatch between inputs")

        validations = []
        
        for i, (chunk, rag_results, llm_results) in enumerate(
            zip(chunks, rag_results_list, llm_results_list)
        ):
            print(
                f"🟡 Validating chunk {i+1}/{len(chunks)} - ID: {chunk.get('chunk_id', 'N/A')}"
            )

            validation = self.validate_single_chunk(chunk, rag_results, llm_results)
            validations.append(validation)

        return {
            "validations": validations,
            "metadata": {
                "validation_config": VALIDATION_CONFIG,
                "generated_at": datetime.now().isoformat(),
                "total_processed": len(chunks),
            },
        }

    def extract_final_techniques(self, judge_results: Dict) -> Dict[str, List[str]]:
        """Extract final validated techniques for each chunk."""
        return {
            validation["chunk_id"]: validation.get("final_validated_techniques", [])
            for validation in judge_results.get("validations", [])
            if validation.get("success", False)
        }

    def _create_error_result(self, chunk_id: str, error: str) -> Dict:
        """Create standardized error result."""
        return {
            "chunk_id": chunk_id,
            "error": error,
            "success": False,
            "timestamp": datetime.now().isoformat(),
        }
