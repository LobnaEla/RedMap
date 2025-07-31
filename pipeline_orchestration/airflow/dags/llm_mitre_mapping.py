import sys
import os
import glob
import json
import time
from typing import List, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# ================================
# PATH CONFIGURATION
# ================================

sys.path.append("/opt/project")
import importlib.util
shared_spec = importlib.util.spec_from_file_location("shared", "/opt/airflow/scripts/shared.py")
shared = importlib.util.module_from_spec(shared_spec)
shared_spec.loader.exec_module(shared)
load_chunk_files = shared.load_chunk_files

BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = f"{BASE_PROJECT_PATH}/data"
METADATA_DIR = f"{BASE_PROJECT_PATH}/data/metadata"
PROCESSED_DIR = f"{BASE_PROJECT_PATH}/data/processed"
CHUNKS_DIR = f"{BASE_PROJECT_PATH}/data/chunks"
LLM_RESULTS_DIR = f"{BASE_PROJECT_PATH}/data/llm_results"
MITRE_MAPPING_DIR = f"{BASE_PROJECT_PATH}/data/mitre_mappings"
LOGS_DIR = f"{BASE_PROJECT_PATH}/logs"

COMPREHENSIVE_MAPPING_FILE = "comprehensive_mitre_mappings.json"
STATS_FILE = "mitre_mapping_statistics.json"

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"Using GEMINI_API_KEY: {GEMINI_API_KEY is not None}")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

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
    description="CTI to MITRE ATT&CK Mapping Pipeline using Gemini 1.5 Flash",
    schedule_interval=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["cti", "llm", "mitre", "mapping", "gemini"],
    max_active_runs=1,
)

# ================================
# SAVING FUNCTIONS
# ================================

