import os
import json
from typing import Dict, List
from datetime import datetime


def save_evaluation_results(
    results: Dict, output_path: str = None, include_detailed: bool = True
) -> str:
    """
    Sauvegarde les résultats d'évaluation

    Args:
        results: Résultats de l'évaluation
        output_path: Chemin de sortie (optionnel)
        include_detailed: Inclure les détails pour chaque chunk

    Returns:
        Chemin du fichier sauvegardé
    """
    from ..core.config import PATH_CONFIG

    # Création du répertoire si nécessaire
    if output_path is None:
        os.makedirs(PATH_CONFIG["evaluations"], exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            PATH_CONFIG["evaluations"], f"evaluation_results_{timestamp}.json"
        )

    # Préparer les données pour la sauvegarde
    save_data = {
        "metadata": results.get("metadata", {}),
        "statistics": results.get("statistics", {}),
    }

    if include_detailed:
        save_data["evaluations"] = results.get("evaluations", [])
    else:
        # Seulement les résumés
        save_data["evaluation_summary"] = [
            {
                "chunk_id": eval_data.get("chunk_id"),
                "success": eval_data.get("success"),
                "winner": eval_data.get("evaluation", {}).get("winner"),
                "rag_score": eval_data.get("evaluation", {}).get("rag_score"),
                "icl_score": eval_data.get("evaluation", {}).get("icl_score"),
            }
            for eval_data in results.get("evaluations", [])
        ]

    # Sauvegarde
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    return output_path


def load_evaluation_results(file_path: str) -> Dict:
    """
    Charge les résultats d'évaluation depuis un fichier

    Args:
        file_path: Chemin du fichier

    Returns:
        Résultats chargés
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
