import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


def save_judge_results(
    judge_results: Dict[str, Any], include_detailed: bool = True, output_dir: str = None
) -> str:
    """Save judge validation results to file."""

    if output_dir is None:
        # Use project structure from config
        from ..core.config import PATH_CONFIG

        output_dir = PATH_CONFIG["judge_results"]

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if include_detailed:
        filename = f"judge_validation_detailed_{timestamp}.json"
        data_to_save = judge_results
    else:
        filename = f"judge_validation_summary_{timestamp}.json"
        # Extract only essential information
        data_to_save = {
            "statistics": judge_results.get("statistics", {}),
            "final_techniques": {
                v["chunk_id"]: v.get("final_validated_techniques", [])
                for v in judge_results.get("validations", [])
                if v.get("success", False)
            },
            "metadata": judge_results.get("metadata", {}),
        }

    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=2, ensure_ascii=False)

        print(f"✅ Judge results saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"❌ Error saving judge results: {e}")
        return ""


def save_final_techniques_only(
    judge_results: Dict[str, Any], output_dir: str = None
) -> str:
    """Save only final validated techniques for operational use."""

    if output_dir is None:
        from ..core.config import PATH_CONFIG

        output_dir = PATH_CONFIG["judge_results"]

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"final_validated_techniques_{timestamp}.json"

    # Extract just the final techniques
    final_data = {
        "generated_at": datetime.now().isoformat(),
        "total_chunks": judge_results.get("statistics", {}).get("total_chunks", 0),
        "successful_validations": judge_results.get("statistics", {}).get(
            "successful_validations", 0
        ),
        "final_techniques": {},
    }

    for validation in judge_results.get("validations", []):
        if validation.get("success", False):
            chunk_id = validation["chunk_id"]
            techniques = validation.get("final_validated_techniques", [])
            final_data["final_techniques"][chunk_id] = techniques

    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Final techniques saved: {filepath}")
        return filepath

    except Exception as e:
        print(f"❌ Error saving final techniques: {e}")
        return ""


def load_judge_results(filepath: str) -> Dict[str, Any]:
    """Load previously saved judge results."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"❌ Error loading judge results from {filepath}: {e}")
        return {}
