import logging
from datetime import datetime, timedelta
from pathlib import Path
import glob
import json
import sys
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Add the scripts directory to the path to import db_manager
sys.path.insert(0, '/opt/airflow/scripts')
from db_manager import CTIResultsDB

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_llm_results_to_database(**context):
    """Save validated techniques from Judge results to database in STIX format"""
    logger.info("[DB-SAVE] Starting STIX format database save process")
    
    try:
        # Get DAG run information
        dag_run = context.get('dag_run')
        dag_run_id = dag_run.run_id if dag_run else 'manual_run'
        
        execution_date_raw = context.get('execution_date')
        if execution_date_raw:
            execution_date = datetime.fromisoformat(str(execution_date_raw).replace('+00:00', ''))
        else:
            execution_date = datetime.now()
        
        # Use the same path structure as the LLM pipeline
        base_project_path = Path("/opt/project/cti_pipeline")
        data_dir = base_project_path / "data"
        llm_data_path = data_dir / "llm"
        
        logger.info(f"[DB-SAVE] Base project path: {base_project_path}")
        logger.info(f"[DB-SAVE] LLM data path: {llm_data_path}")
        
        # Check Judge results
        judge_path = llm_data_path / "judge"
        judge_files = list(judge_path.glob("*.json")) if judge_path.exists() else []
        logger.info(f"[DB-SAVE] Found {len(judge_files)} Judge result files to process")
        
        if not judge_files:
            logger.warning(f"[DB-SAVE] No judge results found to process")
            return {"status": "no_data", "message": "No judge results found"}
        
        # Process judge results and create unified results structure
        validation_results = []
        pipeline_summary = {
            "total_chunks_processed": 0,
            "files_processed": [],
            "success_rate": "0.0%",
            "llm_icl_chunks": 0,
            "rag_retrieval_chunks": 0,
            "judge_validated_chunks": 0
        }
        
        # Extract validated techniques for STIX format
        all_validated_techniques = set()
        
        for judge_file in judge_files:
            logger.info(f"[DB-SAVE] Processing judge file: {judge_file.name}")
            
            try:
                with open(judge_file, 'r', encoding='utf-8') as f:
                    judge_data = json.load(f)
                
                # Extract file metadata
                source_file = judge_file.name
                pipeline_summary["files_processed"].append(source_file)
                
                # Process individual validations
                validations = judge_data.get("validations", [])
                pipeline_summary["total_chunks_processed"] += len(validations)
                pipeline_summary["judge_validated_chunks"] += len(validations)
                
                for validation in validations:
                    chunk_id = validation.get("chunk_id")
                    original_chunk = validation.get("original_chunk", "")
                    iocs = validation.get("iocs", "")
                    
                    # Get original techniques
                    llm_techniques = validation.get("llm_techniques", [])
                    ras_techniques = validation.get("ras_techniques", [])
                    
                    # Get judge results - THIS IS WHERE THE VALIDATED TECHNIQUES ARE!
                    judge_result = validation.get("judge_result", {})
                    validated_techniques = judge_result.get("validated_techniques", [])
                    rejected_techniques = judge_result.get("rejected_techniques", [])
                    
                    # Add validated techniques to the global set for STIX
                    all_validated_techniques.update(validated_techniques)
                    
                    # Create simplified result record
                    result_record = {
                        "dag_run_id": dag_run_id,
                        "execution_date": execution_date.isoformat(),
                        "source_file": source_file,
                        "chunk_id": chunk_id,
                        "original_chunk": original_chunk,
                        "iocs": iocs,
                        "llm_techniques": llm_techniques,
                        "ras_techniques": ras_techniques,
                        "validated_techniques": validated_techniques,
                        "rejected_techniques": rejected_techniques,
                        "success": validation.get("success", False),
                        "timestamp": validation.get("timestamp")
                    }
                    
                    validation_results.append(result_record)
                    
            except Exception as e:
                logger.error(f"[DB-SAVE] Error processing judge file {judge_file}: {e}")
                continue
        
        logger.info(f"[DB-SAVE] Processed {len(validation_results)} validation records from {len(judge_files)} files")
        
        # Calculate success rate
        successful_validations = sum(1 for r in validation_results if r.get("success", False))
        total_validations = len(validation_results)
        success_rate = (successful_validations / total_validations * 100) if total_validations > 0 else 0
        pipeline_summary["success_rate"] = f"{success_rate:.1f}%"
        
        # Create unified results structure for STIX conversion
        final_results = {
            "analysis_metadata": {
                "dag_id": "llm_database_save",
                "processing_timestamp": datetime.now().isoformat(),
                "total_files_processed": len(judge_files),
                "total_chunks_analyzed": total_validations,
                "pipeline_components": ["llm_icl", "rag_retrieval", "judge_validation"]
            },
            "processing_summary": pipeline_summary,
            "component_results": {
                "validated_techniques": list(all_validated_techniques),
                "validation_details": validation_results
            }
        }
        
        logger.info(f"[DB-SAVE] Found {len(all_validated_techniques)} unique validated techniques: {sorted(list(all_validated_techniques))}")
        
        # Use CTIResultsDB to save in STIX format
        db = CTIResultsDB()
        result = db.save_unified_results(
            final_results=final_results,
            dag_run_id=dag_run_id,
            execution_date=execution_date
        )
        
        logger.info(f"[DB-SAVE] Successfully saved pipeline results to database in STIX format")
        logger.info(f"[DB-SAVE] Database result: {result}")
        
        return {
            "status": "completed",
            "database_result": result,
            "validation_records": len(validation_results),
            "validated_techniques": list(all_validated_techniques),
            "pipeline_summary": pipeline_summary,
            "stix_format": True
        }
            
    except Exception as e:
        logger.error(f"[DB-SAVE] Error during database save: {str(e)}")
        raise

# DAG configuration
default_args = {
    'owner': 'cti-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'llm_database_save',
    default_args=default_args,
    description='Save validated MITRE techniques from LLM Judge results to database',
    schedule_interval=None,  
    max_active_runs=1,
    catchup=False,
    tags=['llm', 'database', 'cti', 'mitre', 'validation']
)

# Save results to database - runs directly when triggered
save_to_database_task = PythonOperator(
    task_id='save_validated_techniques_to_database',
    python_callable=save_llm_results_to_database,
    dag=dag
)