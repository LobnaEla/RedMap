# from datetime import datetime, timedelta
# import sys
# import os
# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from airflow.operators.dummy import DummyOperator
# from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# # Add the project root to Python path for imports
# sys.path.append("/opt/project")  # Path inside Docker container

# # Centralized path configuration
# BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
# DATA_DIR = f"{BASE_PROJECT_PATH}/data"
# METADATA_DIR = f"{BASE_PROJECT_PATH}/data/metadata"
# PROCESSED_DIR = f"{BASE_PROJECT_PATH}/data/processed"
# CHUNKS_DIR = f"{BASE_PROJECT_PATH}/data/chunks"
# RAW_SCRAPED_DIR = f"{BASE_PROJECT_PATH}/data/raw_scraped_data"

# # Default arguments for the DAG
# default_args = {
#     "owner": "cti-preprocessing",
#     "depends_on_past": False,
#     "start_date": datetime(2025, 1, 1),
#     "email_on_failure": False,
#     "email_on_retry": False,
#     "retries": 2,
#     "retry_delay": timedelta(minutes=5),
# }

# # Define the DAG
# dag = DAG(
#     "preprocess_pipeline",
#     default_args=default_args,
#     description="CTI Preprocessing Pipeline: Extract -> Clean -> Normalize -> Chunk (Triggered by cti_pipeline DAG)",
#     schedule_interval=None,
#     catchup=False,
#     is_paused_upon_creation=False,
#     tags=["cti", "preprocessing", "extract", "clean", "normalize", "chunk"],
#     max_active_runs=1,  # Prevent concurrent runs
# )

# # ================================
# # PREPROCESSING TASK FUNCTIONS
# # ================================


# def extract_data():
#     """Extract text from various file formats with intelligent handling"""
#     try:
#         from cti_pipeline.src.preprocess.core.extraction import (
#             extract_with_result,
#         )
#         import glob
#         import json
#         import hashlib
#         from datetime import datetime

#         # Create output directory with extracted subdirectory
#         os.makedirs(PROCESSED_DIR, exist_ok=True)
#         extracted_dir = os.path.join(PROCESSED_DIR, "extracted")
#         os.makedirs(extracted_dir, exist_ok=True)

#         # Focus on specific directories:
#         structured_patterns = [
#             f"{RAW_SCRAPED_DIR}/blogs/*.json",
#             f"{RAW_SCRAPED_DIR}/blogs/*.jsonl",
#         ]

#         unstructured_patterns = [
#             f"{BASE_PROJECT_PATH}/PDFs/*.pdf",
#             f"{RAW_SCRAPED_DIR}/pdfs/*.pdf",
#         ]

#         extracted_files = []
#         total_processed = 0

#         # Process all file patterns
#         all_patterns = structured_patterns + unstructured_patterns

#         for pattern in all_patterns:
#             files = glob.glob(pattern)
#             for file_path in files:
#                 try:
#                     file_ext = os.path.splitext(file_path)[1].lower()
#                     base_name = os.path.basename(file_path)

#                     # Handle JSONL files specially
#                     if file_ext == ".jsonl":
#                         # Create metadata directory
#                         os.makedirs(METADATA_DIR, exist_ok=True)

#                         metadata_entries = []

#                         with open(file_path, "r", encoding="utf-8") as f:
#                             for line_num, line in enumerate(f, 1):
#                                 try:
#                                     entry = json.loads(line.strip())

#                                     # Generate unique filename from URL hash
#                                     url = entry.get("url", "")
#                                     url_hash = hashlib.md5(url.encode()).hexdigest()[
#                                         :12
#                                     ]
#                                     timestamp = (
#                                         entry.get("timestamp", "")
#                                         .replace(":", "-")
#                                         .replace("T", "_")
#                                     )
#                                     source = entry.get("source", "unknown")

#                                     # Create unique filename
#                                     content_filename = f"extracted_article_{source}_{timestamp}_{url_hash}.txt"
#                                     content_filepath = os.path.join(
#                                         extracted_dir, content_filename
#                                     )

#                                     # Save content as separate .txt file
#                                     with open(
#                                         content_filepath, "w", encoding="utf-8"
#                                     ) as content_file:
#                                         content_file.write(entry.get("content", ""))

