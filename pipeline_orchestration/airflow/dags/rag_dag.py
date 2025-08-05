from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import sys

sys.path.append("/opt/project")
import importlib.util

shared_spec = importlib.util.spec_from_file_location(
    "shared", "/opt/airflow/scripts/shared.py"
)
shared = importlib.util.module_from_spec(shared_spec)
shared_spec.loader.exec_module(shared)
load_chunk_files = shared.load_chunk_files

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_scraped_data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
EXTRACT_DIR = os.path.join(PROCESSED_DIR, "extracted")
CLEAN_DIR = os.path.join(PROCESSED_DIR, "cleaned")
NORMALIZE_DIR = os.path.join(PROCESSED_DIR, "normalized")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")


def get_chunk():
    print("[Chunking] Getting chunk for RAG...")
    chunk_files = load_chunk_files(CHUNKS_DIR)
    print(f"Found {len(chunk_files)} chunk files.")
    return chunk_files


def apply_rag():
    """
    Apply RAG to process chunks and perform retrieval search
    """
    import json
    import requests
    import time
    from datetime import datetime

    chunk_files = get_chunk()
    if not chunk_files:
        print("[RAG] No chunk files found. Skipping RAG application.")
        return

    print(f"[RAG] Applying RAG on {len(chunk_files)} chunk files...")

    # Configure RAG API endpoint
    RAG_API_URL = os.getenv("RAG_API_URL")
    if not RAG_API_URL:
        print(
            "[RAG] RAG API URL not set. Please set the RAG_API_URL environment variable."
        )
        return
    RAG_OUTPUT_DIR = os.path.join(DATA_DIR, "rag_results")
    os.makedirs(RAG_OUTPUT_DIR, exist_ok=True)

    total_chunks_processed = 0
    total_files_processed = 0

    for chunk_file in chunk_files:
        try:
            print(f"[RAG] Processing chunk file: {chunk_file}")

            # Load chunk file
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)

            # Prepare results structure
            base_name = os.path.splitext(os.path.basename(chunk_file))[0]
            
            # Check if already processed
            output_file = os.path.join(RAG_OUTPUT_DIR, f"rag_{base_name}.json")
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    if existing_data.get("rag_processing_complete", False):
                        print(f"[RAG] Skipping {chunk_file} - RAG processing already completed")
                        continue
            
            # Check if prerequisites are met
            if not chunk_data.get("preprocessing_complete", False):
                print(f"[RAG] Skipping {chunk_file} - preprocessing not complete")
                continue
                
            if not chunk_data.get("llm_mapping_complete", False):
                print(f"[RAG] Skipping {chunk_file} - LLM mapping not complete")
                continue
            
            results = {
                "original_chunk_file": chunk_file,
                "processing_timestamp": datetime.now().isoformat(),
                "total_chunks": chunk_data.get("total_chunks", 0),
                "processed_chunks": 0,
                "rag_processing_complete": False,
                "rag_results": [],
            }

            # Process each chunk
            for chunk in chunk_data.get("chunks", []):
                chunk_id = chunk.get("chunk_id", 0)
                chunk_text = chunk.get("text", "")

                if not chunk_text.strip():
                    print(f"[RAG] Skipping empty chunk {chunk_id}")
                    continue

                try:
                    # Prepare query for RAG API
                    # Combine text and IOCs for better retrieval
                    query_text = chunk_text

                    # Query RAG API
                    payload = {
                        "query": query_text,
                        "top_k": 5,  # Get top 5 most relevant MITRE techniques
                    }

                    print(f"[RAG] Querying API for chunk {chunk_id}...")
                    response = requests.post(RAG_API_URL, json=payload, timeout=1000)

                    if response.status_code == 200:
                        rag_response = response.json()

                        # Store chunk result
                        chunk_result = {
                            "chunk_id": chunk_id,
                            "original_text": chunk_text,
                            "mitre_techniques": rag_response,
                            "retrieval_timestamp": datetime.now().isoformat(),
                            "status": "success",
                        }

                        results["rag_results"].append(chunk_result)
                        results["processed_chunks"] += 1
                        total_chunks_processed += 1

                        print(
                            f"[RAG] Chunk {chunk_id}: Found {len(rag_response)} MITRE techniques"
                        )

                    else:
                        print(
                            f"[RAG] API error for chunk {chunk_id}: {response.status_code}"
                        )
                        error_result = {
                            "chunk_id": chunk_id,
                            "original_text": chunk_text,
                            "mitre_techniques": [],
                            "retrieval_timestamp": datetime.now().isoformat(),
                            "status": "api_error",
                            "error": f"HTTP {response.status_code}: {response.text}",
                        }
                        results["rag_results"].append(error_result)

                except requests.exceptions.RequestException as e:
                    print(f"[RAG] Network error for chunk {chunk_id}: {e}")
                    error_result = {
                        "chunk_id": chunk_id,
                        "original_text": chunk_text,
                        "mitre_techniques": [],
                        "retrieval_timestamp": datetime.now().isoformat(),
                        "status": "network_error",
                        "error": str(e),
                    }
                    results["rag_results"].append(error_result)

                except Exception as e:
                    print(f"[RAG] Error processing chunk {chunk_id}: {e}")
                    error_result = {
                        "chunk_id": chunk_id,
                        "original_text": chunk_text,
                        "mitre_techniques": [],
                        "retrieval_timestamp": datetime.now().isoformat(),
                        "status": "processing_error",
                        "error": str(e),
                    }
                    results["rag_results"].append(error_result)

                # Small delay to avoid overwhelming the API
                time.sleep(0.1)

            # Mark RAG processing as complete
            results["rag_processing_complete"] = True

            # Save results for this chunk file
            output_file = os.path.join(RAG_OUTPUT_DIR, f"rag_{base_name}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            print(f"[RAG] Saved results to: {output_file}")
            print(
                f"[RAG] Processed {results['processed_chunks']}/{results['total_chunks']} chunks from {chunk_file}"
            )
            total_files_processed += 1

        except Exception as e:
            print(f"[RAG] Failed to process chunk file {chunk_file}: {e}")
            continue

    print(f"[RAG] RAG processing complete!")
    print(f"[RAG] Files processed: {total_files_processed}/{len(chunk_files)}")
    print(f"[RAG] Total chunks processed: {total_chunks_processed}")
    print(f"[RAG] Results saved in: {RAG_OUTPUT_DIR}")

    return {
        "total_files_processed": total_files_processed,
        "total_chunks_processed": total_chunks_processed,
        "output_directory": RAG_OUTPUT_DIR,
        "status": "completed",
    }


def validate_format():
    """
    Validate RAG output format and generate summary statistics
    """
    import json
    import glob

    print("[Validation] Validating RAG output...")

    RAG_OUTPUT_DIR = os.path.join(DATA_DIR, "rag_results")

    if not os.path.exists(RAG_OUTPUT_DIR):
        print(f"[Validation] RAG output directory does not exist: {RAG_OUTPUT_DIR}")
        return {"status": "failed", "error": "No RAG output directory found"}

    # Find all RAG result files
    rag_files = glob.glob(os.path.join(RAG_OUTPUT_DIR, "rag_*.json"))

    if not rag_files:
        print("[Validation] No RAG result files found")
        return {"status": "failed", "error": "No RAG result files found"}

    # Validation statistics
    validation_stats = {
        "total_files": len(rag_files),
        "total_chunks": 0,
        "successful_chunks": 0,
        "failed_chunks": 0,
        "techniques_found": 0,
        "files_with_errors": 0,
        "validation_errors": [],
    }

    for rag_file in rag_files:
        try:
            with open(rag_file, "r", encoding="utf-8") as f:
                rag_data = json.load(f)

            # Validate file structure
            required_fields = [
                "original_chunk_file",
                "processing_timestamp",
                "total_chunks",
                "processed_chunks",
                "rag_processing_complete",
                "rag_results",
            ]
            missing_fields = [
                field for field in required_fields if field not in rag_data
            ]

            if missing_fields:
                validation_stats["files_with_errors"] += 1
                validation_stats["validation_errors"].append(
                    {
                        "file": rag_file,
                        "error": f"Missing required fields: {missing_fields}",
                    }
                )
                continue

            # Count chunks and techniques
            validation_stats["total_chunks"] += rag_data.get("total_chunks", 0)
            file_successful = 0
            file_failed = 0
            file_techniques = 0

            for result in rag_data.get("rag_results", []):
                if result.get("status") == "success":
                    file_successful += 1
                    file_techniques += len(result.get("mitre_techniques", []))
                else:
                    file_failed += 1

            validation_stats["successful_chunks"] += file_successful
            validation_stats["failed_chunks"] += file_failed
            validation_stats["techniques_found"] += file_techniques

            print(
                f"[Validation] {os.path.basename(rag_file)}: {file_successful}/{rag_data.get('processed_chunks', 0)} successful, {file_techniques} techniques found"
            )

        except json.JSONDecodeError as e:
            validation_stats["files_with_errors"] += 1
            validation_stats["validation_errors"].append(
                {"file": rag_file, "error": f"Invalid JSON: {str(e)}"}
            )
        except Exception as e:
            validation_stats["files_with_errors"] += 1
            validation_stats["validation_errors"].append(
                {"file": rag_file, "error": f"Validation error: {str(e)}"}
            )

    # Calculate success rate
    if validation_stats["total_chunks"] > 0:
        success_rate = (
            validation_stats["successful_chunks"] / validation_stats["total_chunks"]
        ) * 100
    else:
        success_rate = 0

    validation_stats["success_rate"] = round(success_rate, 2)
    validation_stats["status"] = "completed"

    # Save validation summary
    summary_file = os.path.join(RAG_OUTPUT_DIR, "validation_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(validation_stats, f, indent=2, ensure_ascii=False)

    print(f"[Validation] Validation complete!")
    print(f"[Validation] Files processed: {validation_stats['total_files']}")
    print(
        f"[Validation] Chunks processed: {validation_stats['successful_chunks']}/{validation_stats['total_chunks']} ({validation_stats['success_rate']}%)"
    )
    print(
        f"[Validation] MITRE techniques found: {validation_stats['techniques_found']}"
    )
    print(f"[Validation] Files with errors: {validation_stats['files_with_errors']}")
    print(f"[Validation] Summary saved to: {summary_file}")

    if validation_stats["validation_errors"]:
        print("[Validation] Validation errors found:")
        for error in validation_stats["validation_errors"]:
            print(f"  - {error['file']}: {error['error']}")

    return validation_stats


with DAG(
    dag_id="rag_pipeline",
    start_date=datetime(2025, 7, 23),
    schedule_interval=None,
    catchup=False,
    description="RAG Pipeline: Process chunks with MITRE technique retrieval",
    tags=["cti", "rag", "mitre"],
    max_active_runs=1,
) as dag:

    task_get_chunk = PythonOperator(
        task_id="get_chunk",
        python_callable=get_chunk,
    )

    task_rag = PythonOperator(
        task_id="apply_rag",
        python_callable=apply_rag,
    )

    task_validate = PythonOperator(
        task_id="validate_format",
        python_callable=validate_format,
    )

    task_get_chunk >> task_rag >> task_validate
