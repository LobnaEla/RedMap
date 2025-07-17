import sys
import os
import glob
import json
import time
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.models import Variable
from cti_pipeline.scripts.llm.core.file_utils import save_processing_results


ANTHROPIC_API_KEY = Variable.get("ANTHROPIC_API_KEY")
# ================================
# PATH CONFIGURATION
# ================================
sys.path.append("/opt/project")

BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = f"{BASE_PROJECT_PATH}/data"
METADATA_DIR = f"{BASE_PROJECT_PATH}/metadata"
CHUNKS_DIR = f"{BASE_PROJECT_PATH}/chunks"
LLM_RESULTS_DIR = f"{BASE_PROJECT_PATH}/llm_results"
MITRE_MAPPING_DIR = f"{BASE_PROJECT_PATH}/mitre_mappings"
LOGS_DIR = f"{BASE_PROJECT_PATH}/logs"

# ================================
# DAG DEFINITION
# ================================
default_args = {
    "owner": "cti-llm-mapping",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=15),
}

dag = DAG(
    "llm_mitre_mapping",
    default_args=default_args,
    description="CTI to MITRE ATT&CK Mapping Pipeline using Claude Opus 4",
    schedule_interval=timedelta(hours=8),
    catchup=False,
    is_paused_upon_creation=False,
    tags=["cti", "llm", "mitre", "mapping", "claude"],
    max_active_runs=1,
)


# ================================
# CORE PROCESSING FUNCTION
# ================================
def process_all_chunks():
    """Traite tous les chunks avec le modèle LLM"""
    from cti_pipeline.scripts.llm.core.chunk_processor import ChunkProcessor

    try:
        # Initialisation du processeur
        processor = ChunkProcessor(api_key=ANTHROPIC_API_KEY)

        # Chargement des fichiers
        chunk_files = glob.glob(os.path.join(CHUNKS_DIR, "chunks_*.json"))
        if not chunk_files:
            raise FileNotFoundError("No chunk files found in chunks directory")

        print(f"Found {len(chunk_files)} chunk files to process")

        # Statistiques de traitement
        stats = {
            "total_chunks": 0,
            "successful_mappings": 0,
            "failed_mappings": 0,
            "start_time": datetime.now().isoformat(),
        }

        all_mappings = []

        # Traitement fichier par fichier
        for chunk_file in chunk_files:
            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunk_data = json.load(f)

                filename = os.path.basename(chunk_file)
                chunks = chunk_data.get("chunks", [])

                # Traitement chunk par chunk
                for chunk in chunks:
                    stats["total_chunks"] += 1

                    # Validation du chunk
                    if not isinstance(chunk, dict):
                        mapping = {
                            "chunk_id": "unknown",
                            "error": "Invalid chunk format: not a dictionary",
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                        }
                        stats["failed_mappings"] += 1
                        all_mappings.append(mapping)
                        continue

                    if "text" not in chunk or not chunk["text"].strip():
                        mapping = {
                            "chunk_id": chunk.get("chunk_id", "unknown"),
                            "error": "Empty text content in chunk",
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                        }
                        stats["failed_mappings"] += 1
                        all_mappings.append(mapping)
                        continue

                    # Traitement du chunk
                    mapping = processor.process_chunk(chunk, filename)
                    mapping["source_file"] = filename

                    if mapping["success"]:
                        stats["successful_mappings"] += 1
                    else:
                        stats["failed_mappings"] += 1

                    all_mappings.append(mapping)

                    # Délai entre les requêtes
                    time.sleep(0.5)  # 500ms

                # Délai entre les fichiers
                time.sleep(2)  # 2s

            except Exception as e:
                print(f"Error processing {chunk_file}: {str(e)}")
                continue

        # Calcul du taux de succès
        stats["success_rate"] = (
            stats["successful_mappings"] / stats["total_chunks"]
            if stats["total_chunks"] > 0
            else 0
        )
        stats["end_time"] = datetime.now().isoformat()

        # Sauvegarde des résultats
        save_processing_results(
            all_mappings,
            stats,
            {
                "llm_results": LLM_RESULTS_DIR,
                "mitre_mappings": MITRE_MAPPING_DIR,
                "logs": LOGS_DIR,
            },
        )

        return {"status": "success", "processed_files": len(chunk_files), **stats}

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
        }


