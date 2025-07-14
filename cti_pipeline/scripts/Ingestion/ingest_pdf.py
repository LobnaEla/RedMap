import os
import json
import logging
from datetime import datetime
from cti_pipeline.scripts.preprocessing.ExtractionTexte import extraire_texte
from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
    PDF_DIR,
)

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_pdf(file_path, processed_data, output_file="raw_pdf.jsonl"):
    try:
        filename = os.path.basename(file_path)
        file_stat = os.stat(file_path)
        file_key = f"{filename}_{file_stat.st_size}_{file_stat.st_mtime}"

        if file_key in processed_data.get("processed_files", []):
            logger.debug(f"[⏩] Déjà traité : {filename}")
            return False, "skipped"

        logger.info(f"[📄] Traitement de : {filename}")
        full_text = extraire_texte(file_path) or ""

        if not full_text.strip():
            logger.warning(f"[⚠] Aucun texte extrait de {filename}")
            return False, "skipped"

        dummy_url = f"file://{file_path}"
        if is_duplicate(full_text, dummy_url, processed_data, "pdf"):
            logger.info(f"[🔁] Doublon détecté : {filename}")
            return False, "skipped"

        content_hash = get_content_hash(full_text, "pdf")

        doc = {
            "source": filename,
            "type": "report",
            "content": full_text.strip(),
            "date": datetime.now().isoformat(),
            "format": "PDF",
            "file_size": file_stat.st_size,
        }

        os.makedirs(DATA_DIR, exist_ok=True)
        path = os.path.join(DATA_DIR, output_file)
        with open(path, "a", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
            f.write("\n")

        # Save metadata
        processed_data.setdefault("processed_files", []).append(file_key)
        processed_data.setdefault("hashes", []).append(content_hash)
        processed_data.setdefault("urls", []).append(dummy_url)

        logger.info(f"[✅] PDF ingéré : {filename}")
        return True, "processed"

    except Exception as e:
        logger.error(f"[❌] Échec de traitement {file_path} : {e}", exc_info=True)
        return False, "failed"


def ingest_all_pdfs(pdf_dir, data_dir, metadata_dir):
    processed_data = load_processed_items("pdfs")
    stats = {"processed": 0, "skipped": 0, "failed": 0}

    for filename in os.listdir(pdf_dir):
        if not filename.endswith(".pdf"):
            continue
        file_path = os.path.join(pdf_dir, filename)
        success, status = ingest_pdf(file_path, processed_data)
        stats[status] += 1

    save_processed_items("pdfs", processed_data)
    logger.info(f"[🏁] PDF Ingestion terminée. Résumé : {stats}")
    return stats


if __name__ == "__main__":
    result = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
    print(f"Processing result: {result}")
