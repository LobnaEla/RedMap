import os
import logging
import warnings
from bs4 import XMLParsedAsHTMLWarning

from cti_pipeline.scripts.Ingestion.ingest_rss import ingest_certfr_rss
from cti_pipeline.scripts.Ingestion.ingest_otx import ingest_otx_pulses
from cti_pipeline.scripts.Ingestion.ingest_pdf import ingest_all_pdfs
from cti_pipeline.scripts.Ingestion.ingest_twitter_users import ingest_all_twitter_users
from cti_pipeline.scripts.preprocessing.ExtractionTexte import extraire_texte
from cti_pipeline.scripts.Ingestion.scraper_blog import ingest_all_blog
from cti_pipeline.scripts.preprocessing.ocr_client import extract_text
from cti_pipeline.scripts.Ingestion.ingest_tuncert import ingest_tuncert_vulnerabilities
from cti_pipeline.blog_sources import BLOG_SOURCES

from cti_pipeline.scripts.preprocessing.cti_preprocessing import extract_iocs_and_ttps_from_file, save_result_to_json, export_all_iocs_to_json

from cti_pipeline.scripts.utilities import (
    get_content_hash,
    load_processed_items,
    save_processed_items,
    is_duplicate,
    DATA_DIR,
    METADATA_DIR,
    PDF_DIR,
)

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def lancer_preprocessing():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # remonte à cti_pipeline
    samples_dir = os.path.join(base_dir, "samples")
    results_dir = os.path.join(base_dir, "results")

    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    for filename in os.listdir(samples_dir):
        filepath = os.path.join(samples_dir, filename)
        if os.path.isfile(filepath):
            print(f"📄 Traitement de {filename}")
            result = extract_iocs_and_ttps_from_file(filepath)
            if result:
                save_result_to_json(result, filepath, results_dir)

    export_all_iocs_to_json(results_dir, os.path.join(base_dir, "all_iocs.json"))
    print("✅ Pipeline de prétraitement terminé.")


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

    print("📥 Démarrage du pipeline de prétraitement...")
    lancer_preprocessing()
