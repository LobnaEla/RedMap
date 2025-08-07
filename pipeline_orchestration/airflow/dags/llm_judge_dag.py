"""
LLM as a Judge DAG for Cross-Validation of MITRE Technique Mappings

This DAG processes chunks, LLM results, and RAG results through the LLM-as-a-Judge
pipeline for cross-validation and consensus-based technique validation.
"""

from airflow import DAG
from airflow.operators.python import PythonOperator, get_current_context
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os
import sys
import json
import glob
from typing import Dict, List, Optional

sys.path.append("/opt/project")
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
RAG_RESULTS_DIR = os.path.join(DATA_DIR, "rag_results")
LLM_RESULTS_DIR = os.path.join(DATA_DIR, "llm_results")
JUDGE_RESULTS_DIR = os.path.join(DATA_DIR, "judge_results")

# === DAG Configuration ===
default_args = {
    "owner": "cti-llm-judge",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

dag = DAG(
    "llm_judge_dag",  # Changed to match n8n workflow expectation
    default_args=default_args,
    description="LLM-as-a-Judge pipeline",
    schedule_interval=None,
    catchup=False,
    max_active_runs=1,
    tags=["cti", "llm", "judge", "validation"],
)


def get_processable_files() -> List[Dict]:
    """
    Get files that are ready for LLM Judge processing and haven't been processed yet
    """
    print("[JUDGE] Identifying processable files...")
    
    # Get all chunk files
    chunk_files = load_chunk_files(CHUNKS_DIR)
    processable = []
    
    for chunk_file in chunk_files:
        try:
            # Check if chunk file is complete
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
            
            if not chunk_data.get("preprocessing_complete", False):
                print(f"[JUDGE] Skipping {chunk_file} - preprocessing not complete")
                continue
                
            if not chunk_data.get("llm_mapping_complete", False):
                print(f"[JUDGE] Skipping {chunk_file} - LLM mapping not complete")
                continue
            
            # Check if corresponding RAG results exist
            base_name = os.path.splitext(os.path.basename(chunk_file))[0]
            rag_result_file = os.path.join(RAG_RESULTS_DIR, f"rag_{base_name}.json")
            
            if not os.path.exists(rag_result_file):
                print(f"[JUDGE] Skipping {chunk_file} - no RAG results found")
                continue
                
            # Check if RAG processing is complete
            with open(rag_result_file, "r", encoding="utf-8") as f:
                rag_data = json.load(f)
                
            if not rag_data.get("rag_processing_complete", False):
                print(f"[JUDGE] Skipping {chunk_file} - RAG processing not complete")
                continue
            
            # Check if corresponding LLM results exist for all chunks
            chunk_ids = [str(chunk.get("chunk_id", "")) for chunk in chunk_data.get("chunks", [])]
            missing_llm_results = []
            available_llm_files = []
            
            for chunk_id in chunk_ids:
                llm_result_file = os.path.join(LLM_RESULTS_DIR, f"{chunk_id}.json")
                if not os.path.exists(llm_result_file):
                    missing_llm_results.append(chunk_id)
                else:
                    available_llm_files.append(chunk_id)
            
            # Also check for "unknown.json" which might be chunk 0
            unknown_file = os.path.join(LLM_RESULTS_DIR, "unknown.json")
            if os.path.exists(unknown_file) and "0" in missing_llm_results:
                # Check if unknown.json corresponds to chunk 0 by comparing content
                try:
                    unknown_data = load_file_data(unknown_file)
                    chunk_0_text = ""
                    for chunk in chunk_data.get("chunks", []):
                        if str(chunk.get("chunk_id")) == "0":
                            chunk_0_text = chunk.get("text", "")
                            break
                    
                    if unknown_data.get("original_text", "") == chunk_0_text:
                        # unknown.json is chunk 0
                        missing_llm_results.remove("0")
                        available_llm_files.append("0")
                        print(f"[JUDGE] Found chunk 0 data in unknown.json for {chunk_file}")
                except Exception as e:
                    print(f"[JUDGE] Error checking unknown.json: {e}")
            
            if missing_llm_results:
                print(f"[JUDGE] Skipping {chunk_file} - missing LLM results for chunks: {missing_llm_results}")
                print(f"[JUDGE] Available LLM results for chunks: {available_llm_files}")
                continue
            
            # Check if already processed by judge
            judge_result_file = os.path.join(JUDGE_RESULTS_DIR, f"judge_{base_name}.json")
            
            if os.path.exists(judge_result_file):
                with open(judge_result_file, "r", encoding="utf-8") as f:
                    judge_data = json.load(f)
                    
                if judge_data.get("judge_processing_complete", False):
                    print(f"[JUDGE] Skipping {chunk_file} - already processed by judge")
                    continue
            
            # File is ready for processing
            processable.append({
                "chunk_file": chunk_file,
                "rag_file": rag_result_file,
                "chunk_ids": chunk_ids,  # Store chunk IDs for LLM result lookup
                "judge_file": judge_result_file,
                "base_name": base_name
            })
            
        except Exception as e:
            print(f"[JUDGE] Error checking file {chunk_file}: {e}")
            continue
    
    print(f"[JUDGE] Found {len(processable)} files ready for judge processing")
    return processable


def load_file_data(file_path: str) -> Dict:
    """Load and parse JSON data from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[JUDGE] Error loading file {file_path}: {e}")
        return {}


def prepare_judge_input(file_info: Dict) -> Optional[Dict]:
    """
    Prepare input data for judge processing from chunk, LLM and RAG results
    """
    try:
        # Load chunk and RAG data
        chunk_data = load_file_data(file_info["chunk_file"])
        rag_data = load_file_data(file_info["rag_file"])
        
        if not all([chunk_data, rag_data]):
            print(f"[JUDGE] Failed to load required data for {file_info['base_name']}")
            return None
        
        # Load individual LLM results for each chunk
        llm_results_by_chunk = {}
        for chunk_id in file_info["chunk_ids"]:
            llm_result_file = os.path.join(LLM_RESULTS_DIR, f"{chunk_id}.json")
            
            # If the standard file doesn't exist, try "unknown.json" for chunk 0
            if not os.path.exists(llm_result_file) and chunk_id == "0":
                unknown_file = os.path.join(LLM_RESULTS_DIR, "unknown.json")
                if os.path.exists(unknown_file):
                    llm_result_file = unknown_file
            
            llm_result_data = load_file_data(llm_result_file)
            if llm_result_data:
                llm_results_by_chunk[chunk_id] = llm_result_data.get("mitre_techniques", [])
                print(f"[JUDGE] Loaded LLM results for chunk {chunk_id}: {len(llm_result_data.get('mitre_techniques', []))} techniques")
        
        # Extract chunks and results
        chunks = chunk_data.get("chunks", [])
        rag_results = {str(r.get("chunk_id")): r.get("mitre_techniques", []) for r in rag_data.get("rag_results", [])}
        
        print(f"[JUDGE] Found {len(chunks)} chunks to process")
        print(f"[JUDGE] RAG results available for chunks: {list(rag_results.keys())}")
        print(f"[JUDGE] LLM results available for chunks: {list(llm_results_by_chunk.keys())}")
        
        # Prepare validation data
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
            print(f"[JUDGE] No matching chunks found for {file_info['base_name']}")
            return None
            
        return {
            "chunks": validation_chunks,
            "rag_results_list": rag_results_list,
            "llm_results_list": llm_results_list,
            "file_info": file_info
        }
        
    except Exception as e:
        print(f"[JUDGE] Error preparing judge input for {file_info['base_name']}: {e}")
        return None


def run_judge_validation():
    """
    Main function to run LLM-as-a-Judge validation
    """
    print("[JUDGE] Starting LLM-as-a-Judge validation...")
    
    # Ensure output directory exists
    os.makedirs(JUDGE_RESULTS_DIR, exist_ok=True)
    
    # Get files ready for processing
    processable_files = get_processable_files()
    
    if not processable_files:
        print("[JUDGE] No files ready for judge processing")
        return {
            "status": "no_files",
            "processed_files": 0,
            "message": "No files ready for judge processing"
        }
    
    # Import LLM-as-a-Judge components
    try:
        from llm_as_a_judge import TechniqueValidator, save_judge_results
        
        # Get API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
            
        validator = TechniqueValidator(api_key=api_key)
        
    except ImportError as e:
        print(f"[JUDGE] Failed to import LLM-as-a-Judge components: {e}")
        raise e
    except Exception as e:
        print(f"[JUDGE] Failed to initialize validator: {e}")
        raise e
    
    processed_files = 0
    total_chunks_processed = 0
    
    for file_info in processable_files:
        try:
            print(f"[JUDGE] Processing file: {file_info['base_name']}")
            
            # Prepare input data
            judge_input = prepare_judge_input(file_info)
            if not judge_input:
                continue
            
            # Run validation
            print(f"[JUDGE] Running validation on {len(judge_input['chunks'])} chunks...")
            results = validator.batch_validate(
                chunks=judge_input["chunks"],
                rag_results_list=judge_input["rag_results_list"],
                llm_results_list=judge_input["llm_results_list"],
            )
            
            # Prepare output structure
            output_results = {
                "original_chunk_file": file_info["chunk_file"],
                "rag_results_file": file_info["rag_file"],
                "llm_results_chunks": file_info["chunk_ids"],  # Store chunk IDs used for LLM results
                "processing_timestamp": datetime.now().isoformat(),
                "total_chunks": len(judge_input["chunks"]),
                "processed_chunks": len(results.get("validations", [])),
                "judge_processing_complete": True,
                "validation_results": results,
            }
            
            # Save results with llm_ prefix as requested
            judge_output_file = os.path.join(JUDGE_RESULTS_DIR, f"llm_{file_info['base_name']}.json")
            with open(judge_output_file, "w", encoding="utf-8") as f:
                json.dump(output_results, f, indent=2, ensure_ascii=False)
            
            print(f"[JUDGE] Saved judge results to: {judge_output_file}")
            print(f"[JUDGE] Processed {output_results['processed_chunks']}/{output_results['total_chunks']} chunks")
            
            processed_files += 1
            total_chunks_processed += output_results['processed_chunks']
            
        except Exception as e:
            print(f"[JUDGE] Error processing file {file_info['base_name']}: {e}")
            
            # Create error result file with llm_ prefix
            judge_output_file = os.path.join(JUDGE_RESULTS_DIR, f"llm_{file_info['base_name']}.json")
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
    
    print(f"[JUDGE] Judge validation complete!")
    print(f"[JUDGE] Files processed: {processed_files}/{len(processable_files)}")
    print(f"[JUDGE] Total chunks processed: {total_chunks_processed}")
    print(f"[JUDGE] Results saved in: {JUDGE_RESULTS_DIR}")
    
    return {
        "status": "completed",
        "processed_files": processed_files,
        "total_files": len(processable_files),
        "total_chunks_processed": total_chunks_processed,
        "output_directory": JUDGE_RESULTS_DIR,
    }


def validate_judge_results():
    """
    Validate judge processing results
    """
    print("[JUDGE] Validating judge results...")
    
    judge_files = glob.glob(os.path.join(JUDGE_RESULTS_DIR, "llm_*.json"))
    
    total_files = len(judge_files)
    successful_files = 0
    total_chunks_validated = 0
    
    for judge_file in judge_files:
        try:
            with open(judge_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("judge_processing_complete", False):
                successful_files += 1
                total_chunks_validated += data.get("processed_chunks", 0)
                
        except Exception as e:
            print(f"[JUDGE] Error validating {judge_file}: {e}")
    
    validation_results = {
        "total_files": total_files,
        "successful_files": successful_files,
        "failed_files": total_files - successful_files,
        "total_chunks_validated": total_chunks_validated,
        "success_rate": (successful_files / total_files) * 100 if total_files > 0 else 0
    }
    
    print(f"[JUDGE] Validation complete:")
    print(f"[JUDGE] Successful files: {successful_files}/{total_files}")
    print(f"[JUDGE] Success rate: {validation_results['success_rate']:.1f}%")
    print(f"[JUDGE] Total chunks validated: {total_chunks_validated}")
    
    return validation_results


def judge_completion():
    """Final completion task"""
    return {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "message": "LLM-as-a-Judge processing pipeline finished successfully",
    }


def extract_webhook_trigger_context():
    """Extract webhook trigger context from DAG configuration"""
    try:
        context = get_current_context()
        dag_run = context['dag_run']
        dag_config = dag_run.conf or {}
        
        print(f"[Judge Webhook] DAG Run ID: {dag_run.dag_id}")
        print(f"[Judge Webhook] Execution Date: {dag_run.execution_date}")
        print(f"[Judge Webhook] Triggered by: {dag_config.get('triggered_by', 'unknown')}")
        print(f"[Judge Webhook] Configuration: {json.dumps(dag_config, indent=2)}")
        
        # Check if this was triggered by the n8n webhook orchestrator
        triggered_by = dag_config.get('triggered_by', '')
        
        if 'n8n' in triggered_by.lower() or 'webhook' in triggered_by.lower():
            print("[Judge Webhook] ✅ Detected webhook trigger from orchestrator")
            
            # Extract completion context
            llm_completion = dag_config.get('llm_dag_completion', {})
            rag_completion = dag_config.get('rag_dag_completion', {})
            
            if llm_completion and rag_completion:
                print(f"[Judge Webhook] LLM completed: {llm_completion.get('completion_time')}")
                print(f"[Judge Webhook] RAG completed: {rag_completion.get('completion_time')}")
                
                # Save trigger context for use by subsequent tasks
                trigger_context = {
                    "trigger_source": "webhook_orchestrator",
                    "trigger_timestamp": datetime.now().isoformat(),
                    "llm_dag_info": llm_completion,
                    "rag_dag_info": rag_completion,
                    "orchestrator_config": dag_config
                }
                
                # Save to judge results directory
                os.makedirs(JUDGE_RESULTS_DIR, exist_ok=True)
                context_file = os.path.join(JUDGE_RESULTS_DIR, f"webhook_context_{dag_run.dag_id}.json")
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump(trigger_context, f, indent=2, ensure_ascii=False)
                    
                print(f"[Judge Webhook] Trigger context saved: {context_file}")
                
                return {
                    "status": "webhook_triggered",
                    "context_saved": True,
                    "context_file": context_file,
                    "llm_dag_run": llm_completion.get('dag_run_id'),
                    "rag_dag_run": rag_completion.get('dag_run_id')
                }
            else:
                print("[Judge Webhook] ⚠️ Incomplete webhook context - missing completion data")
                return {
                    "status": "incomplete_webhook_context",
                    "context_saved": False,
                    "message": "Missing LLM or RAG completion data"
                }
        else:
            print("[Judge Webhook] Standard DAG trigger (not from webhook orchestrator)")
            return {
                "status": "standard_trigger",
                "context_saved": False,
                "message": "Not triggered by webhook orchestrator"
            }
            
    except Exception as e:
        print(f"[Judge Webhook] Error extracting webhook context: {str(e)}")
        return {
            "status": "error",
            "context_saved": False,
            "error": str(e)
        }


# === Task Definitions ===
start_task = DummyOperator(
    task_id="start_judge_processing",
    dag=dag,
)

webhook_context_task = PythonOperator(
    task_id="extract_webhook_context",
    python_callable=extract_webhook_trigger_context,
    dag=dag,
)

judge_processing_task = PythonOperator(
    task_id="run_judge_validation",
    python_callable=run_judge_validation,
    dag=dag,
)

validation_task = PythonOperator(
    task_id="validate_judge_results",
    python_callable=validate_judge_results,
    dag=dag,
)

end_task = PythonOperator(
    task_id="judge_completion",
    python_callable=judge_completion,
    dag=dag,
)

# === Task Dependencies ===
start_task >> webhook_context_task >> judge_processing_task >> validation_task >> end_task
