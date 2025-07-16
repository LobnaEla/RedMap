import os
import json
from typing import List, Dict


def save_processing_results(mappings: List[Dict], stats: Dict, paths: Dict):
    """
    Sauvegarde les résultats du traitement dans les répertoires appropriés

    Args:
        mappings: Liste des résultats de mapping
        stats: Statistiques du traitement
        paths: Configuration des chemins
    """
    # Création des répertoires si nécessaire
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

    # Fichier complet
    comprehensive_path = os.path.join(
        paths["mitre_mappings"], "comprehensive_mitre_mappings.json"
    )
    with open(comprehensive_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "metadata": {
                    "generated_at": stats.get("end_time", ""),
                    "total_chunks": stats["total_chunks"],
                    "successful_mappings": stats["successful_mappings"],
                    "success_rate": stats.get("success_rate", 0),
                },
                "mappings": mappings,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    # Fichiers individuels pour les chunks
    for mapping in mappings:
        if mapping.get("success", False):
            file_path = os.path.join(
                paths["llm_results"], f"{mapping['chunk_id']}.json"
            )
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mapping, f, indent=2, ensure_ascii=False)

    # Logs d'erreurs
    errors = [m for m in mappings if not m.get("success", True)]
    if errors:
        error_path = os.path.join(paths["logs"], "processing_errors.json")
        with open(error_path, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)


def load_chunk_files(chunks_dir: str) -> List[str]:
    """Charge les fichiers de chunks depuis le répertoire"""
    import glob

    try:
        chunk_files = glob.glob(os.path.join(chunks_dir, "chunks_*.json"))
        if not chunk_files:
            raise FileNotFoundError(f"No chunk files found in {chunks_dir}")
        return chunk_files

    except Exception as e:
        raise RuntimeError(f"Error loading chunk files: {str(e)}")
