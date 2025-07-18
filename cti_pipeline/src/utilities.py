# Utilities for duplicate handling
from datetime import datetime
import hashlib
import json
import os
import re


# Base data directory
BASE_DATA_DIR = "cti_pipeline/data/"

# Organized subdirectories under /data
DATA_DIR = BASE_DATA_DIR
METADATA_DIR = os.path.join(BASE_DATA_DIR, "metadata")
PDF_DIR = "cti_pipeline/PDFs/"
PROCESSED_DIR = os.path.join(BASE_DATA_DIR, "processed")
CHUNKS_DIR = os.path.join(BASE_DATA_DIR, "chunks")
RAW_SCRAPED_DIR = os.path.join(BASE_DATA_DIR, "raw_scraped_data")

# Create all required directories
directories_to_create = [
    BASE_DATA_DIR,
    METADATA_DIR,
    PDF_DIR,
    PROCESSED_DIR,
    CHUNKS_DIR,
    RAW_SCRAPED_DIR,
    os.path.join(RAW_SCRAPED_DIR, "rss"),
    os.path.join(RAW_SCRAPED_DIR, "otx"),
    os.path.join(RAW_SCRAPED_DIR, "twitter"),
    os.path.join(RAW_SCRAPED_DIR, "blogs"),
    os.path.join(RAW_SCRAPED_DIR, "tuncert"),
    os.path.join(RAW_SCRAPED_DIR, "pdfs"),
    os.path.join(PROCESSED_DIR, "extracted"),
    os.path.join(PROCESSED_DIR, "cleaned"),
    os.path.join(PROCESSED_DIR, "normalized"),
]

for directory in directories_to_create:
    os.makedirs(directory, exist_ok=True)


def get_content_hash(content, content_type="generic"):
    """Generates a robust hash of the content to detect duplicates."""

    # Basic normalization
    normalized = content.lower().strip()

    # Remove multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Remove dynamic elements based on content type
    if content_type == "rss":
        # Remove dates in RSS feeds
        normalized = re.sub(
            r"publié le \d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", "", normalized
        )
        normalized = re.sub(
            r"mis à jour le \d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", "", normalized
        )

    elif content_type == "pdf":
        # Remove page numbers
        normalized = re.sub(r"page \d+", "", normalized)
        normalized = re.sub(r"^\s*\d+\s*$", "", normalized, flags=re.MULTILINE)

    # Remove insignificant punctuation
    normalized = re.sub(r"[^\w\s]", "", normalized)

    # Final cleanup
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def load_processed_items(source_name):
    """Loads the list of already processed items for a source."""
    metadata_file = os.path.join(METADATA_DIR, f"{source_name}_processed.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"hashes": [], "urls": [], "last_run": None}


def save_processed_items(source_name, processed_data):
    """Saves the list of processed items for a source."""
    metadata_file = os.path.join(METADATA_DIR, f"{source_name}_processed.json")
    processed_data["last_run"] = datetime.now().isoformat()
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)


def is_duplicate(content, url, processed_data, content_type="generic"):
    """Checks if the content is a duplicate."""

    # Exact URL check
    if url in processed_data["urls"]:
        return True

    # Normalized content check
    content_hash = get_content_hash(content, content_type)
    if content_hash in processed_data["hashes"]:
        return True

    return False
