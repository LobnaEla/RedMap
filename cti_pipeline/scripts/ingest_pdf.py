import logging
import os
import json
from datetime import datetime
from cti_pipeline.scripts.ExtractionTexte import extraire_texte
from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
)
from cti_pipeline.scripts.utilities import DATA_DIR, METADATA_DIR, PDF_DIR

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_single_pdf(filepath, processed_data):
    """
    Process individual PDF file with comprehensive error handling
    Returns:
        tuple: (success_status: bool, content_hash: str or None)
    """
    try:
        filename = os.path.basename(filepath)
        file_stat = os.stat(filepath)
        file_key = f"{filename}_{file_stat.st_size}_{file_stat.st_mtime}"

        if file_key in processed_data.get("processed_files", []):
            logger.debug(f"Skipping already processed PDF: {filename}")
            return False, None

        logger.info(f"Processing PDF: {filename}")
        full_text = extraire_texte(filepath)

        if not full_text:
            logger.warning(f"Empty text extracted from {filename}")
            return False, None

        dummy_url = f"file://{filepath}"
        if is_duplicate(full_text, dummy_url, processed_data, "pdf"):
            logger.debug(f"Duplicate content in {filename}")
            return False, None

        content_hash = get_content_hash(full_text, "pdf")
        return True, content_hash

    except Exception as e:
        logger.error(f"Failed to process {filepath}: {str(e)}")
        return False, None


def save_pdf_document(filename, content, output_dir):
    """Save extracted PDF content to standardized JSONL format"""
    output_file = os.path.join(
        output_dir, f"pdf_{datetime.now().strftime('%Y%m%d')}.jsonl"
    )

    document = {
        "source": filename,
        "type": "report",
        "content": content.strip(),
        "date": datetime.now().isoformat(),
        "format": "PDF",
        "file_size": os.path.getsize(filename),
    }

    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False)
        f.write("\n")


def ingest_all_pdfs(pdf_dir, data_dir, metadata_dir):
    """
    Main PDF ingestion workflow with proper state management
    Returns:
        dict: {'processed': int, 'skipped': int, 'failed': int}
    """
    processed_data = load_processed_items("pdfs", metadata_dir)
    stats = {"processed": 0, "skipped": 0, "failed": 0}

    for filename in os.listdir(pdf_dir):
        if not filename.endswith(".pdf"):
            continue

        filepath = os.path.join(pdf_dir, filename)
        success, content_hash = process_single_pdf(filepath, processed_data)

        if not success:
            stats["skipped" if content_hash is None else "failed"] += 1
            continue

        try:
            # Re-extract text to avoid storing in memory
            full_text = extraire_texte(filepath)
            save_pdf_document(filename, full_text, data_dir)

            # Update processing metadata
            file_stat = os.stat(filepath)
            file_key = f"{filename}_{file_stat.st_size}_{file_stat.st_mtime}"

            processed_data.setdefault("processed_files", []).append(file_key)
            processed_data.setdefault("hashes", []).append(content_hash)
            processed_data.setdefault("urls", []).append(f"file://{filepath}")
            stats["processed"] += 1

        except Exception as e:
            logger.error(f"Failed to save {filename}: {str(e)}")
            stats["failed"] += 1

    save_processed_items("pdfs", processed_data, metadata_dir)
    logger.info(f"PDF processing complete. Stats: {stats}")
    return stats


if __name__ == "__main__":
    result = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
    print(f"Processing result: {result}")
