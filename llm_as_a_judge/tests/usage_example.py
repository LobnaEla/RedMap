"""
Exemple d'utilisation du module de llm-as-a-judge pour la validation de techniques CTI
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append("/opt/project/cti_pipeline")
from core import TechniqueValidator
from utils import save_judge_results, TechniqueAnalysis

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)
api_key = os.getenv("GEMINI_API_KEY")


def example_single_validation():
    """Exemple de validation d'un seul chunk"""

    # Configuration
    validator = TechniqueValidator(api_key=api_key)

    # Données d'exemple
    chunk_data = {
        "chunk_id": "1",
        "text": "The malware uses PowerShell scripts to download additional payloads from remote servers. It establishes persistence through scheduled tasks and modifies registry entries to maintain access.",
        "iocs": "powershell.exe, schtasks.exe, reg.exe",
        "source_file": "example_report.pdf",
    }

    # Résultats simulés des deux approches
    rag_results = ["T1059.001", "T1105", "T1053.005"]  # RAG/RAS
    llm_results = ["T1059.001", "T1053.005", "T1547.001"]  # Premier LLM

    # Analyse préliminaire
    analysis = TechniqueAnalysis(rag_results, llm_results)
    print("=== PRELIMINARY ANALYSIS ===")
    print(f"RAG techniques: {rag_results}")
    print(f"LLM techniques: {llm_results}")
    print(f"Common techniques: {analysis.common}")
    print(f"RAG-only: {analysis.rag_only}")
    print(f"LLM-only: {analysis.llm_only}")

    overlap_stats = analysis.get_overlap_stats()
    print(f"Overlap: {overlap_stats['overlap_percentage']:.1f}%")

    # Validation croisée
    result = validator.validate_single_chunk(
        chunk_data=chunk_data, rag_results=rag_results, llm_results=llm_results
    )

    print("\n=== LLM-as-a-judge RESULTS ===")
    print(f"Chunk ID: {result.get('chunk_id')}")
    print(f"Success: {result.get('success')}")

    if result.get("success"):
        final_techniques = result.get("final_validated_techniques", [])
        print(f"Final validated techniques: {final_techniques}")

        judge_result = result.get("judge_result", {})
        if "technique_analysis" in judge_result:
            print("\n--- TECHNIQUE ANALYSIS ---")
            for tech_id, analysis in judge_result["technique_analysis"].items():
                status = analysis.get("status", "unknown")
                confidence = analysis.get("confidence", 0)
                source = analysis.get("source", "unknown")
                print(
                    f"{tech_id}: {status} (confidence: {confidence:.2f}, source: {source})"
                )

    return result


def example_batch_validation():
    """Exemple de validation en batch"""

    api_key = os.getenv("GEMINI_API_KEY")
    validator = TechniqueValidator(api_key=api_key)

    # Données d'exemple multiples
    chunks = [
        {
            "chunk_id": "batch_001",
            "text": "The attacker used RDP to move laterally across the network after obtaining valid credentials through credential dumping.",
            "iocs": "mstsc.exe, 3389/tcp, lsadump",
        },
        {
            "chunk_id": "batch_002",
            "text": "Sensitive data was collected from file shares and compressed using WinRAR before being exfiltrated to cloud storage services.",
            "iocs": "winrar.exe, *.rar files, network uploads",
        },
    ]

    # Résultats simulés
    rag_results_list = [
        ["T1021.001", "T1078", "T1003"],  # RDP, Valid Accounts, Credential Dumping
        [
            "T1005",
            "T1560.001",
            "T1567.002",
        ],  # Data from Local System, Archive via Utility, Exfiltration to Cloud
    ]

    llm_results_list = [
        ["T1021.001", "T1078", "T1090"],  # RDP, Valid Accounts, Proxy
        ["T1560.001", "T1567.002", "T1041"],  # Archive, Cloud Exfiltration, C2
    ]

    # Validation batch
    results = validator.batch_validate(
        chunks=chunks,
        rag_results_list=rag_results_list,
        llm_results_list=llm_results_list,
    )

    print("\n=== LLM-as-a-judge RESULTS ===")
    stats = results["statistics"]
    print(f"Total chunks: {stats['total_chunks']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Total techniques analyzed: {stats['total_techniques_analyzed']}")
    print(f"Total techniques validated: {stats['total_techniques_validated']}")
    print(f"Average validation rate: {stats['average_validation_rate']:.2%}")

    # Techniques finales extraites
    final_techniques = validator.extract_final_techniques(results)
    print(f"\n--- FINAL TECHNIQUES ---")
    for chunk_id, techniques in final_techniques.items():
        print(f"{chunk_id}: {techniques}")

    return results


def example_advanced_analysis():
    """Exemple d'analyse avancée des résultats"""

    # Supposons qu'on ait des résultats de validation
    from utils.validation_utils import calculate_validation_metrics

    # Données d'exemple de résultats de validation
    mock_validations = [
        {
            "success": True,
            "chunk_id": "001",
            "input_analysis": {
                "total_unique_techniques": 4,
                "common_techniques": ["T1059.001", "T1053.005"],
                "rag_only_techniques": ["T1105"],
                "llm_only_techniques": ["T1547.001"],
            },
            "final_validated_techniques": ["T1059.001", "T1053.005", "T1105"],
        },
        {
            "success": True,
            "chunk_id": "002",
            "input_analysis": {
                "total_unique_techniques": 5,
                "common_techniques": ["T1021.001"],
                "rag_only_techniques": ["T1078", "T1003"],
                "llm_only_techniques": ["T1090", "T1110"],
            },
            "final_validated_techniques": ["T1021.001", "T1078"],
        },
    ]

    metrics = calculate_validation_metrics(mock_validations)

    print("\n=== ADVANCED ANALYSIS ===")
    if "error" not in metrics:
        overall = metrics["overall_metrics"]
        source_analysis = metrics["source_analysis"]
        insights = metrics["insights"]

        print(f"Overall validation rate: {overall['overall_validation_rate']:.2%}")
        print(f"Consensus accuracy: {overall['consensus_accuracy']:.2%}")

        print(
            f"\nCommon techniques validation: {source_analysis['common_techniques']['validation_rate']:.2%}"
        )
        print(
            f"RAG-only validation: {source_analysis['rag_only_techniques']['validation_rate']:.2%}"
        )
        print(
            f"LLM-only validation: {source_analysis['llm_only_techniques']['validation_rate']:.2%}"
        )

        print(f"\nConsensus reliability: {insights['consensus_reliability']}")
        print(f"RAG contribution: {insights['rag_contribution']}")
        print(f"LLM contribution: {insights['llm_contribution']}")


if __name__ == "__main__":
    print("=== LLM-as-a-Judge Validation Examples ===\n")

    # Exemple de validation unique
    single_result = example_single_validation()

    # Exemple de validation batch
    batch_results = example_batch_validation()

    # Analyse avancée
    example_advanced_analysis()

    # Sauvegarde des résultats
    if batch_results:
        output_file = save_judge_results(batch_results)
        print(f"\nResults saved to: {output_file}")