# ================================
# STATISTICS & VALIDATION FUNCTIONS
# ================================
def generate_mitre_statistics():
    """Generate statistics and analysis of MITRE mappings"""
    try:
        # Load comprehensive results
        comprehensive_file = os.path.join(
            MITRE_MAPPING_DIR, "comprehensive_mitre_mappings.json"
        )
        if not os.path.exists(comprehensive_file):
            raise FileNotFoundError("Comprehensive MITRE mappings file not found")

        with open(comprehensive_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        mappings = data.get("mappings", [])
        successful_mappings = [m for m in mappings if m.get("success", False)]

        # Extract all MITRE techniques
        all_techniques = []
        for mapping in successful_mappings:
            all_techniques.extend(mapping.get("mitre_techniques", []))

        # Calculate statistics
        technique_counts = {}
        for technique in all_techniques:
            technique_counts[technique] = technique_counts.get(technique, 0) + 1

        # Sort by frequency
        sorted_techniques = sorted(
            technique_counts.items(), key=lambda x: x[1], reverse=True
        )

        statistics = {
            "generation_timestamp": datetime.now().isoformat(),
            "total_successful_mappings": len(successful_mappings),
            "total_techniques_identified": len(all_techniques),
            "unique_techniques": len(technique_counts),
            "top_10_techniques": sorted_techniques[:10],
            "technique_distribution": dict(sorted_techniques),
            "files_processed": len(
                set(m.get("source_file", "unknown") for m in mappings)
            ),
            "success_rate": data.get("metadata", {}).get("success_rate", 0),
        }

        # Save statistics
        stats_file = os.path.join(MITRE_MAPPING_DIR, "mitre_mapping_statistics.json")
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)

        # Generate summary report
        summary_report = {
            "summary": {
                "total_mappings": len(successful_mappings),
                "unique_techniques": len(technique_counts),
                "success_rate": f"{data.get('metadata', {}).get('success_rate', 0):.2%}",
                "most_common_technique": (
                    sorted_techniques[0] if sorted_techniques else None
                ),
            },
            "detailed_stats": statistics,
        }

        summary_file = os.path.join(MITRE_MAPPING_DIR, "mapping_summary_report.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "statistics_generated": True,
            "unique_techniques": len(technique_counts),
            "total_mappings": len(successful_mappings),
            "output_files": [stats_file, summary_file],
        }

    except Exception as e:
        error_msg = f"Statistics generation failed: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
        }


def validate_llm_results():
    """Validate LLM processing results"""
    try:
        # Check files existence
        validation_results = {
            "comprehensive_file_exists": os.path.exists(
                os.path.join(MITRE_MAPPING_DIR, "comprehensive_mitre_mappings.json")
            ),
            "statistics_file_exists": os.path.exists(
                os.path.join(MITRE_MAPPING_DIR, "mitre_mapping_statistics.json")
            ),
            "llm_results_count": len(glob.glob(f"{LLM_RESULTS_DIR}/*.json")),
            "processing_logs_count": len(glob.glob(f"{LOGS_DIR}/*.json")),
            "pipeline_success": False,
        }

        # Load comprehensive results if exists
        if validation_results["comprehensive_file_exists"]:
            comp_file = os.path.join(
                MITRE_MAPPING_DIR, "comprehensive_mitre_mappings.json"
            )
            with open(comp_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = data.get("metadata", {})
            validation_results.update(
                {
                    "total_chunks_processed": metadata.get("total_chunks", 0),
                    "successful_mappings": metadata.get("successful_mappings", 0),
                    "success_rate": metadata.get("success_rate", 0),
                    "processing_completed": True,
                }
            )

            # Check if we have at least 70% success rate
            if metadata.get("success_rate", 0) >= 0.7:
                validation_results["pipeline_success"] = True

        return validation_results

    except Exception as e:
        error_msg = f"Validation failed: {str(e)}"
        print(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "timestamp": datetime.now().isoformat(),
        }


def llm_completion():
    """Final completion task"""
    return {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "message": "LLM processing pipeline finished successfully",
    }


# ================================
# TASK DEFINITIONS
# ================================
start_task = DummyOperator(
    task_id="start_llm_processing",
    dag=dag,
)

llm_processing_task = PythonOperator(
    task_id="process_chunks_with_llm",
    python_callable=process_all_chunks,
    dag=dag,
)

statistics_task = PythonOperator(
    task_id="generate_mitre_statistics",
    python_callable=generate_mitre_statistics,
    dag=dag,
)

validation_task = PythonOperator(
    task_id="validate_llm_results",
    python_callable=validate_llm_results,
    dag=dag,
)

end_task = PythonOperator(
    task_id="llm_completion",
    python_callable=llm_completion,
    dag=dag,
)

# ================================
# TASK DEPENDENCIES
# ================================
start_task >> llm_processing_task >> statistics_task >> validation_task >> end_task
