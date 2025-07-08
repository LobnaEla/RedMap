from cti_pipeline.scripts.ingest_rss import ingest_certfr_rss
from cti_pipeline.scripts.ingest_otx import ingest_otx_pulses
from cti_pipeline.scripts.ingest_pdf import ingest_all_pdfs
from cti_pipeline.scripts.ingest_twitter_users import ingest_all_twitter_users
from cti_pipeline.scripts.ExtractionTexte import extraire_texte
from cti_pipeline.scripts.scraper_blog import ingest_all_blog
from cti_pipeline.scripts.ocr_library import extract_text, final_ocr_polish
from cti_pipeline.scripts.ingest_tuncert import ingest_tuncert_vulnerabilities
from cti_pipeline.blog_sources import BLOG_SOURCES

from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
    PDF_DIR,
)
import logging
import os
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


users = ["vxunderground", "CERT_FR", "CISACyber"]


if __name__ == "__main__":
    print("[🏁] Starting full ingestion...")

    logging.basicConfig(level=logging.INFO)
    tuncert_count = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
    print(f"[✔] TUNCERT Processed {tuncert_count} vulnerabilities")

    results = ingest_otx_pulses(DATA_DIR, METADATA_DIR)
    print(f"Results: {results}")
    print("[✔] OTX pulse ingestion completed.")

    result = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
    print(f"[✔] PDFProcessing result: {result}")

    results = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
    print("[✔] RSS feed ingestion completed.")

    twitter_users = ["vxunderground", "CERT_FR", "CISACyber"]
    stats = ingest_all_twitter_users(twitter_users, DATA_DIR, METADATA_DIR)
    print(f"[✔] Processed {stats['processed']} new tweets from {stats['users']} users.")

    ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
    print("[✔] Blog scraping completed.")

    print("[✅] Ingestion completed.")
