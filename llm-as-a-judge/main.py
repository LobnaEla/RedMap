"""
Script principal pour exécuter l'évaluation LLM-as-a-Judge
"""

import os
import sys
import json
from typing import List, Dict

# Ajout du chemin pour les imports
sys.path.append("/opt/project/cti_pipeline")

from core.evaluator import TechniqueEvaluator
from core.config import PATH_CONFIG
from utils.metrics import EvaluationMetrics
from utils.file_utils import save_evaluation_results


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
    """Charge les résultats RAG"""
    # À adapter selon le format de sortie de votre RAG
    rag_results = {}
    # Implementation à compléter selon votre format RAG
    return rag_results


def load_icl_results(icl_results_dir: str) -> Dict[str, List[str]]:
    """Charge les résultats ICL (LLM)"""
    import glob

    icl_results = {}
    result_files = glob.glob(os.path.join(icl_results_dir, "*.json"))

    for file_path in result_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            chunk_id = data.get("chunk_id")
            techniques = data.get("mitre_techniques", [])
            if chunk_id:
                icl_results[chunk_id] = techniques

    return icl_results


def main():
    """Fonction principale"""
    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    # Chemins des données
    chunks_dir = "/opt/project/cti_pipeline/chunks"
    rag_results_dir = "/opt/project/cti_pipeline/rag_results"  # À créer
    icl_results_dir = "/opt/project/cti_pipeline/llm_results"

    print("Loading data...")

    # Chargement des données
    chunks = load_chunk_data(chunks_dir)
    rag_results = load_rag_results(rag_results_dir)
    icl_results = load_icl_results(icl_results_dir)

    print(f"Loaded {len(chunks)} chunks")
    print(f"RAG results for {len(rag_results)} chunks")
    print(f"ICL results for {len(icl_results)} chunks")

    # Préparation des données pour l'évaluation
    evaluation_data = []
    rag_results_list = []
    icl_results_list = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in rag_results and chunk_id in icl_results:
            evaluation_data.append(chunk)
            rag_results_list.append(rag_results[chunk_id])
            icl_results_list.append(icl_results[chunk_id])

    print(f"Will evaluate {len(evaluation_data)} chunks with both RAG and ICL results")

    if not evaluation_data:
        print("No chunks with both RAG and ICL results found")
        sys.exit(1)

    # Initialisation de l'évaluateur
    evaluator = TechniqueEvaluator(api_key=api_key)

    print("Starting evaluation...")

    # Évaluation
    results = evaluator.batch_evaluate(
        chunks=evaluation_data,
        rag_results_list=rag_results_list,
        icl_results_list=icl_results_list,
    )

    # Calcul des métriques agrégées
    metrics = EvaluationMetrics.calculate_aggregate_scores(results["evaluations"])
    results["aggregate_metrics"] = metrics

    # Sauvegarde des résultats
    output_file = save_evaluation_results(results)
    print(f"Results saved to: {output_file}")

    # Affichage des résultats principaux
    stats = results["statistics"]
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Total chunks evaluated: {stats['total_chunks']}")
    print(f"Successful evaluations: {stats['successful_evaluations']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"RAG wins: {stats['rag_wins']}")
    print(f"ICL wins: {stats['icl_wins']}")
    print(f"Ties: {stats['ties']}")
    print(f"Errors: {stats['errors']}")

    if "aggregate_metrics" in results:
        agg = results["aggregate_metrics"]["overall_metrics"]
        print(
            f"\nMean RAG Score: {agg['mean_rag_score']:.3f} (±{agg['std_rag_score']:.3f})"
        )
        print(
            f"Mean ICL Score: {agg['mean_icl_score']:.3f} (±{agg['std_icl_score']:.3f})"
        )


if __name__ == "__main__":
    main()
