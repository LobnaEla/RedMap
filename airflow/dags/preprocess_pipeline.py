from datetime import datetime, timedelta
import sys
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# Add the project root to Python path for imports
sys.path.append("/opt/project")  # Path inside Docker container

# Centralized path configuration 
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = f"{BASE_PROJECT_PATH}/data"
METADATA_DIR = f"{BASE_PROJECT_PATH}/data/metadata"  
PROCESSED_DIR = f"{BASE_PROJECT_PATH}/data/processed" 
CHUNKS_DIR = f"{BASE_PROJECT_PATH}/data/chunks" 
RAW_SCRAPED_DIR = f"{BASE_PROJECT_PATH}/data/raw_scraped_data"  

# Default arguments for the DAG
default_args = {
    "owner": "cti-preprocessing",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    "preprocess_pipeline",
    default_args=default_args,
    description="CTI Preprocessing Pipeline: Extract -> Clean -> Normalize -> Chunk",
    schedule_interval=timedelta(hours=6),  # Run every 6 hours
    catchup=False,
    is_paused_upon_creation=False,
    tags=["cti", "preprocessing", "extract", "clean", "normalize", "chunk"],
    max_active_runs=1,  # Prevent concurrent runs
)

# ================================
# PREPROCESSING TASK FUNCTIONS
# ================================


def extract_data():
    """Extract text from various file formats with intelligent handling"""
    try:
        from cti_pipeline.scripts.preprocess.core.processors.extraction import (
            extract_with_result,
        )
        import glob

        # Create output directory
        os.makedirs(PROCESSED_DIR, exist_ok=True)

        # Process files from data directory
        file_patterns = [
            f"{DATA_DIR}/*.pdf",
            f"{DATA_DIR}/*.html",
            f"{DATA_DIR}/*.json",
            f"{DATA_DIR}/*.jsonl",
            f"{BASE_PROJECT_PATH}/PDFs/*.pdf",
        
        # Updated patterns to look in organized raw_scraped_data directory
        structured_patterns = [
            f"{RAW_SCRAPED_DIR}/*/*.json",
            f"{RAW_SCRAPED_DIR}/*/*.jsonl"
        ]
        
        unstructured_patterns = [
            f"{RAW_SCRAPED_DIR}/*/*.pdf",
            f"{RAW_SCRAPED_DIR}/*/*.html", 
            f"{BASE_PROJECT_PATH}/PDFs/*.pdf"
        ]

        extracted_files = []
        total_processed = 0
        
        # Process all file patterns
        all_patterns = structured_patterns + unstructured_patterns
        
        for pattern in all_patterns:

        for pattern in file_patterns:
            files = glob.glob(pattern)
            for file_path in files:
                try:
                    result = extract_with_result(file_path)
                    if result.success:
                        # Save extracted text with source type indicator
                        base_name = os.path.basename(file_path)
                        file_ext = os.path.splitext(file_path)[1].lower()
                        
                        # Mark structured sources for downstream optimization
                        if file_ext in ['.json', '.jsonl']:
                            output_file = os.path.join(PROCESSED_DIR, f"extracted_structured_{base_name}.txt")
                        else:
                            output_file = os.path.join(PROCESSED_DIR, f"extracted_{base_name}.txt")
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                        # Save extracted text
                        output_file = os.path.join(
                            PROCESSED_DIR,
                            f"extracted_{os.path.basename(file_path)}.txt",
                        )
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(result.text)
                        extracted_files.append(output_file)
                        total_processed += 1
                        
                        print(f"[Extract] Processed {file_path} -> {output_file}")
                except Exception as e:
                    print(f"Failed to extract from {file_path}: {e}")

        return {
            "step": "extract",
            "files_processed": total_processed,
            "output_files": extracted_files,
            "status": "success",
        }
    except Exception as e:
        raise


def clean_data():
    """Clean extracted text data with optimizations for structured content"""
    try:
        from cti_pipeline.scripts.preprocess.core.processors.cleaning.cleaning import (
            clean_text,
        )
        import glob

        # Create output directory
        cleaned_dir = os.path.join(PROCESSED_DIR, "cleaned")
        os.makedirs(cleaned_dir, exist_ok=True)

        # Process extracted files
        extracted_files = glob.glob(f"{PROCESSED_DIR}/extracted_*.txt")
        cleaned_files = []
        total_processed = 0

        for file_path in extracted_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Check if this is structured content (lighter cleaning)
                is_structured = "extracted_structured_" in os.path.basename(file_path)
                
                if is_structured:
                    # Minimal cleaning for structured content to preserve format
                    cleaned_text = text.strip()
                    # Only remove excessive whitespace
                    import re
                    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)
                    print(f"[Clean] Applied minimal cleaning to structured file: {file_path}")
                else:
                    # Full cleaning for unstructured content
                    cleaned_text = clean_text(text)
                    print(f"[Clean] Applied full cleaning to unstructured file: {file_path}")
                

                # Clean the text
                cleaned_text = clean_text(text)

                # Save cleaned text
                output_file = os.path.join(
                    cleaned_dir, f"cleaned_{os.path.basename(file_path)}"
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)

                cleaned_files.append(output_file)
                total_processed += 1
            except Exception as e:
                print(f"Failed to clean {file_path}: {e}")

        return {
            "step": "clean",
            "files_processed": total_processed,
            "output_files": cleaned_files,
            "status": "success",
        }
    except Exception as e:
        raise


