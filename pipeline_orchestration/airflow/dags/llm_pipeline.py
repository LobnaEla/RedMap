from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os
import sys
import json
import glob
import time
import requests
from typing import Dict, List, Optional

# Add project paths
sys.path.append("/opt/project")
sys.path.append("/opt/airflow/scripts")
import importlib.util

# Load shared utilities
shared_spec = importlib.util.spec_from_file_location(
    "shared", "/opt/airflow/scripts/shared.py"
)
shared = importlib.util.module_from_spec(shared_spec)
shared_spec.loader.exec_module(shared)
load_chunk_files = shared.load_chunk_files

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
LLM_DIR = os.path.join(DATA_DIR, "llm")
ICL_RESULTS_DIR = os.path.join(LLM_DIR, "icl")
RETRIEVAL_SEARCH_RESULTS_DIR = os.path.join(LLM_DIR, "retrieval_search")
JUDGE_RESULTS_DIR = os.path.join(LLM_DIR, "judge")
LOGS_DIR = os.path.join(BASE_PROJECT_PATH, "logs")

# API Configuration
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8000/search")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# === DAG Configuration ===
default_args = {
    "owner": "cti-llm-analysis",
    "depends_on_past": False,
    "start_date": datetime(2025, 8, 6),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "llm_pipeline",
    default_args=default_args,
    description="LLM Pipeline: Parallel LLM ICL + RAG → Judge Validation",
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=["cti", "llm", "rag", "judge", "pipeline"],
)


# ================================
# CORE TASK FUNCTIONS (using existing system)
# ================================

def prepare_chunks_for_analysis():
    """Load and prepare chunks for parallel processing"""
    print("[PIPELINE] Preparing chunks for analysis...")
    
    # Create LLM directories
    os.makedirs(ICL_RESULTS_DIR, exist_ok=True)
    os.makedirs(RETRIEVAL_SEARCH_RESULTS_DIR, exist_ok=True)
    os.makedirs(JUDGE_RESULTS_DIR, exist_ok=True)
    
    # Load chunk files using existing shared function
    chunk_files = load_chunk_files(CHUNKS_DIR)
    
    if not chunk_files:
        print("[PIPELINE] No chunk files found")
        return {"status": "no_data", "message": "No chunk files found for processing"}
    
    # Filter for ready chunks (preprocessing complete)
    ready_chunks = []
    
    for chunk_file in chunk_files:
        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            
            # Check if preprocessing is complete
            if chunk_data.get("preprocessing_complete", False):
                chunks = chunk_data.get("chunks", [])
                ready_chunks.append({
                    "file_path": chunk_file,
                    "base_name": os.path.splitext(os.path.basename(chunk_file))[0],
                    "chunk_count": len(chunks),
                    "chunks": chunks
                })
        except Exception as e:
            print(f"[PIPELINE] Error processing {chunk_file}: {e}")
    
    print(f"[PIPELINE] Found {len(ready_chunks)} ready files for processing")
    return {"status": "ready", "ready_files": ready_chunks}

