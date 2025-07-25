from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from datetime import datetime, timedelta
import sys
import os
import glob

sys.path.append("/opt/project")

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw_scraped_data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
EXTRACT_DIR = os.path.join(PROCESSED_DIR, "extracted")
CLEAN_DIR = os.path.join(PROCESSED_DIR, "cleaned")
NORMALIZE_DIR = os.path.join(PROCESSED_DIR, "normalized")
CHUNKS_DIR = os.path.join(DATA_DIR, "chunks")


# === Define Task Functions ===
def extract_all_files():
    from cti_pipeline.src.preprocess import extract_text
    import glob

    os.makedirs(EXTRACT_DIR, exist_ok=True)
    raw_files = glob.glob(f"{RAW_DIR}/**/*.*", recursive=True)
    for file_path in raw_files:
        try:
            extracted = extract_text(file_path)
            base_name = os.path.basename(file_path)
            # Remove original extension and add .txt
            name_without_ext = os.path.splitext(base_name)[0]
            output_file = os.path.join(EXTRACT_DIR, f"extracted_{name_without_ext}.txt")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(extracted)
        except Exception as e:
            print(f"[Extract] Failed for {file_path}: {e}")

def clean_all_files():
    from cti_pipeline.src.preprocess import clean_text
    import glob

    os.makedirs(CLEAN_DIR, exist_ok=True)
    extracted_files = glob.glob(f"{EXTRACT_DIR}/extracted_*.txt")
    for file_path in extracted_files:
        try:
            cleaned = clean_text(file_path)
            base_name = os.path.basename(file_path)
            # Remove 'extracted_' prefix and replace with 'cleaned_'
            if base_name.startswith("extracted_"):
                clean_name = base_name.replace("extracted_", "cleaned_", 1)
            else:
                clean_name = f"cleaned_{base_name}"
            
            output_file = os.path.join(CLEAN_DIR, clean_name)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned)
        except Exception as e:
            print(f"[Clean] Failed for {file_path}: {e}")

def normalize_all_files():
    from cti_pipeline.src.preprocess import normalize_text
    import glob

    os.makedirs(NORMALIZE_DIR, exist_ok=True)
    cleaned_files = glob.glob(f"{CLEAN_DIR}/cleaned_*.txt")
    
    for file_path in cleaned_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            normalized = normalize_text(content)  # Pass content, not file path
            
            base_name = os.path.basename(file_path)
            # Replace 'cleaned_' with 'normalized_' only at the beginning
            normalized_name = base_name.replace("cleaned_", "normalized_", 1)
            
            output_file = os.path.join(NORMALIZE_DIR, normalized_name)
            with open(output_file, "w", encoding="utf-8") as f_out:
                f_out.write(normalized)
        
        except Exception as e:
            print(f"[Normalize] Failed for {file_path}: {e}")


def chunk_data():
    """Chunk normalized text data using IOC-based chunking"""
    try:
        from cti_pipeline.src.preprocess import (
            CTIChunker,
        )
        import glob
        import json

        # Create output directory
        os.makedirs(CHUNKS_DIR, exist_ok=True)

        # Initialize chunker 
        chunker = CTIChunker()

        # Process normalized files
        normalized_files = glob.glob(f"{PROCESSED_DIR}/normalized/normalized_*.txt")
        chunk_files = []
        total_processed = 0
        total_chunks = 0

        for file_path in normalized_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()

                # Chunk the text
                chunks = chunker.chunk(text)

                if chunks:
                    # Save chunks as JSON
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_file = os.path.join(CHUNKS_DIR, f"chunks_{base_name}.json")

                    chunk_data = {
                        "original_file": file_path,
                        "processing_time": "N/A",
                        "strategy_used": "ioc_based",
                        "total_chunks": len(chunks),
                        "chunks": [
                            {
                                "chunk_id": i,
                                "text": chunk.get("chunk", ""),
                                "iocs": chunk.get("ioc", ""),
                                "type": chunk.get("type", ""),
                                "metadata": {
                                    "chunk_length": len(chunk.get("chunk", "")),
                                    "record_id": i,
                                    "ioc_count": 1 if chunk.get("ioc") else 0,
                                },
                            }
                            for i, chunk in enumerate(chunks)
                        ],
                    }

                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)

                    chunk_files.append(output_file)
                    total_chunks += len(chunks)
                    total_processed += 1
                else:
                    print(f"No chunks generated for {file_path}")

            except Exception as e:
                print(f"Failed to process {file_path}: {e}")

        return {
            "step": "chunk",
            "files_processed": total_processed,
            "total_chunks": total_chunks,
            "output_files": chunk_files,
            "status": "success",
        }
    except Exception as e:
        raise

def validate_preprocessing():
    extracted = glob.glob(f"{EXTRACT_DIR}/extracted_*.txt")
    cleaned = glob.glob(f"{CLEAN_DIR}/cleaned_*.txt")
    normalized = glob.glob(f"{NORMALIZE_DIR}/normalized_*.txt")
    success = all([len(extracted) > 0, len(cleaned) > 0, len(normalized) > 0])
    if not success:
        raise ValueError("Missing files in preprocessing output")
    return {
        "extracted": len(extracted),
        "cleaned": len(cleaned),
        "normalized": len(normalized),
        "status": "Validation passed"
    }

def preprocessing_completion():
    return "Preprocessing pipeline finished successfully."

# === DAG Arguments ===
default_args = {
    "owner": "cti-preprocessing",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "preprocess_pipeline",
    default_args=default_args,
    description="CTI Preprocessing Pipeline",
    schedule_interval=None,
    catchup=False,
    is_paused_upon_creation=False,
    tags=["cti", "preprocessing"],
    max_active_runs=1,
)

# === Define Tasks ===
start_task = DummyOperator(task_id="start_preprocessing", dag=dag)

extract_task = PythonOperator(task_id="extract_data", python_callable=extract_all_files, dag=dag)
clean_task = PythonOperator(task_id="clean_text", python_callable=clean_all_files, dag=dag)
normalize_task = PythonOperator(task_id="normalize_text", python_callable=normalize_all_files, dag=dag)
chunk_task = PythonOperator(task_id="chunk_data", python_callable=chunk_data, dag=dag)

validate_task = PythonOperator(task_id="validate_preprocessing", python_callable=validate_preprocessing, dag=dag)

end_task = PythonOperator(task_id="preprocessing_completion", python_callable=preprocessing_completion, dag=dag)

trigger_llm_mapping = TriggerDagRunOperator(
    task_id="trigger_llm_mapping",
    trigger_dag_id="llm_mitre_mapping",
    wait_for_completion=False,
    dag=dag,
)

trigger_rag_mapping = TriggerDagRunOperator(
    task_id="trigger_rag_mapping",
    trigger_dag_id="rag_dag",
    wait_for_completion=False,
    dag=dag,
)

# === DAG Flow ===
start_task >> extract_task >> clean_task >> normalize_task >> chunk_task >> validate_task >> end_task >> trigger_llm_mapping >> trigger_rag_mapping