def normalize_data():
    """Normalize cleaned text data with optimizations for structured content"""
    try:
        from cti_pipeline.scripts.preprocess.core.processors.cleaning.normalization import (
            normalize_text,
        )
        import glob

        # Create output directory
        normalized_dir = os.path.join(PROCESSED_DIR, "normalized")
        os.makedirs(normalized_dir, exist_ok=True)

        # Process cleaned files
        cleaned_files = glob.glob(f"{PROCESSED_DIR}/cleaned/cleaned_*.txt")
        normalized_files = []
        total_processed = 0

        for file_path in cleaned_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                
                # Check if this is structured content (lighter normalization)
                is_structured = "cleaned_extracted_structured_" in os.path.basename(file_path)
                
                if is_structured:
                    # Minimal normalization for structured content
                    normalized_text = text.strip()
                    # Only basic text normalization
                    import re
                    normalized_text = re.sub(r'\s+', ' ', normalized_text)
                    normalized_text = re.sub(r'\n\s*\n', '\n', normalized_text)
                    print(f"[Normalize] Applied minimal normalization to structured file: {file_path}")
                else:
                    # Full normalization for unstructured content
                    normalized_text = normalize_text(text)
                    print(f"[Normalize] Applied full normalization to unstructured file: {file_path}")
                

                # Normalize the text
                normalized_text = normalize_text(text)

                # Save normalized text
                output_file = os.path.join(
                    normalized_dir, f"normalized_{os.path.basename(file_path)}"
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(normalized_text)

                normalized_files.append(output_file)
                total_processed += 1
            except Exception as e:
                print(f"Failed to normalize {file_path}: {e}")

        return {
            "step": "normalize",
            "files_processed": total_processed,
            "output_files": normalized_files,
            "status": "success",
        }
    except Exception as e:
        raise


def chunk_data():
    """Chunk normalized text data using IOC-based chunking"""
    try:
        from cti_pipeline.scripts.preprocess.core.processors.chunking.chunker import (
            CTIChunker,
        )
        from cti_pipeline.scripts.preprocess.core.processors.chunking.config import (
            ChunkingConfig,
        )
        import glob
        import json

        # Create output directory
        os.makedirs(CHUNKS_DIR, exist_ok=True)

        # Initialize chunker with IOC-based strategy
        config = ChunkingConfig(chunk_strategy="ioc_based")
        chunker = CTIChunker(config)

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
                result = chunker.chunk(text)

                if result.success:
                    # Save chunks as JSON
                    base_name = os.path.splitext(os.path.basename(file_path))[0]
                    output_file = os.path.join(CHUNKS_DIR, f"chunks_{base_name}.json")

                    chunk_data = {
                        "original_file": file_path,
                        "processing_time": result.processing_time,
                        "strategy_used": result.strategy_used,
                        "total_chunks": len(result.chunks),
                        "chunks": [
                            {
                                "chunk_id": i,
                                "text": chunk.get("chunk", ""),
                                "iocs": chunk.get("ioc", ""),
                                "type": chunk.get("type", ""),
                                "metadata": {
                                    "chunk_length": chunk.get("chunk_length", 0),
                                    "record_id": chunk.get("record_id", i),
                                    "ioc_count": chunk.get("ioc_count", 0)
                                }
                                "text": chunk.text,
                                "iocs": chunk.iocs,
                                "metadata": chunk.metadata,
                            }
                            for i, chunk in enumerate(result.chunks)
                        ],
                    }

                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(chunk_data, f, indent=2, ensure_ascii=False)

                    chunk_files.append(output_file)
                    total_chunks += len(result.chunks)
                    total_processed += 1
                else:
                    print(f"Failed to chunk {file_path}: {result.errors}")

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
    """Validate that preprocessing pipeline completed successfully"""
    try:
        import glob

        # Check if all steps produced outputs
        extracted_count = len(glob.glob(f"{PROCESSED_DIR}/extracted_*.txt"))
        cleaned_count = len(glob.glob(f"{PROCESSED_DIR}/cleaned/cleaned_*.txt"))
        normalized_count = len(
            glob.glob(f"{PROCESSED_DIR}/normalized/normalized_*.txt")
        )
        chunk_count = len(glob.glob(f"{CHUNKS_DIR}/chunks_*.json"))

        validation_result = {
            "extracted_files": extracted_count,
            "cleaned_files": cleaned_count,
            "normalized_files": normalized_count,
            "chunk_files": chunk_count,
            "pipeline_success": all(
                [
                    extracted_count > 0,
                    cleaned_count > 0,
                    normalized_count > 0,
                    chunk_count > 0,
                ]
            ),
        }

        return validation_result
    except Exception as e:
        raise


def preprocessing_completion():
    """Final task to mark preprocessing pipeline completion"""
    return "Preprocessing pipeline completed successfully"


# ================================
# TASK DEFINITIONS
# ================================

# Start task
start_task = DummyOperator(
    task_id="start_preprocessing",
    dag=dag,
)

# Sequential preprocessing tasks
extract_task = PythonOperator(
    task_id="extract_data",
    python_callable=extract_data,
    dag=dag,
)

clean_task = PythonOperator(
    task_id="clean_data",
    python_callable=clean_data,
    dag=dag,
)

normalize_task = PythonOperator(
    task_id="normalize_data",
    python_callable=normalize_data,
    dag=dag,
)

chunk_task = PythonOperator(
    task_id="chunk_data",
    python_callable=chunk_data,
    dag=dag,
)

# Validation task
validate_task = PythonOperator(
    task_id="validate_preprocessing",
    python_callable=validate_preprocessing,
    dag=dag,
)

# End task
end_task = PythonOperator(
    task_id="preprocessing_completion",
    python_callable=preprocessing_completion,
    dag=dag,
)

# ================================
# TASK DEPENDENCIES
# ================================

# Define the sequential pipeline flow
(
    start_task
    >> extract_task
    >> clean_task
    >> normalize_task
    >> chunk_task
    >> validate_task
    >> end_task
)