#                                     # Prepare metadata entry
#                                     metadata_entry = {
#                                         "content_file": content_filename,
#                                         "content_filepath": content_filepath,
#                                         "url": url,
#                                         "source": source,
#                                         "timestamp": entry.get("timestamp", ""),
#                                         "original_file": file_path,
#                                         "line_number": line_num,
#                                         "extraction_time": datetime.now().isoformat(),
#                                         "file_type": "structured_blog",
#                                     }
#                                     metadata_entries.append(metadata_entry)
#                                     extracted_files.append(content_filepath)
#                                     total_processed += 1

#                                 except json.JSONDecodeError as e:
#                                     print(
#                                         f"Failed to parse line {line_num} in {file_path}: {e}"
#                                     )

#                         # Save metadata for this JSONL file
#                         metadata_filename = f"metadata_{base_name}.json"
#                         metadata_filepath = os.path.join(
#                             METADATA_DIR, metadata_filename
#                         )
#                         with open(
#                             metadata_filepath, "w", encoding="utf-8"
#                         ) as meta_file:
#                             json.dump(
#                                 {
#                                     "source_file": file_path,
#                                     "processing_time": datetime.now().isoformat(),
#                                     "total_articles": len(metadata_entries),
#                                     "articles": metadata_entries,
#                                 },
#                                 meta_file,
#                                 indent=2,
#                                 ensure_ascii=False,
#                             )

#                         print(
#                             f"[Extract] Processed JSONL {file_path} -> {len(metadata_entries)} articles + metadata"
#                         )

#                     else:
#                         # Handle other file types (PDF, JSON, etc.) with existing extraction
#                         result = extract_with_result(file_path)
#                         if result.success:
#                             # Save extracted text with source type indicator
#                             if file_ext in [".json"]:
#                                 output_file = os.path.join(
#                                     PROCESSED_DIR,
#                                     f"extracted_structured_{base_name}.txt",
#                                 )
#                             else:
#                                 output_file = os.path.join(
#                                     PROCESSED_DIR, f"extracted_{base_name}.txt"
#                                 )

#                             with open(output_file, "w", encoding="utf-8") as f:
#                                 f.write(result.text)

#                             # Create metadata for non-JSONL files
#                             os.makedirs(METADATA_DIR, exist_ok=True)
#                             metadata_entry = {
#                                 "content_file": os.path.basename(output_file),
#                                 "content_filepath": output_file,
#                                 "original_file": file_path,
#                                 "extraction_time": datetime.now().isoformat(),
#                                 "file_type": (
#                                     "unstructured_pdf"
#                                     if file_ext == ".pdf"
#                                     else "structured_json"
#                                 ),
#                                 "extraction_success": True,
#                             }

#                             metadata_filename = f"metadata_{base_name}.json"
#                             metadata_filepath = os.path.join(
#                                 METADATA_DIR, metadata_filename
#                             )
#                             with open(
#                                 metadata_filepath, "w", encoding="utf-8"
#                             ) as meta_file:
#                                 json.dump(
#                                     metadata_entry,
#                                     meta_file,
#                                     indent=2,
#                                     ensure_ascii=False,
#                                 )

#                             extracted_files.append(output_file)
#                             total_processed += 1

#                             print(f"[Extract] Processed {file_path} -> {output_file}")

#                 except Exception as e:
#                     print(f"Failed to extract from {file_path}: {e}")

#         return {
#             "step": "extract",
#             "files_processed": total_processed,
#             "output_files": extracted_files,
#             "status": "success",
#         }
#     except Exception as e:
#         raise


# def clean_data():
#     """Clean extracted text data with optimizations for structured content"""
#     try:
#         from cti_pipeline.src.preprocess.core.cleaning import (
#             clean_text,
#         )
#         import glob

#         # Create output directory
#         cleaned_dir = os.path.join(PROCESSED_DIR, "cleaned")
#         os.makedirs(cleaned_dir, exist_ok=True)

#         # Process extracted files from extracted subdirectory
#         extracted_dir = os.path.join(PROCESSED_DIR, "extracted")
#         extracted_files = glob.glob(f"{extracted_dir}/extracted_*.txt")
#         cleaned_files = []
#         total_processed = 0

#         for file_path in extracted_files:
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     text = f.read()

#                 # Check if this is structured content (lighter cleaning)
#                 filename = os.path.basename(file_path)
#                 is_structured = (
#                     "extracted_structured_" in filename
#                     or "extracted_article_" in filename
#                 )

