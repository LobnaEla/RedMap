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
    """Save validated techniques from Judge results to database"""
    logger.info("[DB-SAVE] Starting database save process")
    
    try:
        import psycopg2
        import json
        from datetime import datetime
        
        # Database connection parameters from environment variables
        db_params = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'airflow'), 
            'user': os.getenv('POSTGRES_USER', 'airflow'),
            'password': os.getenv('POSTGRES_PASSWORD', 'airflow'),
            'port': int(os.getenv('POSTGRES_PORT', '5432'))
        }
        
        logger.info(f"[DB-SAVE] Connecting to PostgreSQL with user: {db_params['user']}")
        
        # Get DAG run information - convert to native Python types
        dag_run = context.get('dag_run')
        dag_run_id = dag_run.run_id if dag_run else 'manual_run'
        
        execution_date_raw = context.get('execution_date')
        if execution_date_raw:
            # Convert Airflow datetime to native Python datetime
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
        
        # Process judge results and extract validated techniques
        validation_results = []
        pipeline_summary = {
            "total_chunks_processed": 0,
            "files_processed": []
        }
        
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
                
                for validation in validations:
                    chunk_id = validation.get("chunk_id")
                    original_chunk = validation.get("original_chunk", "")
                    iocs = validation.get("iocs", "")
                    
                    # Get original techniques
                    llm_techniques = validation.get("llm_techniques", [])
                    ras_techniques = validation.get("ras_techniques", [])
                    
                    # Get judge results
                    judge_result = validation.get("judge_result", {})
                    validated_techniques = judge_result.get("validated_techniques", [])
                    rejected_techniques = judge_result.get("rejected_techniques", [])
                    
                    # Create simplified result record
                    result_record = {
                        "dag_run_id": dag_run_id,
                        "execution_date": execution_date,
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
        
        # Connect to PostgreSQL directly
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                logger.info("[DB-SAVE] Connected to PostgreSQL successfully")
                
                # Ensure schema exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS cti_results;")
                
                # Create main validation results table
                create_validation_table_sql = """
                CREATE TABLE IF NOT EXISTS cti_results.technique_validations (
                    id SERIAL PRIMARY KEY,
                    dag_run_id VARCHAR(255),
                    execution_date TIMESTAMP,
                    source_file VARCHAR(255),
                    chunk_id INTEGER,
                    original_chunk TEXT,
                    iocs TEXT,
                    llm_techniques TEXT[],
                    ras_techniques TEXT[],
                    validated_techniques TEXT[],
                    rejected_techniques TEXT[],
                    success BOOLEAN,
                    chunk_timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cur.execute(create_validation_table_sql)
                
                # Create simplified pipeline summary table
                create_summary_table_sql = """
                CREATE TABLE IF NOT EXISTS cti_results.pipeline_summary (
                    id SERIAL PRIMARY KEY,
                    dag_run_id VARCHAR(255),
                    execution_date TIMESTAMP,
                    total_chunks_processed INTEGER,
                    files_processed TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cur.execute(create_summary_table_sql)
                
                # Insert validation results
                if validation_results:
                    insert_validation_sql = """
                    INSERT INTO cti_results.technique_validations (
                        dag_run_id, execution_date, source_file, chunk_id, original_chunk,
                        iocs, llm_techniques, ras_techniques, validated_techniques, rejected_techniques,
                        success, chunk_timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    for result in validation_results:
                        # Convert timestamp strings to datetime objects if they exist
                        chunk_timestamp = None
                        
                        if result.get("timestamp"):
                            try:
                                chunk_timestamp = datetime.fromisoformat(result["timestamp"].replace('Z', '+00:00'))
                            except:
                                pass
                        
                        cur.execute(insert_validation_sql, (
                            result["dag_run_id"],
                            result["execution_date"],
                            result["source_file"],
                            result["chunk_id"],
                            result["original_chunk"],
                            result["iocs"],
                            result["llm_techniques"],
                            result["ras_techniques"],
                            result["validated_techniques"],
                            result["rejected_techniques"],
                            result["success"],
                            chunk_timestamp
                        ))
                    
                    logger.info(f"[DB-SAVE] Inserted {len(validation_results)} validation records")
                
                # Insert simplified pipeline summary
                insert_summary_sql = """
                INSERT INTO cti_results.pipeline_summary (
                    dag_run_id, execution_date, total_chunks_processed, files_processed
                ) VALUES (%s, %s, %s, %s)
                RETURNING id;
                """
                
                cur.execute(insert_summary_sql, (
                    dag_run_id,
                    execution_date,
                    pipeline_summary["total_chunks_processed"],
                    pipeline_summary["files_processed"]
                ))
                
                summary_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"[DB-SAVE] Successfully saved pipeline results to database")
                logger.info(f"[DB-SAVE] Pipeline Summary ID: {summary_id}")
                logger.info(f"[DB-SAVE] Processed {pipeline_summary['total_chunks_processed']} chunks")
                
                return {
                    "status": "completed",
                    "summary_id": summary_id,
                    "validation_records": len(validation_results),
                    "pipeline_summary": pipeline_summary
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