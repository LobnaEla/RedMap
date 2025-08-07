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

# Import database manager
from db_manager import save_cti_results

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")
RAG_RESULTS_DIR = os.path.join(DATA_DIR, "rag_results")
LLM_RESULTS_DIR = os.path.join(DATA_DIR, "llm_results")
JUDGE_RESULTS_DIR = os.path.join(DATA_DIR, "judge_results")
LOGS_DIR = os.path.join(BASE_PROJECT_PATH, "logs")
UNIFIED_RESULTS_DIR = os.path.join(DATA_DIR, "unified_analysis_results")

# API Configuration
RAG_API_URL = os.getenv("RAG_API_URL", "http://rag-api:8000/search")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# === DAG Configuration ===
default_args = {
    "owner": "cti-unified-analysis",
    "depends_on_past": False,
    "start_date": datetime(2025, 8, 6),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "unified_llm_analysis_dag",
    default_args=default_args,
    description="Unified LLM Analysis: Parallel LLM ICL + RAG → Judge Validation",
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    max_active_runs=1,
    tags=["cti", "llm", "rag", "judge", "unified"],
)


# ================================
# CORE TASK FUNCTIONS (using existing system)
# ================================

def prepare_chunks_for_analysis():
    """Load and prepare chunks for parallel processing"""
    print("[UNIFIED] Preparing chunks for analysis...")
    
    # Create output directory
    os.makedirs(UNIFIED_RESULTS_DIR, exist_ok=True)
    
    # Load chunk files using existing shared function
    chunk_files = load_chunk_files(CHUNKS_DIR)
    
    if not chunk_files:
        print("[UNIFIED] No chunk files found")
        return {
            "status": "no_data",
            "chunk_files": [],
            "message": "No chunk files found for processing"
        }
    
    # Filter for ready chunks (preprocessing complete)
    ready_chunks = []
    total_chunks_count = 0
    
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
                total_chunks_count += len(chunks)
        except Exception as e:
            print(f"[UNIFIED] Error processing {chunk_file}: {e}")
    
    print(f"[UNIFIED] Found {len(ready_chunks)} ready files with {total_chunks_count} chunks")
    
    # Store chunk info for downstream tasks
    chunk_info = {
        "status": "ready",
        "ready_files": ready_chunks,
        "total_files": len(ready_chunks),
        "total_chunks": total_chunks_count,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save chunk info for other tasks to use with timestamp in filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    chunk_info_file = os.path.join(UNIFIED_RESULTS_DIR, f"chunk_preparation_info_{timestamp}.json")
    with open(chunk_info_file, "w", encoding="utf-8") as f:
        json.dump(chunk_info, f, indent=2, ensure_ascii=False)
    
    return chunk_info

def process_llm_icl(**context):
    """Process chunks with LLM In-Context Learning using existing ChunkProcessor"""
    print("[UNIFIED-LLM] Starting LLM In-Context Learning processing...")
    
    # Load chunk preparation info (find the most recent one)
    chunk_info_files = glob.glob(os.path.join(UNIFIED_RESULTS_DIR, "chunk_preparation_info_*.json"))
    if not chunk_info_files:
        print("[UNIFIED-LLM] No chunk preparation info found")
        return {"status": "error", "message": "Could not find chunk preparation info"}
    
    # Use the most recent chunk info file
    chunk_info_file = max(chunk_info_files, key=os.path.getmtime)
    try:
        with open(chunk_info_file, "r", encoding="utf-8") as f:
            chunk_info = json.load(f)
    except Exception as e:
        print(f"[UNIFIED-LLM] Error loading chunk info: {e}")
        return {"status": "error", "message": "Could not load chunk preparation info"}
    
    if chunk_info["status"] != "ready":
        print("[UNIFIED-LLM] Chunks not ready for processing")
        return {"status": "not_ready", "message": "Chunks not ready for processing"}
    
    # Import existing LLM processor
    try:
        from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor
        processor = ChunkProcessor(GEMINI_API_KEY)
        print("[UNIFIED-LLM] Using existing ChunkProcessor")
    except ImportError:
        print("[UNIFIED-LLM] Could not import ChunkProcessor")
        return {"status": "error", "message": "Could not import ChunkProcessor"}
    
    # Process each file using existing LLM logic
    llm_results = {
        "processing_timestamp": datetime.now().isoformat(),
        "total_files_processed": 0,
        "total_chunks_processed": 0,
        "file_results": []
    }
    
    # Create LLM results directory
    os.makedirs(LLM_RESULTS_DIR, exist_ok=True)
    
    for file_info in chunk_info["ready_files"]:
        print(f"[UNIFIED-LLM] Processing file: {file_info['base_name']}")
        
        filename = os.path.basename(file_info["file_path"])
        successful_mappings = []
        
        for chunk in file_info["chunks"]:
            chunk_id = chunk.get("chunk_id", "unknown")
            chunk_text = chunk.get("text", "")
            
            if not chunk_text.strip():
                continue
                
            print(f"[UNIFIED-LLM] Processing chunk {chunk_id}")
            
            try:
                # Use existing processor
                mapping = processor.process_chunk(chunk, filename)
                mapping["source_file"] = filename
                
                if mapping["success"]:
                    successful_mappings.append(mapping)
                    print(f"[UNIFIED-LLM] Chunk {chunk_id}: Found {len(mapping.get('mitre_techniques', []))} techniques")
                else:
                    print(f"[UNIFIED-LLM] Chunk {chunk_id}: Failed - {mapping.get('error', 'Unknown error')}")
                
                llm_results["total_chunks_processed"] += 1
                
                # Rate limiting like original
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[UNIFIED-LLM] Error processing chunk {chunk_id}: {e}")
        
        # Save results 
        if successful_mappings:
            if filename.startswith("chunks_normalized_"):
                source_identifier = filename.replace("chunks_normalized_", "").replace(".json", "")
                llm_filename = f"llm_chunks_normalized_{source_identifier}.json"
            else:
                # Fallback for other naming patterns
                base_name = filename.replace(".json", "")
                llm_filename = f"llm_{base_name}.json"
            file_path = os.path.join(LLM_RESULTS_DIR, llm_filename)
            
            file_results = {
                "source_file": filename,
                "total_chunks": len(file_info["chunks"]),
                "successful_chunks": len(successful_mappings),
                "timestamp": datetime.now().isoformat(),
                "mappings": successful_mappings
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(file_results, f, indent=2, ensure_ascii=False)
            
            print(f"[UNIFIED-LLM] Saved {len(successful_mappings)} results to {llm_filename}")
        
        # Mark LLM processing as complete in original chunk file
        try:
            with open(file_info["file_path"], "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            chunk_data["llm_mapping_complete"] = True
            with open(file_info["file_path"], "w", encoding="utf-8") as f:
                json.dump(chunk_data, f, indent=2, ensure_ascii=False)
            print(f"[UNIFIED-LLM] Marked {filename} as LLM mapping complete")
        except Exception as e:
            print(f"[UNIFIED-LLM] Warning: Could not mark LLM complete: {e}")
        
        llm_results["total_files_processed"] += 1
    
    # Save unified LLM results summary with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    llm_results_file = os.path.join(UNIFIED_RESULTS_DIR, f"llm_icl_results_{timestamp}.json")
    with open(llm_results_file, "w", encoding="utf-8") as f:
        json.dump(llm_results, f, indent=2, ensure_ascii=False)
    
    print(f"[UNIFIED-LLM] Completed. Processed {llm_results['total_chunks_processed']} chunks")
    return llm_results

def process_rag_retrieval(**context):
    """Process chunks with RAG retrieval using existing pattern"""
    print("[UNIFIED-RAG] Starting RAG retrieval processing...")
    
    # Load chunk preparation info (find the most recent one)
    chunk_info_files = glob.glob(os.path.join(UNIFIED_RESULTS_DIR, "chunk_preparation_info_*.json"))
    if not chunk_info_files:
        print("[UNIFIED-RAG] No chunk preparation info found")
        return {"status": "error", "message": "Could not find chunk preparation info"}
    
    # Use the most recent chunk info file
    chunk_info_file = max(chunk_info_files, key=os.path.getmtime)
    try:
        with open(chunk_info_file, "r", encoding="utf-8") as f:
            chunk_info = json.load(f)
    except Exception as e:
        print(f"[UNIFIED-RAG] Error loading chunk info: {e}")
        return {"status": "error", "message": "Could not load chunk preparation info"}
    
    if chunk_info["status"] != "ready":
        print("[UNIFIED-RAG] Chunks not ready for processing")
        return {"status": "not_ready", "message": "Chunks not ready for processing"}
    
    # Create RAG results directory
    os.makedirs(RAG_RESULTS_DIR, exist_ok=True)
    
    # Process each file using existing RAG logic
    total_chunks_processed = 0
    total_files_processed = 0
    
    for file_info in chunk_info["ready_files"]:
        try:
            print(f"[UNIFIED-RAG] Processing file: {file_info['base_name']}")
            
            base_name = file_info["base_name"]
            
            # Prepare results structure (matching existing RAG DAG format)
            # Extract source identifier from chunk file for proper naming
            chunk_filename = os.path.basename(file_info["file_path"])
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                rag_output_filename = f"rag_chunks_normalized_{source_identifier}.json"
            else:
                # Fallback for other naming patterns
                base_name = os.path.splitext(chunk_filename)[0]
                rag_output_filename = f"rag_{base_name}.json"
            
            results = {
                "original_chunk_file": file_info["file_path"],
                "processing_timestamp": datetime.now().isoformat(),
                "total_chunks": file_info["chunk_count"],
                "processed_chunks": 0,
                "rag_processing_complete": False,
                "rag_results": [],
            }
            
            # Process each chunk
            for chunk in file_info["chunks"]:
                chunk_id = chunk.get("chunk_id", 0)
                chunk_text = chunk.get("text", "")
                
                if not chunk_text.strip():
                    print(f"[UNIFIED-RAG] Skipping empty chunk {chunk_id}")
                    continue
                
                try:
                    # Query RAG API (same as existing RAG DAG)
                    payload = {
                        "query": chunk_text,
                        "top_k": 5,  # Get top 5 most relevant MITRE techniques
                    }
                    
                    print(f"[UNIFIED-RAG] Querying API for chunk {chunk_id}...")
                    response = requests.post(RAG_API_URL, json=payload, timeout=1000)
                    
                    if response.status_code == 200:
                        rag_response = response.json()
                        
                        # Store chunk result (matching existing format)
                        chunk_result = {
                            "chunk_id": chunk_id,
                            "original_text": chunk_text,
                            "mitre_techniques": rag_response,
                            "retrieval_timestamp": datetime.now().isoformat(),
                            "status": "success",
                            "llm_mapping_available": False,  # Will be updated later
                        }
                        
                        results["rag_results"].append(chunk_result)
                        results["processed_chunks"] += 1
                        total_chunks_processed += 1
                        
                        print(f"[UNIFIED-RAG] Chunk {chunk_id}: Found {len(rag_response)} MITRE techniques")
                        
                    else:
                        print(f"[UNIFIED-RAG] API error for chunk {chunk_id}: {response.status_code}")
                        error_result = {
                            "chunk_id": chunk_id,
                            "original_text": chunk_text,
                            "mitre_techniques": [],
                            "retrieval_timestamp": datetime.now().isoformat(),
                            "status": "api_error",
                            "error": f"HTTP {response.status_code}: {response.text}",
                            "llm_mapping_available": False,
                        }
                        results["rag_results"].append(error_result)
                        
                except requests.exceptions.RequestException as e:
                    print(f"[UNIFIED-RAG] Network error for chunk {chunk_id}: {e}")
                    error_result = {
                        "chunk_id": chunk_id,
                        "original_text": chunk_text,
                        "mitre_techniques": [],
                        "retrieval_timestamp": datetime.now().isoformat(),
                        "status": "network_error",
                        "error": str(e),
                        "llm_mapping_available": False,
                    }
                    results["rag_results"].append(error_result)
                    
                except Exception as e:
                    print(f"[UNIFIED-RAG] Error processing chunk {chunk_id}: {e}")
                    error_result = {
                        "chunk_id": chunk_id,
                        "original_text": chunk_text,
                        "mitre_techniques": [],
                        "retrieval_timestamp": datetime.now().isoformat(),
                        "status": "processing_error",
                        "error": str(e),
                        "llm_mapping_available": False,
                    }
                    results["rag_results"].append(error_result)
                
                # Small delay to avoid overwhelming the API (same as existing)
                time.sleep(0.1)
            
            # Mark RAG processing as complete (matching existing format)
            results["rag_processing_complete"] = True
            results["processing_notes"] = {
                "llm_mapping_complete": False,  # Will be updated by LLM task
                "processed_all_available_chunks": True,
                "can_reprocess_after_llm": False
            }
            
            # Save results for this chunk file (same format as existing RAG DAG)
            output_file = os.path.join(RAG_RESULTS_DIR, rag_output_filename)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"[UNIFIED-RAG] Saved results to: {output_file}")
            print(f"[UNIFIED-RAG] Processed {results['processed_chunks']}/{results['total_chunks']} chunks from {file_info['file_path']}")
            total_files_processed += 1
            
        except Exception as e:
            print(f"[UNIFIED-RAG] Failed to process chunk file {file_info['file_path']}: {e}")
            continue
    
    # Save unified RAG results summary
    rag_results = {
        "processing_timestamp": datetime.now().isoformat(),
        "total_files_processed": total_files_processed,
        "total_chunks_processed": total_chunks_processed,
        "output_directory": RAG_RESULTS_DIR,
        "status": "completed",
    }
    
    # Save unified RAG results summary with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    rag_results_file = os.path.join(UNIFIED_RESULTS_DIR, f"rag_retrieval_results_{timestamp}.json")
    with open(rag_results_file, "w", encoding="utf-8") as f:
        json.dump(rag_results, f, indent=2, ensure_ascii=False)
    
    print(f"[UNIFIED-RAG] Completed. Processed {total_chunks_processed} chunks")
    return rag_results

def run_judge_validation(**context):
    """Run LLM-as-a-Judge validation using existing system"""
    print("[UNIFIED-JUDGE] Starting LLM-as-a-Judge validation...")
    
    # Create judge results directory
    os.makedirs(JUDGE_RESULTS_DIR, exist_ok=True)
    
    # Import existing judge components
    try:
        sys.path.append("/opt/project/llm_as_a_judge")
        from core.technique_validator import TechniqueValidator
        
        validator = TechniqueValidator(api_key=GEMINI_API_KEY)
        print("[UNIFIED-JUDGE] Using existing TechniqueValidator")
    except ImportError:
        print("[UNIFIED-JUDGE] TechniqueValidator not available")
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
                
            # Check if corresponding RAG results exist
            chunk_filename = os.path.basename(chunk_file)
            source_identifier = None
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                rag_result_file = os.path.join(RAG_RESULTS_DIR, f"rag_chunks_normalized_{source_identifier}.json")
                base_name = f"chunks_normalized_{source_identifier}"
            else:
                # Fallback for other naming patterns
                base_name = os.path.splitext(chunk_filename)[0]
                rag_result_file = os.path.join(RAG_RESULTS_DIR, f"rag_{base_name}.json")
            
            if not os.path.exists(rag_result_file):
                continue
                
            # Check if RAG processing is complete
            with open(rag_result_file, "r", encoding="utf-8") as f:
                rag_data = json.load(f)
                
            if not rag_data.get("rag_processing_complete", False):
                continue
            
            # Check if LLM results exist
            chunk_ids = [str(chunk.get("chunk_id", "")) for chunk in chunk_data.get("chunks", [])]
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                llm_result_file = os.path.join(LLM_RESULTS_DIR, f"llm_chunks_normalized_{source_identifier}.json")
            else:
                # Fallback for other naming patterns
                llm_result_file = os.path.join(LLM_RESULTS_DIR, f"llm_{base_name}.json")
            
            missing_llm_results = []
            if not os.path.exists(llm_result_file):
                missing_llm_results = chunk_ids
            
            if missing_llm_results:
                continue
            
            # Check if already processed by judge
            if chunk_filename.startswith("chunks_normalized_"):
                source_identifier = chunk_filename.replace("chunks_normalized_", "").replace(".json", "")
                judge_result_file = os.path.join(JUDGE_RESULTS_DIR, f"judge_chunks_normalized_{source_identifier}.json")
            else:
                # Fallback for other naming patterns  
                judge_result_file = os.path.join(JUDGE_RESULTS_DIR, f"judge_{base_name}.json")
            
            if os.path.exists(judge_result_file):
                with open(judge_result_file, "r", encoding="utf-8") as f:
                    judge_data = json.load(f)
                    
                if judge_data.get("judge_processing_complete", False):
                    continue
            
            # File is ready for processing
            processable_files.append({
                "chunk_file": chunk_file,
                "rag_file": rag_result_file,
                "llm_file": llm_result_file, 
                "chunk_ids": chunk_ids,
                "judge_file": judge_result_file,
                "base_name": base_name,
                "source_identifier": source_identifier if source_identifier else base_name
            })
            
        except Exception as e:
            print(f"[UNIFIED-JUDGE] Error checking file {chunk_file}: {e}")
            continue
    
    if not processable_files:
        print("[UNIFIED-JUDGE] No files ready for judge processing")
        return {
            "status": "no_files",
            "processed_files": 0,
            "message": "No files ready for judge processing"
        }
    
    processed_files = 0
    total_chunks_processed = 0
    
    for file_info in processable_files:
        try:
            print(f"[UNIFIED-JUDGE] Processing file: {file_info['base_name']}")
            
            # Load required data
            chunk_data = load_file_data(file_info["chunk_file"])
            rag_data = load_file_data(file_info["rag_file"])
            
            # Load LLM results from the unified format
            llm_data = load_file_data(file_info["llm_file"])
            
            if not all([chunk_data, rag_data, llm_data]):
                print(f"[UNIFIED-JUDGE] Failed to load required data for {file_info['base_name']}")
                continue
            
            # Prepare validation data in the format expected by existing judge
            chunks = chunk_data.get("chunks", [])
            rag_results = {str(r.get("chunk_id")): r.get("mitre_techniques", []) for r in rag_data.get("rag_results", [])}
            
            # Extract LLM results by chunk_id
            llm_results_by_chunk = {}
            for mapping in llm_data.get("mappings", []):
                chunk_id = str(mapping.get("chunk_id", ""))
                llm_results_by_chunk[chunk_id] = mapping.get("mitre_techniques", [])
            
            # Prepare validation input
            validation_chunks = []
            rag_results_list = []
            llm_results_list = []
            
            for chunk in chunks:
                chunk_id = str(chunk.get("chunk_id", ""))
                
                if chunk_id in rag_results and chunk_id in llm_results_by_chunk:
                    validation_chunks.append(chunk)
                    rag_results_list.append(rag_results[chunk_id])
                    llm_results_list.append(llm_results_by_chunk[chunk_id])
            
            if not validation_chunks:
                print(f"[UNIFIED-JUDGE] No matching chunks found for {file_info['base_name']}")
                continue
            
            # Run validation using existing judge
            print(f"[UNIFIED-JUDGE] Running validation on {len(validation_chunks)} chunks...")
            results = validator.batch_validate(
                chunks=validation_chunks,
                rag_results_list=rag_results_list,
                llm_results_list=llm_results_list,
            )
            
            # Prepare output structure 
            output_results = {
                "original_chunk_file": file_info["chunk_file"],
                "rag_results_file": file_info["rag_file"],
                "llm_results_file": file_info["llm_file"],
                "processing_timestamp": datetime.now().isoformat(),
                "total_chunks": len(validation_chunks),
                "processed_chunks": len(results.get("validations", [])),
                "judge_processing_complete": True,
                "validation_results": results,
            }
            
            if file_info["source_identifier"].startswith("chunks_normalized_"):
                judge_output_filename = f"judge_{file_info['source_identifier']}.json"
            else:
                judge_output_filename = f"judge_chunks_normalized_{file_info['source_identifier']}.json"
            judge_output_file = os.path.join(JUDGE_RESULTS_DIR, judge_output_filename)
            with open(judge_output_file, "w", encoding="utf-8") as f:
                json.dump(output_results, f, indent=2, ensure_ascii=False)
            
            print(f"[UNIFIED-JUDGE] Saved judge results to: {judge_output_file}")
            print(f"[UNIFIED-JUDGE] Processed {output_results['processed_chunks']}/{output_results['total_chunks']} chunks")
            
            processed_files += 1
            total_chunks_processed += output_results['processed_chunks']
            
        except Exception as e:
            print(f"[UNIFIED-JUDGE] Error processing file {file_info['base_name']}: {e}")
            
            # Create error result file
            if file_info["source_identifier"].startswith("chunks_normalized_"):
                error_output_filename = f"judge_{file_info['source_identifier']}.json"
            else:
                error_output_filename = f"judge_chunks_normalized_{file_info['source_identifier']}.json"
            judge_output_file = os.path.join(JUDGE_RESULTS_DIR, error_output_filename)
            error_result = {
                "original_chunk_file": file_info["chunk_file"],
                "processing_timestamp": datetime.now().isoformat(),
                "judge_processing_complete": False,
                "error": str(e),
                "status": "error"
            }
            
            with open(judge_output_file, "w", encoding="utf-8") as f:
                json.dump(error_result, f, indent=2, ensure_ascii=False)
            
            continue
    
    # Save unified judge results summary
    judge_results = {
        "processing_timestamp": datetime.now().isoformat(),
        "total_files_processed": processed_files,
        "total_chunks_validated": total_chunks_processed,
        "output_directory": JUDGE_RESULTS_DIR,
        "status": "completed",
    }
    
    # Save unified judge results summary with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    judge_results_file = os.path.join(UNIFIED_RESULTS_DIR, f"judge_validation_results_{timestamp}.json")
    with open(judge_results_file, "w", encoding="utf-8") as f:
        json.dump(judge_results, f, indent=2, ensure_ascii=False)
    
    print(f"[UNIFIED-JUDGE] Completed. Validated {total_chunks_processed} chunks")
    return judge_results

def load_file_data(file_path: str) -> Dict:
    """Load and parse JSON data from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[UNIFIED-JUDGE] Error loading file {file_path}: {e}")
        return {}

def generate_unified_results(**context):
    """Generate final unified analysis results and save to database"""
    print("[UNIFIED-FINAL] Generating unified analysis results...")
    
    # Load all results using pattern matching to find the most recent files
    try:
        # Find the most recent files for each type
        file_patterns = [
            ("chunk_preparation_info_*.json", "chunk_info"),
            ("llm_icl_results_*.json", "llm_results"),
            ("rag_retrieval_results_*.json", "rag_results"),
            ("judge_validation_results_*.json", "judge_results")
        ]
        
        results = {}
        for pattern, key in file_patterns:
            matching_files = glob.glob(os.path.join(UNIFIED_RESULTS_DIR, pattern))
            if not matching_files:
                print(f"[UNIFIED-FINAL] No files found for pattern: {pattern}")
                return {"status": "error", "message": f"No files found for pattern: {pattern}"}
            
            # Use the most recent file
            latest_file = max(matching_files, key=os.path.getmtime)
            with open(latest_file, "r", encoding="utf-8") as f:
                results[key] = json.load(f)
            print(f"[UNIFIED-FINAL] Loaded {key} from: {os.path.basename(latest_file)}")
        
    except Exception as e:
        print(f"[UNIFIED-FINAL] Error loading results: {e}")
        return {"status": "error", "message": "Could not load analysis results"}
    
    # Generate comprehensive summary with DAG execution info
    dag_run = context.get('dag_run')
    execution_date = dag_run.execution_date if dag_run else datetime.now()
    dag_run_id = dag_run.run_id if dag_run else 'manual_test'
    
    # Save final unified results to file with meaningful timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    final_results_filename = f"unified_analysis_results_{dag_run_id}_{timestamp}.json"
    final_results_file = os.path.join(UNIFIED_RESULTS_DIR, final_results_filename)
    
    final_results = {
        "analysis_metadata": {
            "dag_id": "unified_llm_analysis_dag",
            "dag_run_id": dag_run_id,
            "execution_date": execution_date.isoformat(),
            "processing_timestamp": datetime.now().isoformat(),
            "total_files_processed": results["judge_results"]["total_files_processed"],
            "total_chunks_analyzed": results["judge_results"]["total_chunks_validated"],
            "pipeline_components": ["LLM_ICL", "RAG_Retrieval", "Judge_Validation"],
            "results_filename": final_results_filename
        },
        "processing_summary": {
            "llm_icl_chunks": results["llm_results"]["total_chunks_processed"],
            "rag_retrieval_chunks": results["rag_results"]["total_chunks_processed"], 
            "judge_validated_chunks": results["judge_results"]["total_chunks_validated"],
            "success_rate": f"{(results['judge_results']['total_chunks_validated'] / results['chunk_info']['total_chunks'] * 100):.1f}%"
        },
        "component_results": {
            "chunk_preparation": results["chunk_info"],
            "llm_icl_processing": results["llm_results"],
            "rag_retrieval": results["rag_results"],
            "judge_validation": results["judge_results"]
        }
    }
    
    with open(final_results_file, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    # Save to PostgreSQL database using modular function
    try:
        db_result = save_cti_results(
            final_results=final_results,
            dag_run_id=dag_run_id,
            execution_date=execution_date
        )
        
        if db_result.get("status") == "success":
            print(f"[UNIFIED-FINAL] Successfully saved to database with ID: {db_result.get('unified_analysis_id')}")
        else:
            print(f"[UNIFIED-FINAL] Database save failed: {db_result.get('message')}")
            
    except Exception as e:
        print(f"[UNIFIED-FINAL] Warning: Could not save to database: {e}")
    
    print(f"[UNIFIED-FINAL] Generated unified results for {final_results['analysis_metadata']['total_chunks_analyzed']} chunks")
    return final_results


# ================================
# TASK DEFINITIONS
# ================================

start_task = DummyOperator(
    task_id="start_unified_analysis",
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

# Final results generation
generate_results_task = PythonOperator(
    task_id="generate_unified_results",
    python_callable=generate_unified_results,
    dag=dag,
)

completion_task = DummyOperator(
    task_id="unified_analysis_complete",
    dag=dag,
)


# ================================
# TASK DEPENDENCIES
# ================================

# Sequential: start → prepare chunks
start_task >> prepare_chunks_task

# Parallel: chunks → (llm_icl + rag_retrieval) → wait
prepare_chunks_task >> [llm_icl_task, rag_retrieval_task] >> wait_for_parallel

# Sequential: wait → judge → results → complete
wait_for_parallel >> judge_validation_task >> generate_results_task >> completion_task