#                 if is_structured:
#                     # Minimal cleaning for structured content (articles and structured files)
#                     cleaned_text = text.strip()
#                     # Only remove excessive whitespace within content
#                     import re

#                     cleaned_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_text)
#                     print(
#                         f"[Clean] Applied minimal cleaning to structured file: {file_path}"
#                     )
#                 else:
#                     # Full cleaning for unstructured content (PDFs)
#                     cleaned_text = clean_text(text)
#                     print(
#                         f"[Clean] Applied full cleaning to unstructured file: {file_path}"
#                     )

#                 # Save cleaned text
#                 output_file = os.path.join(
#                     cleaned_dir, f"cleaned_{os.path.basename(file_path)}"
#                 )
#                 with open(output_file, "w", encoding="utf-8") as f:
#                     f.write(cleaned_text)

#                 cleaned_files.append(output_file)
#                 total_processed += 1
#             except Exception as e:
#                 print(f"Failed to clean {file_path}: {e}")

#         return {
#             "step": "clean",
#             "files_processed": total_processed,
#             "output_files": cleaned_files,
#             "status": "success",
#         }
#     except Exception as e:
#         raise


# def normalize_data():
#     """Normalize cleaned text data with optimizations for structured content"""
#     try:
#         from cti_pipeline.src.preprocess.core.cleaning import (
#             normalize_text,
#         )
#         import glob

#         # Create output directory
#         normalized_dir = os.path.join(PROCESSED_DIR, "normalized")
#         os.makedirs(normalized_dir, exist_ok=True)

#         # Process cleaned files
#         cleaned_files = glob.glob(f"{PROCESSED_DIR}/cleaned/cleaned_*.txt")
#         normalized_files = []
#         total_processed = 0

#         for file_path in cleaned_files:
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     text = f.read()

#                 # Check if this is structured content (lighter normalization)
#                 filename = os.path.basename(file_path)
#                 is_structured = (
#                     "cleaned_extracted_structured_" in filename
#                     or "cleaned_extracted_article_" in filename
#                 )

#                 if is_structured:
#                     # Minimal normalization for structured content (articles and structured files)
#                     normalized_text = text.strip()
#                     # Only basic text normalization within content
#                     import re

#                     normalized_text = re.sub(r"\s+", " ", normalized_text)
#                     normalized_text = re.sub(r"\n\s*\n", "\n", normalized_text)
#                     print(
#                         f"[Normalize] Applied minimal normalization to structured file: {file_path}"
#                     )
#                 else:
#                     # Full normalization for unstructured content (PDFs)
#                     normalized_text = normalize_text(text)
#                     print(
#                         f"[Normalize] Applied full normalization to unstructured file: {file_path}"
#                     )

#                 # Save normalized text
#                 output_file = os.path.join(
#                     normalized_dir, f"normalized_{os.path.basename(file_path)}"
#                 )
#                 with open(output_file, "w", encoding="utf-8") as f:
#                     f.write(normalized_text)

#                 normalized_files.append(output_file)
#                 total_processed += 1
#             except Exception as e:
#                 print(f"Failed to normalize {file_path}: {e}")

#         return {
#             "step": "normalize",
#             "files_processed": total_processed,
#             "output_files": normalized_files,
#             "status": "success",
#         }
#     except Exception as e:
#         raise


# def chunk_data():
#     """Chunk normalized text data using IOC-based chunking"""
#     try:
#         from cti_pipeline.src.preprocess.core.chunking import (
#             CTIChunker,
#         )
#         import glob
#         import json

#         # Create output directory
#         os.makedirs(CHUNKS_DIR, exist_ok=True)

#         # Initialize chunker (simplified without config)
#         chunker = CTIChunker()

#         # Process normalized files
#         normalized_files = glob.glob(f"{PROCESSED_DIR}/normalized/normalized_*.txt")
#         chunk_files = []
#         total_processed = 0
#         total_chunks = 0

#         for file_path in normalized_files:
#             try:
#                 with open(file_path, "r", encoding="utf-8") as f:
#                     text = f.read()

#                 # Chunk the text
#                 chunks = chunker.chunk(text)

#                 if chunks:
#                     # Save chunks as JSON
#                     base_name = os.path.splitext(os.path.basename(file_path))[0]
#                     output_file = os.path.join(CHUNKS_DIR, f"chunks_{base_name}.json")

