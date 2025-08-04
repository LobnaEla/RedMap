import os
import json
from typing import Dict, List
from datetime import datetime


def save_judge_results(
    results: Dict, output_path: str = None, include_detailed: bool = True
) -> str:
    """
    Sauvegarde les résultats du judge

    Args:
        results: Résultats du judge
        output_path: Chemin de sortie
        include_detailed: Inclure les détails pour chaque chunk

    Returns:
        Chemin du fichier sauvegardé
    """
    from ..core.config import PATH_CONFIG

    # Création du répertoire si nécessaire
    if output_path is None:
        os.makedirs(PATH_CONFIG["validated_results"], exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            PATH_CONFIG["validated_results"], f"validation_results_{timestamp}.json"
        )

    # Préparer les données pour la sauvegarde
    save_data = {
        "metadata": results.get("metadata", {}),
        "statistics": results.get("statistics", {}),
    }

    if include_detailed:
        save_data["validations"] = results.get("validations", [])
    else:
        # Seulement les techniques finales validées
        save_data["final_techniques"] = {}
        for validation in results.get("validations", []):
            if validation.get("success", False):
                chunk_id = validation.get("chunk_id")
                validated_techniques = validation.get("final_validated_techniques", [])
                save_data["final_techniques"][chunk_id] = validated_techniques

    # Sauvegarde
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    return output_path


def save_final_techniques_only(
    validation_results: Dict, output_path: str = None
) -> str:
    """
    Sauvegarde uniquement les techniques finales validées

    Args:
        validation_results: Résultats de validation
        output_path: Chemin de sortie

    Returns:
        Chemin du fichier sauvegardé
    """
    from ..core.config import PATH_CONFIG

    if output_path is None:
        os.makedirs(PATH_CONFIG["validated_results"], exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            PATH_CONFIG["validated_results"],
            f"final_validated_techniques_{timestamp}.json",
        )

    final_techniques = {}
    stats = {
        "total_chunks": 0,
        "chunks_with_techniques": 0,
        "total_validated_techniques": 0,
        "generated_at": datetime.now().isoformat(),
    }

    for validation in validation_results.get("validations", []):
        if validation.get("success", False):
            chunk_id = validation.get("chunk_id")
            validated_techniques = validation.get("final_validated_techniques", [])

            final_techniques[chunk_id] = validated_techniques
            stats["total_chunks"] += 1

            if validated_techniques:
                stats["chunks_with_techniques"] += 1
                stats["total_validated_techniques"] += len(validated_techniques)

    save_data = {
        "final_validated_techniques": final_techniques,
        "statistics": stats,
        "metadata": {
            "description": "Final validated MITRE techniques after cross-validation",
            "validation_date": stats["generated_at"],
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    return output_path


def load_validation_results(file_path: str) -> Dict:
    """
    Charge les résultats de validation depuis un fichier

    Args:
        file_path: Chemin du fichier

    Returns:
        Résultats chargés
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
