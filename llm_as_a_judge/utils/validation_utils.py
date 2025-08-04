from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class TechniqueAnalysis:
    """Classe pour analyser les techniques proposées"""

    def __init__(self, rag_techniques: List[str], llm_techniques: List[str]):
        self.rag_techniques = set(rag_techniques)
        self.llm_techniques = set(llm_techniques)

        # Calculs automatiques
        self.common = list(self.rag_techniques.intersection(self.llm_techniques))
        self.rag_only = list(self.rag_techniques - self.llm_techniques)
        self.llm_only = list(self.llm_techniques - self.rag_techniques)
        self.all_unique = list(self.rag_techniques.union(self.llm_techniques))

    def get_overlap_stats(self) -> Dict:
        """Statistiques de chevauchement"""
        total_unique = len(self.all_unique)
        common_count = len(self.common)

        return {
            "total_unique_techniques": total_unique,
            "common_techniques_count": common_count,
            "rag_only_count": len(self.rag_only),
            "llm_only_count": len(self.llm_only),
            "overlap_percentage": (
                (common_count / total_unique * 100) if total_unique > 0 else 0
            ),
            "rag_coverage": (
                (len(self.rag_techniques) / total_unique * 100)
                if total_unique > 0
                else 0
            ),
            "llm_coverage": (
                (len(self.llm_techniques) / total_unique * 100)
                if total_unique > 0
                else 0
            ),
        }

    def analyze_disagreement(self) -> Dict:
        """Analyse les désaccords entre approches"""
        return {
            "disagreement_rate": (
                (len(self.rag_only) + len(self.llm_only)) / len(self.all_unique)
                if self.all_unique
                else 0
            ),
            "rag_unique_contribution": len(self.rag_only),
            "llm_unique_contribution": len(self.llm_only),
            "requires_validation": self.rag_only + self.llm_only,
        }


def calculate_validation_metrics(validation_results: List[Dict]) -> Dict:
    """Calcule les métriques de validation agrégées"""

    successful_validations = [v for v in validation_results if v.get("success", False)]

    if not successful_validations:
        return {"error": "No successful validations to analyze"}

    total_analyzed = 0
    total_validated = 0
    consensus_scores = []
    validation_rates = []

    # Compteurs par source
    common_validated = 0
    common_total = 0
    rag_only_validated = 0
    rag_only_total = 0
    llm_only_validated = 0
    llm_only_total = 0

    for validation in successful_validations:
        input_analysis = validation.get("input_analysis", {})
        validated_techniques = set(validation.get("final_validated_techniques", []))

        # Statistiques générales
        unique_count = input_analysis.get("total_unique_techniques", 0)
        validated_count = len(validated_techniques)

        total_analyzed += unique_count
        total_validated += validated_count

        if unique_count > 0:
            validation_rates.append(validated_count / unique_count)

        # Analyse par source
        common_techs = set(input_analysis.get("common_techniques", []))
        rag_only_techs = set(input_analysis.get("rag_only_techniques", []))
        llm_only_techs = set(input_analysis.get("llm_only_techniques", []))

        common_total += len(common_techs)
        common_validated += len(common_techs.intersection(validated_techniques))

        rag_only_total += len(rag_only_techs)
        rag_only_validated += len(rag_only_techs.intersection(validated_techniques))

        llm_only_total += len(llm_only_techs)
        llm_only_validated += len(llm_only_techs.intersection(validated_techniques))

        # Score de consensus
        if common_techs:
            consensus_score = len(
                common_techs.intersection(validated_techniques)
            ) / len(common_techs)
            consensus_scores.append(consensus_score)

    return {
        "overall_metrics": {
            "total_chunks_validated": len(successful_validations),
            "total_techniques_analyzed": total_analyzed,
            "total_techniques_validated": total_validated,
            "overall_validation_rate": (
                (total_validated / total_analyzed) if total_analyzed > 0 else 0
            ),
            "average_validation_rate": (
                sum(validation_rates) / len(validation_rates) if validation_rates else 0
            ),
            "consensus_accuracy": (
                sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0
            ),
        },
        "source_analysis": {
            "common_techniques": {
                "total": common_total,
                "validated": common_validated,
                "validation_rate": (
                    (common_validated / common_total) if common_total > 0 else 0
                ),
            },
            "rag_only_techniques": {
                "total": rag_only_total,
                "validated": rag_only_validated,
                "validation_rate": (
                    (rag_only_validated / rag_only_total) if rag_only_total > 0 else 0
                ),
            },
            "llm_only_techniques": {
                "total": llm_only_total,
                "validated": llm_only_validated,
                "validation_rate": (
                    (llm_only_validated / llm_only_total) if llm_only_total > 0 else 0
                ),
            },
        },
        "insights": {
            "consensus_reliability": (
                "High"
                if (common_validated / common_total if common_total > 0 else 0) > 0.8
                else (
                    "Medium"
                    if (common_validated / common_total if common_total > 0 else 0)
                    > 0.6
                    else "Low"
                )
            ),
            "rag_contribution": (
                "Significant"
                if (rag_only_validated / rag_only_total if rag_only_total > 0 else 0)
                > 0.5
                else (
                    "Moderate"
                    if (
                        rag_only_validated / rag_only_total if rag_only_total > 0 else 0
                    )
                    > 0.3
                    else "Limited"
                )
            ),
            "llm_contribution": (
                "Significant"
                if (llm_only_validated / llm_only_total if llm_only_total > 0 else 0)
                > 0.5
                else (
                    "Moderate"
                    if (
                        llm_only_validated / llm_only_total if llm_only_total > 0 else 0
                    )
                    > 0.3
                    else "Limited"
                )
            ),
        },
    }
