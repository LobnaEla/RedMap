"""
Exemple d'utilisation du module LLM-as-a-Judge
"""

import os
import sys

sys.path.append("/opt/project/cti_pipeline")

from llm_as_a_judge import TechniqueEvaluator, save_evaluation_results


def example_single_evaluation():
    """Exemple d'évaluation d'un seul chunk"""

    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    evaluator = TechniqueEvaluator(api_key=api_key)

    # Données d'exemple
    chunk_data = {
        "chunk_id": "example_001",
        "text": "The malware uses PowerShell scripts to download additional payloads from remote servers and establishes persistence through scheduled tasks.",
        "iocs": "powershell.exe, schtasks.exe",
        "source_file": "example_report.pdf",
    }

    # Résultats simulés
    rag_results = ["T1059.001", "T1105", "T1053.005"]  # Résultats du RAG
    icl_results = ["T1059.001", "T1053.005", "T1547.001"]  # Résultats de l'ICL

    # Évaluation
    result = evaluator.evaluate_single_chunk(
        chunk_data=chunk_data, rag_results=rag_results, icl_results=icl_results
    )

    print("=== SINGLE CHUNK EVALUATION ===")
    print(f"Chunk ID: {result.get('chunk_id')}")
    print(f"Success: {result.get('success')}")

    if result.get("success"):
        evaluation = result.get("evaluation", {})
        print(f"Winner: {evaluation.get('winner')}")
        print(f"RAG Score: {evaluation.get('rag_score', 0):.3f}")
        print(f"ICL Score: {evaluation.get('icl_score', 0):.3f}")
        print(f"Reasoning: {evaluation.get('reasoning', '')[:200]}...")

    return result


def example_batch_evaluation():
    """Exemple d'évaluation en batch"""

    api_key = os.getenv("GEMINI_API_KEY")
    evaluator = TechniqueEvaluator(api_key=api_key)

    # Données d'exemple multiples
    chunks = [
        {
            "chunk_id": "batch_001",
            "text": "The attacker used RDP to move laterally across the network after obtaining credentials.",
            "iocs": "mstsc.exe, 3389/tcp",
        },
        {
            "chunk_id": "batch_002",
            "text": "Data was exfiltrated using cloud storage services after being compressed with WinRAR.",
            "iocs": "winrar.exe, upload.exe",
        },
    ]

    rag_results_list = [["T1021.001", "T1078"], ["T1567.002", "T1560.001"]]

    icl_results_list = [
        ["T1021.001", "T1078", "T1090"],
        ["T1567.002", "T1560.001", "T1041"],
    ]

    # Évaluation batch
    results = evaluator.batch_evaluate(
        chunks=chunks,
        rag_results_list=rag_results_list,
        icl_results_list=icl_results_list,
    )

    print("\n=== BATCH EVALUATION ===")
    stats = results["statistics"]
    print(f"Total: {stats['total_chunks']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"RAG wins: {stats['rag_wins']}")
    print(f"ICL wins: {stats['icl_wins']}")
    print(f"Ties: {stats['ties']}")

    return results


if __name__ == "__main__":
    # Exemple d'évaluation unique
    single_result = example_single_evaluation()

    # Exemple d'évaluation batch
    batch_results = example_batch_evaluation()

    # Sauvegarde des résultats
    output_file = save_evaluation_results(batch_results)
    print(f"\nResults saved to: {output_file}")
