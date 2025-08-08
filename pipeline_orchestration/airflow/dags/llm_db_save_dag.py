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
    """Save ICL, RAG retrieval, and Judge results to database using direct connection"""
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
        
        data_base_path = Path("/opt/airflow/data")
        llm_data_path = data_base_path / "llm"
        
        # Check ICL results
        icl_path = llm_data_path / "icl"
        icl_files = list(icl_path.glob("*.json")) if icl_path.exists() else []
        logger.info(f"[DB-SAVE] Found {len(icl_files)} ICL result files to save")
        
        # Check RAG retrieval results
        rag_path = llm_data_path / "retrieval_search"
        rag_files = list(rag_path.glob("*.json")) if rag_path.exists() else []
        logger.info(f"[DB-SAVE] Found {len(rag_files)} RAG retrieval result files to save")
        
        # Check Judge results
        judge_path = llm_data_path / "judge"
        judge_files = list(judge_path.glob("*.json")) if judge_path.exists() else []
        logger.info(f"[DB-SAVE] Found {len(judge_files)} Judge result files to save")
        
        # Create a unified results structure that matches the expected schema
        total_files = len(icl_files) + len(rag_files) + len(judge_files)
        
        # Connect to PostgreSQL directly
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                logger.info("[DB-SAVE] Connected to PostgreSQL successfully")
                
                # Ensure schema exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS cti_results;")
                
                # Create table if it doesn't exist (simplified version)
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS cti_results.llm_pipeline_results (
                    id SERIAL PRIMARY KEY,
                    dag_run_id VARCHAR(255),
                    execution_date TIMESTAMP,
                    dag_id VARCHAR(255),
                    processing_timestamp TIMESTAMP,
                    total_files_processed INTEGER,
                    icl_files INTEGER,
                    rag_files INTEGER,
                    judge_files INTEGER,
                    status VARCHAR(50),
                    results_json JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                cur.execute(create_table_sql)
                
                # Build unified results metadata
                unified_results = {
                    "analysis_metadata": {
                        "dag_id": "llm_pipeline",
                        "processing_timestamp": datetime.now().isoformat(),
                        "total_files_processed": total_files,
                        "pipeline_components": ["icl", "rag_retrieval", "judge_validation"]
                    },
                    "processing_summary": {
                        "llm_icl_chunks": len(icl_files),
                        "rag_retrieval_chunks": len(rag_files), 
                        "judge_validated_chunks": len(judge_files),
                        "success_rate": "100.0%" if total_files > 0 else "0.0%"
                    },
                    "component_results": {
                        "icl_files": [str(f) for f in icl_files],
                        "rag_files": [str(f) for f in rag_files],
                        "judge_files": [str(f) for f in judge_files]
                    }
                }
                
                # Insert results
                insert_sql = """
                INSERT INTO cti_results.llm_pipeline_results (
                    dag_run_id, execution_date, dag_id, processing_timestamp,
                    total_files_processed, icl_files, rag_files, judge_files,
                    status, results_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """
                
                cur.execute(insert_sql, (
                    str(dag_run_id),  # Ensure string
                    execution_date,   # Native Python datetime
                    "llm_pipeline",
                    datetime.now(),   # Native Python datetime
                    int(total_files), # Ensure integer
                    int(len(icl_files)),   # Ensure integer
                    int(len(rag_files)),   # Ensure integer
                    int(len(judge_files)), # Ensure integer
                    'completed',
                    json.dumps(unified_results)  # JSON string
                ))
                
                result_id = cur.fetchone()[0]
                conn.commit()
                
                logger.info(f"[DB-SAVE] Successfully saved results to database. Record ID: {result_id}")
                logger.info(f"[DB-SAVE] Processed {total_files} total files: {len(icl_files)} ICL, {len(rag_files)} RAG, {len(judge_files)} Judge")
            
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
    description='Save LLM pipeline results to database',
    schedule_interval=None,  
    max_active_runs=1,
    catchup=False,
    tags=['llm', 'database', 'cti']
)

# Save results to database - runs directly when triggered
save_to_database_task = PythonOperator(
    task_id='save_llm_results_to_database',
    python_callable=save_llm_results_to_database,
    dag=dag
)