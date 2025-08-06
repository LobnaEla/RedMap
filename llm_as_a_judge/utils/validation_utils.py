from typing import Dict, List, Any
from collections import defaultdict, Counter


def calculate_validation_metrics(validations: List[Dict]) -> Dict[str, Any]:
    """Calculate comprehensive validation metrics from judge results."""

    if not validations:
        return {"error": "No validations provided"}

    try:
        # Filter successful validations
        successful = [v for v in validations if v.get("success", False)]

        if not successful:
            return {"error": "No successful validations found"}

        # Overall metrics
        total_chunks = len(validations)
        successful_chunks = len(successful)
        success_rate = successful_chunks / total_chunks

        # Technique analysis
        total_analyzed = 0
        total_validated = 0

        # Source analysis
        source_stats = defaultdict(lambda: {"total": 0, "validated": 0})

        # Consensus analysis
        consensus_matches = []
        validation_rates = []

        for validation in successful:
            input_analysis = validation.get("input_analysis", {})
            final_techniques = set(validation.get("final_validated_techniques", []))

            # Overall counts
            unique_techniques = input_analysis.get("total_unique_techniques", 0)
            validated_count = len(final_techniques)

            total_analyzed += unique_techniques
            total_validated += validated_count

            if unique_techniques > 0:
                validation_rates.append(validated_count / unique_techniques)

            # Source-specific analysis
            common = set(input_analysis.get("common_techniques", []))
            llm_only = set(input_analysis.get("llm_only_techniques", []))
            ras_only = set(input_analysis.get("ras_only_techniques", []))

            # Common techniques (consensus)
            source_stats["common"]["total"] += len(common)
            source_stats["common"]["validated"] += len(
                common.intersection(final_techniques)
            )

            # LLM-only techniques
            source_stats["llm_only"]["total"] += len(llm_only)
            source_stats["llm_only"]["validated"] += len(
                llm_only.intersection(final_techniques)
            )

            # RAS-only techniques
            source_stats["ras_only"]["total"] += len(ras_only)
            source_stats["ras_only"]["validated"] += len(
                ras_only.intersection(final_techniques)
            )

            # Consensus accuracy for this chunk
            if common:
                consensus_matches.append(
                    len(common.intersection(final_techniques)) / len(common)
                )

        # Calculate final metrics
        overall_validation_rate = (
            total_validated / total_analyzed if total_analyzed > 0 else 0.0
        )
        avg_validation_rate = (
            sum(validation_rates) / len(validation_rates) if validation_rates else 0.0
        )
        consensus_accuracy = (
            sum(consensus_matches) / len(consensus_matches)
            if consensus_matches
            else 0.0
        )

        # Source-specific validation rates
        source_analysis = {}
        for source, stats in source_stats.items():
            rate = stats["validated"] / stats["total"] if stats["total"] > 0 else 0.0
            source_analysis[source] = {
                "total": stats["total"],
                "validated": stats["validated"],
                "validation_rate": rate,
            }

        # Insights
        insights = _generate_validation_insights(
            source_analysis, consensus_accuracy, avg_validation_rate
        )

        return {
            "overall_metrics": {
                "total_chunks": total_chunks,
                "successful_chunks": successful_chunks,
                "success_rate": success_rate,
                "total_techniques_analyzed": total_analyzed,
                "total_techniques_validated": total_validated,
                "overall_validation_rate": overall_validation_rate,
                "average_validation_rate": avg_validation_rate,
                "consensus_accuracy": consensus_accuracy,
            },
            "source_analysis": source_analysis,
            "insights": insights,
            "validation_rates_distribution": {
                "min": min(validation_rates) if validation_rates else 0.0,
                "max": max(validation_rates) if validation_rates else 0.0,
                "avg": avg_validation_rate,
                "count": len(validation_rates),
            },
        }

    except Exception as e:
        return {"error": f"Error calculating metrics: {str(e)}"}


