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

            # Add chunk metadata
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
        """Validate batch of chunks - FIXED calculations."""

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
            "rag_only_contribution": 0.0,
            "llm_only_contribution": 0.0,
            "errors": 0,
            "start_time": datetime.now().isoformat(),
        }

        # Collect metrics for averaging
        validation_rates = []
        consensus_scores = []
        rag_contributions = []
        llm_contributions = []

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
                self._update_batch_stats(
                    validation,
                    stats,
                    validation_rates,
                    consensus_scores,
                    rag_contributions,
                    llm_contributions,
                )
            else:
                stats["errors"] += 1

        # Calculate final averages - FIXED
        self._finalize_batch_stats(
            stats,
            validation_rates,
            consensus_scores,
            rag_contributions,
            llm_contributions,
        )

        return {
            "validations": validations,
            "statistics": stats,
            "metadata": {
                "validation_config": VALIDATION_CONFIG,
                "generated_at": stats["end_time"],
                "total_processed": len(chunks),
            },
        }

    def _update_batch_stats(
        self,
        validation,
        stats,
        validation_rates,
        consensus_scores,
        rag_contributions,
        llm_contributions,
    ):
        """Update statistics for single validation - FIXED."""
        input_analysis = validation.get("input_analysis", {})
        validated_techniques = set(validation.get("final_validated_techniques", []))

        # Total techniques
        total_analyzed = input_analysis.get("total_unique_techniques", 0)
        validated_count = len(validated_techniques)

        stats["total_techniques_analyzed"] += total_analyzed
        stats["total_techniques_validated"] += validated_count

        if total_analyzed > 0:
            validation_rates.append(validated_count / total_analyzed)

        # Consensus accuracy (common techniques validated)
        common_techniques = set(input_analysis.get("common_techniques", []))
        if common_techniques:
            consensus_validated = len(
                common_techniques.intersection(validated_techniques)
            )
            consensus_scores.append(consensus_validated / len(common_techniques))

        # RAG contribution (ras_only techniques validated)
        ras_only = set(input_analysis.get("ras_only_techniques", []))
        if ras_only:
            ras_validated = len(ras_only.intersection(validated_techniques))
            rag_contributions.append(ras_validated / len(ras_only))

        # LLM contribution (llm_only techniques validated)
        llm_only = set(input_analysis.get("llm_only_techniques", []))
        if llm_only:
            llm_validated = len(llm_only.intersection(validated_techniques))
            llm_contributions.append(llm_validated / len(llm_only))

    def _finalize_batch_stats(
        self,
        stats,
        validation_rates,
        consensus_scores,
        rag_contributions,
        llm_contributions,
    ):
        """Finalize batch statistics - FIXED."""
        stats["average_validation_rate"] = (
            sum(validation_rates) / len(validation_rates) if validation_rates else 0.0
        )
        stats["consensus_accuracy"] = (
            sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0.0
        )
        stats["rag_only_contribution"] = (
            sum(rag_contributions) / len(rag_contributions)
            if rag_contributions
            else 0.0
        )
        stats["llm_only_contribution"] = (
            sum(llm_contributions) / len(llm_contributions)
            if llm_contributions
            else 0.0
        )

        stats["end_time"] = datetime.now().isoformat()
        stats["success_rate"] = stats["successful_validations"] / stats["total_chunks"]

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
