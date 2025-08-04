"""
Script principal pour exécuter la validation croisée LLM-as-a-Judge
"""

import os
import sys
import json
from typing import List, Dict

# Ajout du chemin pour les imports
sys.path.append("/opt/project/cti_pipeline")

from core.technique_validator import TechniqueValidator
from core.config import PATH_CONFIG
from utils.validation_utils import calculate_validation_metrics, TechniqueAnalysis
from utils.file_utils import save_validation_results, save_final_techniques_only


def load_chunk_data(chunks_dir: str) -> List[Dict]:
    """Charge les données des chunks"""
    import glob

    chunk_files = glob.glob(os.path.join(chunks_dir, "chunks_*.json"))
    chunks = []

    for file_path in chunk_files:
        with open(file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            if isinstance(file_data, list):
                chunks.extend(file_data)
            else:
                chunks.append(file_data)

    return chunks


def load_rag_results(rag_results_dir: str) -> Dict[str, List[str]]:
    """Charge les résultats RAG/RAS"""
    import glob

    rag_results = {}

    # Cherche les fichiers de résultats RAG (format à adapter selon votre implémentation)
    result_files = glob.glob(os.path.join(rag_results_dir, "*.json"))

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Adapter selon le format de vos résultats RAG
                if isinstance(data, dict):
                    chunk_id = data.get("chunk_id") or data.get("id")
                    techniques = data.get("techniques") or data.get(
                        "mitre_techniques", []
                    )
                    if chunk_id:
                        rag_results[chunk_id] = techniques
                elif isinstance(data, list):
                    for item in data:
                        chunk_id = item.get("chunk_id") or item.get("id")
                        techniques = item.get("techniques") or item.get(
                            "mitre_techniques", []
                        )
                        if chunk_id:
                            rag_results[chunk_id] = techniques
        except Exception as e:
            print(f"Error loading RAG result file {file_path}: {e}")
            continue

    return rag_results


def load_llm_results(llm_results_dir: str) -> Dict[str, List[str]]:
    """Charge les résultats du premier LLM (ICL)"""
    import glob

    llm_results = {}
    result_files = glob.glob(os.path.join(llm_results_dir, "*.json"))

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                chunk_id = data.get("chunk_id")
                techniques = data.get("mitre_techniques", [])
                if chunk_id and techniques:
                    llm_results[chunk_id] = techniques
        except Exception as e:
            print(f"Error loading LLM result file {file_path}: {e}")
            continue

    return llm_results


def analyze_input_overlap(rag_results: Dict, llm_results: Dict) -> None:
    """Analyse le chevauchement entre les résultats RAG et LLM"""

    common_chunks = set(rag_results.keys()).intersection(set(llm_results.keys()))
    print(f"\n=== INPUT ANALYSIS ===")
    print(f"RAG results: {len(rag_results)} chunks")
    print(f"LLM results: {len(llm_results)} chunks")
    print(f"Common chunks: {len(common_chunks)} chunks")

    if common_chunks:
        # Analyse de quelques exemples
        sample_chunks = list(common_chunks)[:3]

        for chunk_id in sample_chunks:
            rag_techs = rag_results[chunk_id]
            llm_techs = llm_results[chunk_id]

            analysis = TechniqueAnalysis(rag_techs, llm_techs)
            stats = analysis.get_overlap_stats()

            print(f"\nChunk {chunk_id}:")
            print(f"  RAG: {rag_techs}")
            print(f"  LLM: {llm_techs}")
            print(f"  Common: {analysis.common}")
            print(f"  Overlap: {stats['overlap_percentage']:.1f}%")


def main():
    """Fonction principale"""
    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    # Chemins des données
    chunks_dir = "/opt/project/cti_pipeline/chunks"
    rag_results_dir = "/opt/project/cti_pipeline/rag_results"
    llm_results_dir = "/opt/project/cti_pipeline/llm_results"

    print("Loading data...")

    # Chargement des données
    chunks = load_chunk_data(chunks_dir)
    rag_results = load_rag_results(rag_results_dir)
    llm_results = load_llm_results(llm_results_dir)

    print(f"Loaded {len(chunks)} chunks")
    print(f"RAG results for {len(rag_results)} chunks")
    print(f"LLM results for {len(llm_results)} chunks")

    # Analyse des chevauchements
    analyze_input_overlap(rag_results, llm_results)

    # Préparation des données pour la validation
    validation_data = []
    rag_results_list = []
    llm_results_list = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in rag_results and chunk_id in llm_results:
            validation_data.append(chunk)
            rag_results_list.append(rag_results[chunk_id])
            llm_results_list.append(llm_results[chunk_id])

    print(
        f"\nWill validate {len(validation_data)} chunks with both RAG and LLM results"
    )

    if not validation_data:
        print("No chunks with both RAG and LLM results found")
        sys.exit(1)

    # Initialisation du validateur
    validator = TechniqueValidator(api_key=api_key)

    print("Starting cross-validation...")

    # Validation croisée
    results = validator.batch_validate(
        chunks=validation_data,
        rag_results_list=rag_results_list,
        llm_results_list=llm_results_list,
    )

    # Calcul des métriques de validation
    validation_metrics = calculate_validation_metrics(results["validations"])
    results["validation_metrics"] = validation_metrics

    # Sauvegarde des résultats complets
    full_results_file = save_validation_results(results, include_detailed=True)
    print(f"Detailed results saved to: {full_results_file}")

    # Sauvegarde des techniques finales uniquement
    final_techniques_file = save_final_techniques_only(results)
    print(f"Final validated techniques saved to: {final_techniques_file}")

    # Affichage des résultats principaux
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 60)

    stats = results["statistics"]
    print(f"Total chunks processed: {stats['total_chunks']}")
    print(f"Successful validations: {stats['successful_validations']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Total techniques analyzed: {stats['total_techniques_analyzed']}")
    print(f"Total techniques validated: {stats['total_techniques_validated']}")
    print(f"Overall validation rate: {stats['average_validation_rate']:.2%}")
    print(f"Consensus accuracy: {stats['consensus_accuracy']:.2%}")

    if "validation_metrics" in results:
        metrics = results["validation_metrics"]
        if "error" not in metrics:
            overall = metrics["overall_metrics"]
            source_analysis = metrics["source_analysis"]

            print(f"\n--- TECHNIQUE SOURCE ANALYSIS ---")
            print(f"Common techniques (both approaches):")
            print(f"  Total: {source_analysis['common_techniques']['total']}")
            print(f"  Validated: {source_analysis['common_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['common_techniques']['validation_rate']:.2%}"
            )

            print(f"\nRAG-only techniques:")
            print(f"  Total: {source_analysis['rag_only_techniques']['total']}")
            print(f"  Validated: {source_analysis['rag_only_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['rag_only_techniques']['validation_rate']:.2%}"
            )

            print(f"\nLLM-only techniques:")
            print(f"  Total: {source_analysis['llm_only_techniques']['total']}")
            print(f"  Validated: {source_analysis['llm_only_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['llm_only_techniques']['validation_rate']:.2%}"
            )

            insights = metrics["insights"]
            print(f"\n--- INSIGHTS ---")
            print(f"Consensus reliability: {insights['consensus_reliability']}")
            print(f"RAG contribution: {insights['rag_contribution']}")
            print(f"LLM contribution: {insights['llm_contribution']}")

    # Extraction des techniques finales pour utilisation
    final_techniques = validator.extract_final_techniques(results)
    print(f"\n--- FINAL VALIDATED TECHNIQUES ---")
    print(f"Chunks with validated techniques: {len(final_techniques)}")

    total_final_techniques = sum(len(techs) for techs in final_techniques.values())
    print(f"Total final validated techniques: {total_final_techniques}")

    # Affichage de quelques exemples
    sample_chunks = list(final_techniques.keys())[:3]
    for chunk_id in sample_chunks:
        techniques = final_techniques[chunk_id]
        print(f"\n{chunk_id}: {techniques}")


if __name__ == "__main__":
    main()