def _generate_validation_insights(
    source_analysis: Dict, consensus_accuracy: float, avg_validation_rate: float
) -> Dict[str, str]:
    """Generate insights from validation metrics."""

    insights = {}

    # Consensus reliability
    if consensus_accuracy >= 0.8:
        insights["consensus_reliability"] = (
            "High - Strong agreement between RAG and LLM"
        )
    elif consensus_accuracy >= 0.6:
        insights["consensus_reliability"] = "Medium - Moderate agreement"
    else:
        insights["consensus_reliability"] = (
            "Low - Significant disagreement between systems"
        )

    # RAG contribution
    ras_rate = source_analysis.get("ras_only", {}).get("validation_rate", 0.0)
    if ras_rate >= 0.7:
        insights["rag_contribution"] = "High - RAG provides valuable unique techniques"
    elif ras_rate >= 0.4:
        insights["rag_contribution"] = "Medium - RAG adds some value"
    else:
        insights["rag_contribution"] = "Low - RAG unique techniques often invalid"

    # LLM contribution
    llm_rate = source_analysis.get("llm_only", {}).get("validation_rate", 0.0)
    if llm_rate >= 0.7:
        insights["llm_contribution"] = "High - LLM identifies techniques RAG misses"
    elif llm_rate >= 0.4:
        insights["llm_contribution"] = "Medium - LLM provides some unique value"
    else:
        insights["llm_contribution"] = "Low - LLM prone to hallucination"

    # Overall system performance
    if avg_validation_rate >= 0.8:
        insights["system_performance"] = "Excellent - High precision validation"
    elif avg_validation_rate >= 0.6:
        insights["system_performance"] = "Good - Reasonable validation accuracy"
    else:
        insights["system_performance"] = "Poor - Many techniques rejected by judge"

    return insights


def analyze_technique_patterns(validations: List[Dict]) -> Dict[str, Any]:
    """Analyze patterns in validated/rejected techniques."""

    validated_counter = Counter()
    rejected_counter = Counter()
    confidence_scores = []

    for validation in validations:
        if not validation.get("success", False):
            continue

        judge_result = validation.get("judge_result", {})

        # Count validated/rejected
        validated = judge_result.get("validated_techniques", [])
        rejected = judge_result.get("rejected_techniques", [])

        validated_counter.update(validated)
        rejected_counter.update(rejected)

        # Collect confidence scores
        analysis = judge_result.get("technique_analysis", {})
        for tech_id, details in analysis.items():
            conf = details.get("confidence", 0.0)
            if isinstance(conf, (int, float)):
                confidence_scores.append(conf)

    return {
        "most_validated_techniques": validated_counter.most_common(10),
        "most_rejected_techniques": rejected_counter.most_common(10),
        "confidence_distribution": {
            "min": min(confidence_scores) if confidence_scores else 0.0,
            "max": max(confidence_scores) if confidence_scores else 0.0,
            "avg": (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores
                else 0.0
            ),
            "count": len(confidence_scores),
        },
        "total_unique_validated": len(validated_counter),
        "total_unique_rejected": len(rejected_counter),
    }


def compare_rag_llm_performance(validations: List[Dict]) -> Dict[str, Any]:
    """Compare RAG vs LLM performance in detail."""

    rag_stats = {"proposed": 0, "validated": 0, "unique_contribution": 0}
    llm_stats = {"proposed": 0, "validated": 0, "unique_contribution": 0}
    agreement_stats = {"proposed": 0, "validated": 0}

    for validation in validations:
        if not validation.get("success", False):
            continue

        input_analysis = validation.get("input_analysis", {})
        final_techniques = set(validation.get("final_validated_techniques", []))

        # Get technique sets
        common = set(input_analysis.get("common_techniques", []))
        llm_only = set(input_analysis.get("llm_only_techniques", []))
        ras_only = set(input_analysis.get("ras_only_techniques", []))

        # Agreement (common) stats
        agreement_stats["proposed"] += len(common)
        agreement_stats["validated"] += len(common.intersection(final_techniques))

        # RAG performance (including common + ras_only)
        rag_total = common | ras_only
        rag_stats["proposed"] += len(rag_total)
        rag_stats["validated"] += len(rag_total.intersection(final_techniques))
        rag_stats["unique_contribution"] += len(ras_only.intersection(final_techniques))

        # LLM performance (including common + llm_only)
        llm_total = common | llm_only
        llm_stats["proposed"] += len(llm_total)
        llm_stats["validated"] += len(llm_total.intersection(final_techniques))
        llm_stats["unique_contribution"] += len(llm_only.intersection(final_techniques))

    # Calculate rates
    def calc_rate(validated, proposed):
        return validated / proposed if proposed > 0 else 0.0

    return {
        "rag_performance": {
            **rag_stats,
            "validation_rate": calc_rate(rag_stats["validated"], rag_stats["proposed"]),
            "unique_contribution_rate": calc_rate(
                rag_stats["unique_contribution"], rag_stats["proposed"]
            ),
        },
        "llm_performance": {
            **llm_stats,
            "validation_rate": calc_rate(llm_stats["validated"], llm_stats["proposed"]),
            "unique_contribution_rate": calc_rate(
                llm_stats["unique_contribution"], llm_stats["proposed"]
            ),
        },
        "agreement_performance": {
            **agreement_stats,
            "validation_rate": calc_rate(
                agreement_stats["validated"], agreement_stats["proposed"]
            ),
        },
    }