def save_processing_results(mappings: List[Dict], stats: Dict, paths: Dict):
    """Sauvegarde les résultats du traitement dans les répertoires appropriés"""
    try:
        print("Creating output directories if they don't exist")
        os.makedirs(LLM_RESULTS_DIR, exist_ok=True)
        os.makedirs(MITRE_MAPPING_DIR, exist_ok=True)

        # Fichier complet
        print("Saving comprehensive mapping file")
        comprehensive_path = os.path.join(
            paths["mitre_mappings"], COMPREHENSIVE_MAPPING_FILE
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
        print(f"Saved comprehensive results to {comprehensive_path}")

        # Fichiers individuels pour les chunks
        print("Saving individual chunk results")
        successful_saves = 0
        for mapping in mappings:
            if mapping.get("success", False):
                file_path = os.path.join(
                    paths["llm_results"], f"{mapping['chunk_id']}.json"
                )
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(mapping, f, indent=2, ensure_ascii=False)
                successful_saves += 1

        print(f"Saved {successful_saves} individual chunk results")

        # Logs d'erreurs
        errors = [m for m in mappings if not m.get("success", True)]
        if errors:
            print(f"Found {len(errors)} errors to log")
            error_path = os.path.join(paths["logs"], "processing_errors.json")
            with open(error_path, "w", encoding="utf-8") as f:
                json.dump(errors, f, indent=2, ensure_ascii=False)
            print(f"Saved error log to {error_path}")

    except Exception as e:
        print("Failed to save results", exc_info=True)
        raise RuntimeError(f"Error saving processing results: {str(e)}")


# ================================
# CORE PROCESSING FUNCTION
# ================================


def process_all_chunks():
    """Traite tous les chunks avec le modèle LLM"""
    from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor

    try:
        print("Starting chunk processing pipeline")

        # Initialisation du processeur
        print("Initializing ChunkProcessor with API key")
        processor = ChunkProcessor(GEMINI_API_KEY)

        # Chargement des fichiers
        chunk_files = load_chunk_files(CHUNKS_DIR)

        if not chunk_files:
            print("❌ No chunk files found!")
            raise FileNotFoundError("No chunk files found in chunks directory")

        print(f"✅ Found {len(chunk_files)} chunk files to process")

        # Statistiques de traitement
        stats = {
            "total_chunks": 0,
            "successful_mappings": 0,
            "failed_mappings": 0,
            "start_time": datetime.now().isoformat(),
        }

        all_mappings = []

        # Traitement fichier par fichier
        for file_idx, chunk_file in enumerate(chunk_files, 1):
            print(f"Processing file {file_idx}/{len(chunk_files)}: {chunk_file}")

            try:
                with open(chunk_file, "r", encoding="utf-8") as f:
                    chunk_data = json.load(f)

                filename = os.path.basename(chunk_file)
                chunks = chunk_data.get("chunks", [])
                print(f"Found {len(chunks)} chunks in {filename}")

                # Traitement chunk par chunk
                for chunk_idx, chunk in enumerate(chunks, 1):
                    stats["total_chunks"] += 1
                    chunk_id = chunk.get("chunk_id", "unknown")

                    print(
                        f"Processing chunk {chunk_idx}/{len(chunks)} (ID: {chunk_id})"
                    )

                    # Validation du chunk
                    if not isinstance(chunk, dict):
                        error_msg = "Invalid chunk format: not a dictionary"
                        print(f"❌ Chunk {chunk_id}: {error_msg}")
                        mapping = {
                            "chunk_id": "unknown",
                            "error": error_msg,
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                        }
                        stats["failed_mappings"] += 1
                        all_mappings.append(mapping)
                        continue

                    if "text" not in chunk or not chunk["text"].strip():
                        error_msg = "Empty text content in chunk"
                        print(f"❌ Chunk {chunk_id}: {error_msg}")
                        mapping = {
                            "chunk_id": chunk_id,
                            "error": error_msg,
                            "success": False,
                            "timestamp": datetime.now().isoformat(),
                        }
                        stats["failed_mappings"] += 1
                        all_mappings.append(mapping)
                        continue

                    # Traitement du chunk
                    print(f"🔄 Sending chunk {chunk_id} to LLM processor")
                    mapping = processor.process_chunk(chunk, filename)
                    mapping["source_file"] = filename

                    if mapping["success"]:
                        print(f"✅ Successfully processed chunk {chunk_id}")
                        print(
                            f"🎯 MITRE techniques found: {mapping.get('mitre_techniques', [])}"
                        )
                        stats["successful_mappings"] += 1
                    else:
                        print(
                            f"❌ Failed to process chunk {chunk_id}: {mapping.get('error', 'Unknown error')}"
                        )
                        stats["failed_mappings"] += 1

                    all_mappings.append(mapping)

                    # Délai entre les requêtes
                    time.sleep(0.5)  # 500ms

                # Log progress after each file
                success_rate = (
                    stats["successful_mappings"] / stats["total_chunks"]
                ) * 100
                print(f"Progress: {file_idx}/{len(chunk_files)} files processed")
                print(f"Current success rate: {success_rate:.2f}%")

                # Save results after each file is processed
                print(f"Saving results for file: {filename}")
                try:
                    # Save individual chunk results for this file
                    file_mappings = [m for m in all_mappings if m.get("source_file") == filename]
                    successful_saves = 0
                    os.makedirs(LLM_RESULTS_DIR, exist_ok=True)
                    
                    for mapping in file_mappings:
                        if mapping.get("success", False):
                            file_path = os.path.join(LLM_RESULTS_DIR, f"{mapping['chunk_id']}.json")
                            with open(file_path, "w", encoding="utf-8") as f:
                                json.dump(mapping, f, indent=2, ensure_ascii=False)
                            successful_saves += 1
                    
                    print(f"✅ Saved {successful_saves} chunk results for {filename}")
                    
                    # Save incremental comprehensive file with current progress
                    os.makedirs(MITRE_MAPPING_DIR, exist_ok=True)
                    incremental_stats = {
                        "generated_at": datetime.now().isoformat(),
                        "total_chunks": stats["total_chunks"],
                        "successful_mappings": stats["successful_mappings"],
                        "success_rate": success_rate / 100,
                        "files_processed": file_idx,
                        "total_files": len(chunk_files),
                    }
                    
                    incremental_path = os.path.join(MITRE_MAPPING_DIR, "incremental_mitre_mappings.json")
                    with open(incremental_path, "w", encoding="utf-8") as f:
                        json.dump({
                            "metadata": incremental_stats,
                            "mappings": all_mappings,
                        }, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Saved incremental results to {incremental_path}")
                    
                    # Save error logs incrementally
                    file_errors = [m for m in file_mappings if not m.get("success", True)]
                    if file_errors:
                        os.makedirs(LOGS_DIR, exist_ok=True)
                        error_path = os.path.join(LOGS_DIR, f"errors_{filename.replace('.json', '')}.json")
                        with open(error_path, "w", encoding="utf-8") as f:
                            json.dump(file_errors, f, indent=2, ensure_ascii=False)
                        print(f"✅ Saved {len(file_errors)} error logs for {filename}")
                    
                except Exception as save_error:
                    print(f"⚠️ Warning: Could not save results for {filename}: {str(save_error)}")

                # Délai entre les fichiers
                time.sleep(2)  # 2s

            except Exception as e:
                print(f"❌ Error processing file {chunk_file}: {str(e)}")
                continue

        # Final statistics
        stats["success_rate"] = (
            stats["successful_mappings"] / stats["total_chunks"]
            if stats["total_chunks"] > 0
            else 0
        )
        stats["end_time"] = datetime.now().isoformat()

        print("\n" + "=" * 50)
        print("📊 Processing Summary:")
        print(f"Total chunks processed: {stats['total_chunks']}")
        print(f"Successful mappings: {stats['successful_mappings']}")
        print(f"Failed mappings: {stats['failed_mappings']}")
        print(f"Success rate: {stats['success_rate']:.2f}%")
        print("=" * 50 + "\n")

        # Final comprehensive save (rename incremental to final)
        try:
            incremental_path = os.path.join(MITRE_MAPPING_DIR, "incremental_mitre_mappings.json")
            final_path = os.path.join(MITRE_MAPPING_DIR, COMPREHENSIVE_MAPPING_FILE)
            
            if os.path.exists(incremental_path):
                # Update the final metadata
                with open(incremental_path, "r", encoding="utf-8") as f:
                    final_data = json.load(f)
                
                final_data["metadata"].update({
                    "generated_at": stats.get("end_time", ""),
                    "success_rate": stats.get("success_rate", 0),
                    "processing_completed": True
                })
                
                with open(final_path, "w", encoding="utf-8") as f:
                    json.dump(final_data, f, indent=2, ensure_ascii=False)
                
                # Remove incremental file
                os.remove(incremental_path)
                print(f"✅ Final comprehensive results saved to {final_path}")
            else:
                # Fallback to original save method
                save_processing_results(
                    all_mappings,
                    stats,
                    {
                        "llm_results": LLM_RESULTS_DIR,
                        "mitre_mappings": MITRE_MAPPING_DIR,
                        "logs": LOGS_DIR,
                    },
                )
                print("✅ Results saved using fallback method")
                
        except Exception as save_error:
            print(f"⚠️ Warning: Error in final save: {str(save_error)}")
            # Fallback to original save method
            save_processing_results(
                all_mappings,
                stats,
                {
                    "llm_results": LLM_RESULTS_DIR,
                    "mitre_mappings": MITRE_MAPPING_DIR,
                    "logs": LOGS_DIR,
                },
            )
            print("✅ Results saved using fallback method")

        print("Results processing completed")
        return {"status": "success", "processed_files": len(chunk_files), **stats}

    except Exception as e:
        print(f"❌ Pipeline failed with error: {str(e)}")
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
        comprehensive_file = os.path.join(MITRE_MAPPING_DIR, COMPREHENSIVE_MAPPING_FILE)
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
        stats_file = os.path.join(MITRE_MAPPING_DIR, STATS_FILE)
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
                os.path.join(MITRE_MAPPING_DIR, COMPREHENSIVE_MAPPING_FILE)
            ),
            "statistics_file_exists": os.path.exists(
                os.path.join(MITRE_MAPPING_DIR, STATS_FILE)
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
