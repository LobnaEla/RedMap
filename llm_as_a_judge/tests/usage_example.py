"""
Exemple d'utilisation du module de llm-as-a-judge pour la validation de techniques CTI
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.append("/opt/project/cti_pipeline")
from llm_as_a_judge import TechniqueValidator, save_judge_results, TechniqueAnalysis

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


def example_advanced_analysis(validation_results=None):
    """Exemple d'analyse avancée des résultats obtenus du judge LLM"""

    if validation_results is None:
        print("No validation results provided. Running batch validation first...")
        # Si aucun résultat n'est fourni, on fait une validation pour obtenir de vrais résultats
        validation_results = example_batch_validation()

    from llm_as_a_judge.utils.validation_utils import calculate_validation_metrics

    # Extraire les résultats de validation du batch
    if "validations" in validation_results:
        actual_validations = validation_results["validations"]
        print(f"\n=== ANALYZING LLM JUDGE RESULTS ===")
        print(f"Number of validation results: {len(actual_validations)}")

        # Afficher les techniques finales validées par le judge LLM
        print(f"\n--- FINAL TECHNIQUES FROM JUDGE LLM ---")
        for validation in actual_validations:
            chunk_id = validation.get("chunk_id", "unknown")
            final_techniques = validation.get("final_validated_techniques", [])
            success = validation.get("success", False)
            print(
                f"{chunk_id}: {'SUCCESS' if success else 'FAILED'} - {final_techniques}"
            )

            # Afficher le détail de l'analyse du judge si disponible
            judge_result = validation.get("judge_result", {})
            if "reasoning" in judge_result:
                print(f"  Judge reasoning: {judge_result['reasoning'][:100]}...")

        metrics = calculate_validation_metrics(actual_validations)
    else:
        print(
            "ERROR: No validations found in results. Cannot perform advanced analysis."
        )
        return

    print(f"\n=== ADVANCED ANALYSIS OF JUDGE RESULTS ===")
    if "error" not in metrics:
        overall = metrics["overall_metrics"]
        source_analysis = metrics["source_analysis"]
        insights = metrics["insights"]

        print(
            f"Overall validation rate by Judge LLM: {overall['overall_validation_rate']:.2%}"
        )
        print(
            f"Consensus accuracy (Judge agrees with both RAG+LLM): {overall['consensus_accuracy']:.2%}"
        )

        print(f"\nTechnique Source Analysis:")
        print(
            f"  Common techniques validation: {source_analysis['common_techniques']['validation_rate']:.2%}"
        )
        print(
            f"  RAG-only validation: {source_analysis['rag_only_techniques']['validation_rate']:.2%}"
        )
        print(
            f"  LLM-only validation: {source_analysis['llm_only_techniques']['validation_rate']:.2%}"
        )

        print(f"\nJudge Insights:")
        print(f"  Consensus reliability: {insights['consensus_reliability']}")
        print(f"  RAG contribution: {insights['rag_contribution']}")
        print(f"  LLM contribution: {insights['llm_contribution']}")

        # Afficher les statistiques sur la performance du judge
        print(f"\n--- JUDGE PERFORMANCE STATS ---")
        total_input_techniques = sum(
            v.get("input_analysis", {}).get("total_unique_techniques", 0)
            for v in actual_validations
            if v.get("success")
        )
        total_validated = sum(
            len(v.get("final_validated_techniques", []))
            for v in actual_validations
            if v.get("success")
        )

        if total_input_techniques > 0:
            validation_rate = (total_validated / total_input_techniques) * 100
            print(
                f"Judge validation rate: {validation_rate:.1f}% ({total_validated}/{total_input_techniques})"
            )
    else:
        print(f"Error in metrics calculation: {metrics['error']}")

    return metrics


if __name__ == "__main__":
    print("=== LLM-as-a-Judge Validation Examples ===\n")

    # Exemple de validation unique
    print("1. Running single validation example...")
    single_result = example_single_validation()

    # Exemple de validation batch
    print("\n2. Running batch validation example...")
    batch_results = example_batch_validation()

    # Analyse avancée avec les vrais résultats du judge LLM
    print("\n3. Running advanced analysis on actual judge results...")
    example_advanced_analysis(batch_results)

    # Sauvegarde des résultats
    if batch_results:
        output_file = save_judge_results(batch_results)
        print(f"\nResults saved to: {output_file}")
