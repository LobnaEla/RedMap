from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import os
import sys

sys.path.append("/opt/project")
import importlib.util
shared_spec = importlib.util.spec_from_file_location("shared", "/opt/project/airflow/scripts/shared.py")
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
    chunk_files = get_chunk()
    if not chunk_files:
        print("[RAG] No chunk files found. Skipping RAG application.")
        return
    print(f"[RAG] Applying RAG on {len(chunk_files)} chunk files...")
    for chunk_file in chunk_files:
        #apply RAG logic here
        pass
    print("[RAG] Applying Retrieval-Augmented Generation...")

def validate_format():
    print("[Validation] Validating RAG output...")

with DAG(
    dag_id="chunk_rag",
    start_date=datetime(2025, 7, 23),
    schedule_interval=None,
    catchup=False,
    description="Pipeline: Chunk -> RAG -> Validate",
    tags=["cti", "rag"],
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