def process_llm_icl(**context):
    """Process chunks with LLM In-Context Learning using existing ChunkProcessor"""
    print("[ICL] Starting LLM In-Context Learning processing...")
    
    # Get chunk info from prepare task
    chunk_info = context['task_instance'].xcom_pull(task_ids='prepare_chunks_for_analysis')
    
    if not chunk_info or chunk_info["status"] != "ready":
        print("[ICL] Chunks not ready for processing")
        return {"status": "not_ready", "message": "Chunks not ready for processing"}
    
    # Import existing LLM processor
    try:
        from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        processor = ChunkProcessor(GEMINI_API_KEY)
        print("[ICL] Using existing ChunkProcessor")
    except ImportError:
        print("[ICL] Could not import ChunkProcessor")
        return {"status": "error", "message": "Could not import ChunkProcessor"}
    
    # Process each file using existing LLM logic
    for file_info in chunk_info["ready_files"]:
        print(f"[ICL] Processing file: {file_info['base_name']}")
        
        filename = os.path.basename(file_info["file_path"])
        successful_mappings = []
        
        for chunk in file_info["chunks"]:
            chunk_id = chunk.get("chunk_id", "unknown")
            chunk_text = chunk.get("text", "")
            
            if not chunk_text.strip():
                continue
                
            print(f"[ICL] Processing chunk {chunk_id}")
            
            try:
                # Use existing processor
                mapping = processor.process_chunk(chunk, filename)
                mapping["source_file"] = filename
                
                if mapping["success"]:
                    successful_mappings.append(mapping)
                    print(f"[ICL] Chunk {chunk_id}: Found {len(mapping.get('mitre_techniques', []))} techniques")
                else:
                    print(f"[ICL] Chunk {chunk_id}: Failed - {mapping.get('error', 'Unknown error')}")
                
                # Rate limiting like original
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[ICL] Error processing chunk {chunk_id}: {e}")
        
        # Save results to ICL directory
        if successful_mappings:
            if filename.startswith("chunks_normalized_"):
                source_identifier = filename.replace("chunks_normalized_", "").replace(".json", "")
                icl_filename = f"icl_chunks_normalized_{source_identifier}.json"
            else:
                base_name = filename.replace(".json", "")
                icl_filename = f"icl_{base_name}.json"
            
            file_path = os.path.join(ICL_RESULTS_DIR, icl_filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(successful_mappings, f, indent=2, ensure_ascii=False)
            
            print(f"[ICL] Saved {len(successful_mappings)} results to {icl_filename}")
        
        # Mark LLM processing as complete in original chunk file
        try:
            with open(file_info["file_path"], "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            chunk_data["llm_mapping_complete"] = True
            with open(file_info["file_path"], "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            print(f"[ICL] Marked {filename} as LLM mapping complete")
        except Exception as e:
            print(f"[ICL] Warning: Could not mark LLM complete: {e}")
    
    print(f"[ICL] Completed LLM ICL processing")
    return {"status": "completed"}

def process_rag_retrieval(**context):
    """Process chunks with RAG retrieval using existing pattern"""
    print("[RAG] Starting RAG retrieval processing...")
    
    # Get chunk info from prepare task
    chunk_info = context['task_instance'].xcom_pull(task_ids='prepare_chunks_for_analysis')
    
    if not chunk_info or chunk_info["status"] != "ready":
        print("[RAG] Chunks not ready for processing")
        return {"status": "not_ready", "message": "Chunks not ready for processing"}
    
    # Process each file using existing RAG logic
    for file_info in chunk_info["ready_files"]:
        try:
            print(f"[RAG] Processing file: {file_info['base_name']}")
            
            # Prepare results structure
            chunk_filename = os.path.basename(file_info["file_path"])
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                retrieval_output_filename = f"retrieval_chunks_normalized_{source_identifier}.json"
            else:
                base_name = os.path.splitext(chunk_filename)[0]
                retrieval_output_filename = f"retrieval_{base_name}.json"
            
            results = []
            
            # Process each chunk
            for chunk in file_info["chunks"]:
                chunk_id = chunk.get("chunk_id", 0)
                chunk_text = chunk.get("text", "")
                
                if not chunk_text.strip():
                    print(f"[RAG] Skipping empty chunk {chunk_id}")
                    continue
                
                try:
                    # Query RAG API
                    payload = {"query": chunk_text, "top_k": 5}
                    
                    print(f"[RAG] Querying API for chunk {chunk_id}...")
                    response = requests.post(RAG_API_URL, json=payload, timeout=1000)
                    
                    if response.status_code == 200:
                        rag_response = response.json()
                        
                        chunk_result = {
                            "chunk_id": chunk_id,
                            "original_text": chunk_text,
                            "mitre_techniques": rag_response,
                            "retrieval_timestamp": datetime.now().isoformat(),
                            "status": "success"
                        }
                        
                        results.append(chunk_result)
                        print(f"[RAG] Chunk {chunk_id}: Found {len(rag_response)} MITRE techniques")
                        
                    else:
                        print(f"[RAG] API error for chunk {chunk_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"[RAG] Error processing chunk {chunk_id}: {e}")
                
                # Small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            # Save results for this chunk file
            output_file = os.path.join(RETRIEVAL_SEARCH_RESULTS_DIR, retrieval_output_filename)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"[RAG] Saved results to: {output_file}")
            print(f"[RAG] Processed {len(results)} chunks from {file_info['file_path']}")
            
        except Exception as e:
            print(f"[RAG] Failed to process chunk file {file_info['file_path']}: {e}")
            continue
    
    print(f"[RAG] Completed RAG retrieval processing")
    return {"status": "completed"}

def run_judge_validation(**context):
    """Run LLM-as-a-Judge validation using existing system"""
    print("[JUDGE] Starting LLM-as-a-Judge validation...")
    
    # Import existing judge components
    try:
        sys.path.append("/opt/project/llm_as_a_judge")
        from core.technique_validator import TechniqueValidator
        
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required")
        validator = TechniqueValidator(api_key=GEMINI_API_KEY)
        print("[JUDGE] Using existing TechniqueValidator")
    except ImportError:
        print("[JUDGE] TechniqueValidator not available")
        return {"status": "error", "message": "Could not import TechniqueValidator"}
    
    # Use existing judge logic - get processable files
    chunk_files = load_chunk_files(CHUNKS_DIR)
    processable_files = []
    
    for chunk_file in chunk_files:
        try:
            # Check if chunk file has completed processing
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            
            if not chunk_data.get("preprocessing_complete", False):
                continue
            if not chunk_data.get("llm_mapping_complete", False):
                continue
                
            # Check if corresponding retrieval results exist
            chunk_filename = os.path.basename(chunk_file)
            source_identifier = None
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                retrieval_result_file = os.path.join(RETRIEVAL_SEARCH_RESULTS_DIR, f"retrieval_chunks_normalized_{source_identifier}.json")
                base_name = f"chunks_normalized_{source_identifier}"
            else:
                # Fallback for other naming patterns
                base_name = os.path.splitext(chunk_filename)[0]
                retrieval_result_file = os.path.join(RETRIEVAL_SEARCH_RESULTS_DIR, f"retrieval_{base_name}.json")
            
            if not os.path.exists(retrieval_result_file):
                continue
            
            # Check if ICL results exist
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                icl_result_file = os.path.join(ICL_RESULTS_DIR, f"icl_chunks_normalized_{source_identifier}.json")
            else:
                # Fallback for other naming patterns
                icl_result_file = os.path.join(ICL_RESULTS_DIR, f"icl_{base_name}.json")
            
            if not os.path.exists(icl_result_file):
                continue
            
            # Check if already processed by judge
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                judge_result_file = os.path.join(JUDGE_RESULTS_DIR, f"judge_chunks_normalized_{source_identifier}.json")
            else:
                # Fallback for other naming patterns  
                judge_result_file = os.path.join(JUDGE_RESULTS_DIR, f"judge_{base_name}.json")
            
            if os.path.exists(judge_result_file):
                continue
            
            # File is ready for processing
            processable_files.append({
                "chunk_file": chunk_file,
                "retrieval_file": retrieval_result_file,
                "icl_file": icl_result_file, 
                "judge_file": judge_result_file,
                "base_name": base_name,
                "source_identifier": source_identifier if source_identifier else base_name
            })
            
        except Exception as e:
            print(f"[JUDGE] Error checking file {chunk_file}: {e}")
            continue
    
    if not processable_files:
        print("[JUDGE] No files ready for judge processing")
        return {"status": "no_files", "message": "No files ready for judge processing"}
    
    for file_info in processable_files:
        try:
            print(f"[JUDGE] Processing file: {file_info['base_name']}")
            
            # Load required data
            chunk_data = load_file_data(file_info["chunk_file"])
            retrieval_data = load_file_data(file_info["retrieval_file"])
            icl_data = load_file_data(file_info["icl_file"])
            
            if not all([chunk_data, retrieval_data, icl_data]):
                print(f"[JUDGE] Failed to load required data for {file_info['base_name']}")
                continue
            
            # Prepare validation data in the format expected by existing judge
            chunks = chunk_data.get("chunks", [])
            retrieval_results = {str(r.get("chunk_id")): r.get("mitre_techniques", []) for r in retrieval_data}
            
            # Extract ICL results by chunk_id
            icl_results_by_chunk = {}
            for mapping in icl_data:
                chunk_id = str(mapping.get("chunk_id", ""))
                icl_results_by_chunk[chunk_id] = mapping.get("mitre_techniques", [])
            
            # Prepare validation input
            validation_chunks = []
            retrieval_results_list = []
            icl_results_list = []
            
            for chunk in chunks:
                chunk_id = str(chunk.get("chunk_id", ""))
                
                if chunk_id in retrieval_results and chunk_id in icl_results_by_chunk:
                    validation_chunks.append(chunk)
                    retrieval_results_list.append(retrieval_results[chunk_id])
                    icl_results_list.append(icl_results_by_chunk[chunk_id])
            
            if not validation_chunks:
                print(f"[JUDGE] No matching chunks found for {file_info['base_name']}")
                continue
            
            # Run validation using existing judge
            print(f"[JUDGE] Running validation on {len(validation_chunks)} chunks...")
            results = validator.batch_validate(
                chunks=validation_chunks,
                rag_results_list=retrieval_results_list,
                llm_results_list=icl_results_list,
            )
            
            # Save judge results
            if file_info["source_identifier"].startswith("chunks_normalized_"):
                judge_output_filename = f"judge_{file_info['source_identifier']}.json"
            else:
                judge_output_filename = f"judge_chunks_normalized_{file_info['source_identifier']}.json"
            judge_output_file = os.path.join(JUDGE_RESULTS_DIR, judge_output_filename)
            with open(judge_output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"[JUDGE] Saved judge results to: {judge_output_file}")
            
        except Exception as e:
            print(f"[JUDGE] Error processing file {file_info['base_name']}: {e}")
            continue
    
    print(f"[JUDGE] Completed judge validation")
    return {"status": "completed"}

def load_file_data(file_path: str) -> Dict:
    """Load and parse JSON data from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[PIPELINE] Error loading file {file_path}: {e}")
        return {}


# ================================
# TASK DEFINITIONS
# ================================

start_task = DummyOperator(
    task_id="start_llm_pipeline",
    dag=dag,
)

prepare_chunks_task = PythonOperator(
    task_id="prepare_chunks_for_analysis",
    python_callable=prepare_chunks_for_analysis,
    dag=dag,
)

# Parallel processing tasks
llm_icl_task = PythonOperator(
    task_id="process_llm_icl",
    python_callable=process_llm_icl,
    dag=dag,
)

rag_retrieval_task = PythonOperator(
    task_id="process_rag_retrieval", 
    python_callable=process_rag_retrieval,
    dag=dag,
)

# Wait for both parallel tasks to complete
wait_for_parallel = DummyOperator(
    task_id="wait_for_parallel_completion",
    dag=dag,
)

# Judge validation (runs after both parallel tasks)
judge_validation_task = PythonOperator(
    task_id="run_judge_validation",
    python_callable=run_judge_validation,
    dag=dag,
)

completion_task = DummyOperator(
    task_id="llm_pipeline_complete",
    dag=dag,
)


# ================================
# TASK DEPENDENCIES
# ================================

# Sequential: start → prepare chunks
start_task >> prepare_chunks_task

# Parallel: chunks → (llm_icl + rag_retrieval) → wait
prepare_chunks_task >> [llm_icl_task, rag_retrieval_task] >> wait_for_parallel

# Sequential: wait → judge → complete
wait_for_parallel >> judge_validation_task >> completion_task