#                     chunk_data = {
#                         "original_file": file_path,
#                         "processing_time": "N/A",
#                         "strategy_used": "ioc_based",
#                         "total_chunks": len(chunks),
#                         "chunks": [
#                             {
#                                 "chunk_id": i,
#                                 "text": chunk.get("chunk", ""),
#                                 "iocs": chunk.get("ioc", ""),
#                                 "type": chunk.get("type", ""),
#                                 "metadata": {
#                                     "chunk_length": len(chunk.get("chunk", "")),
#                                     "record_id": i,
#                                     "ioc_count": 1 if chunk.get("ioc") else 0,
#                                 },
#                             }
#                             for i, chunk in enumerate(chunks)
#                         ],
#                     }

#                     with open(output_file, "w", encoding="utf-8") as f:
#                         json.dump(chunk_data, f, indent=2, ensure_ascii=False)

#                     chunk_files.append(output_file)
#                     total_chunks += len(chunks)
#                     total_processed += 1
#                 else:
#                     print(f"No chunks generated for {file_path}")

#             except Exception as e:
#                 print(f"Failed to process {file_path}: {e}")

#         return {
#             "step": "chunk",
#             "files_processed": total_processed,
#             "total_chunks": total_chunks,
#             "output_files": chunk_files,
#             "status": "success",
#         }
#     except Exception as e:
#         raise


# def validate_preprocessing():
#     """Validate that preprocessing pipeline completed successfully"""
#     try:
#         import glob

#         # Check if all steps produced outputs
#         extracted_count = len(glob.glob(f"{PROCESSED_DIR}/extracted_*.txt"))
#         cleaned_count = len(glob.glob(f"{PROCESSED_DIR}/cleaned/cleaned_*.txt"))
#         normalized_count = len(
#             glob.glob(f"{PROCESSED_DIR}/normalized/normalized_*.txt")
#         )
#         chunk_count = len(glob.glob(f"{CHUNKS_DIR}/chunks_*.json"))

#         validation_result = {
#             "extracted_files": extracted_count,
#             "cleaned_files": cleaned_count,
#             "normalized_files": normalized_count,
#             "chunk_files": chunk_count,
#             "pipeline_success": all(
#                 [
#                     extracted_count > 0,
#                     cleaned_count > 0,
#                     normalized_count > 0,
#                     chunk_count > 0,
#                 ]
#             ),
#         }

#         return validation_result
#     except Exception as e:
#         raise


# def preprocessing_completion():
#     """Final task to mark preprocessing pipeline completion"""
#     return "Preprocessing pipeline completed successfully"


# # ================================
# # TASK DEFINITIONS
# # ================================

# # Start task
# start_task = DummyOperator(
#     task_id="start_preprocessing",
#     dag=dag,
# )

# # Sequential preprocessing tasks
# extract_task = PythonOperator(
#     task_id="extract_data",
#     python_callable=extract_data,
#     dag=dag,
# )

# clean_task = PythonOperator(
#     task_id="clean_data",
#     python_callable=clean_data,
#     dag=dag,
# )

# normalize_task = PythonOperator(
#     task_id="normalize_data",
#     python_callable=normalize_data,
#     dag=dag,
# )

# chunk_task = PythonOperator(
#     task_id="chunk_data",
#     python_callable=chunk_data,
#     dag=dag,
# )

# # Validation task
# validate_task = PythonOperator(
#     task_id="validate_preprocessing",
#     python_callable=validate_preprocessing,
#     dag=dag,
# )

# # End task
# end_task = PythonOperator(
#     task_id="preprocessing_completion",
#     python_callable=preprocessing_completion,
#     dag=dag,
# )

# # Trigger LLM mapping DAG after preprocessing
# trigger_llm_mapping = TriggerDagRunOperator(
#     task_id="trigger_llm_mapping",
#     trigger_dag_id="llm_mitre_mapping",
#     wait_for_completion=False,  # Don't wait for LLM mapping to complete
#     dag=dag,
# )
# # ================================
# # TASK DEPENDENCIES
# # ================================

# # Define the sequential pipeline flow
# (
#     start_task
#     >> extract_task
#     >> clean_task
#     >> normalize_task
#     >> chunk_task
#     >> validate_task
#     >> end_task
#     >> trigger_llm_mapping
# )
