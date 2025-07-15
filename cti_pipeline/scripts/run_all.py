import os
import logging
import warnings
import json
from bs4 import XMLParsedAsHTMLWarning
from dotenv import load_dotenv

# Charger le .env depuis le dossier config
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))
load_dotenv(dotenv_path)

from cti_pipeline.scripts.Ingestion.ingest_rss import ingest_certfr_rss
from cti_pipeline.scripts.Ingestion.ingest_otx import ingest_otx_pulses
from cti_pipeline.scripts.Ingestion.ingest_twitter_users import ingest_all_twitter_users
from cti_pipeline.scripts.Ingestion.scraper_blog import ingest_all_blog
# from cti_pipeline.scripts.preprocessing.ocr_client import extract_text
from cti_pipeline.scripts.Ingestion.ingest_tuncert import ingest_tuncert_vulnerabilities
from cti_pipeline.blog_sources import BLOG_SOURCES

# from cti_pipeline.scripts.preprocessing.cti_preprocessing import extract_iocs_and_ttps_from_file, save_result_to_json, export_all_iocs_to_json

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

# def lancer_preprocessing_dataset():
#     base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
#     results_dir = os.path.join(base_dir, "results")
#     data_dir = os.path.join(base_dir, "data")
#     pdf_dir = os.path.join(base_dir, "pdfs")

#     if not os.path.exists(results_dir):
#         os.makedirs(results_dir)

#     print(f"[🔍] Démarrage du preprocessing sur {data_dir}")

#     # Traitement de tous les fichiers dans data/
#     for root, dirs, files in os.walk(data_dir):
#         for filename in files:
#             filepath = os.path.join(root, filename)
#             if os.path.isfile(filepath):
#                 ext = filename.lower().split('.')[-1]
#                 print(f"📄 Traitement de {filepath}")

#                 # Utiliser directement la fonction principale d'extraction
#                 result = extract_iocs_and_ttps_from_file(filepath)
#                 if result:
#                     print(f"✅ IOC/TTP trouvé dans {filename}")
#                     save_result_to_json(result, filepath, results_dir)
#                 else:
#                     print(f"❌ Aucun IOC/TTP détecté dans {filename}")

#     # Si tu veux aussi traiter les PDFs séparément (optionnel si déjà dans data/)
#     if os.path.exists(pdf_dir):
#         print(f"[📚] Traitement des PDFs dans {pdf_dir}")
#         for filename in os.listdir(pdf_dir):
#             filepath = os.path.join(pdf_dir, filename)
#             if os.path.isfile(filepath) and filename.lower().endswith(".pdf"):
#                 print(f"📄 PDF traité séparément : {filepath}")
#                 result = extract_iocs_and_ttps_from_file(filepath)
#                 if result:
#                     save_result_to_json(result, filepath, results_dir)

#     # Export global des IOCs
#     export_all_iocs_to_json(results_dir, os.path.join(base_dir, "all_iocs.json"))
#     print("✅ Pipeline de prétraitement terminé.")

if __name__ == "__main__":
    print("[🏁] Starting full ingestion...")

    logging.basicConfig(level=logging.INFO)

    tuncert_count = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
    print(f"[✔] TUNCERT Processed {tuncert_count} vulnerabilities")

    results = ingest_otx_pulses(DATA_DIR, METADATA_DIR)
    print(f"Results: {results}")
    print("[✔] OTX pulse ingestion completed.")

    # result = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
    # print(f"[✔] PDFProcessing result: {result}")

    results = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
    print("[✔] RSS feed ingestion completed.")

    twitter_users = ["vxunderground", "CERT_FR", "CISACyber"]
    stats = ingest_all_twitter_users(twitter_users, DATA_DIR, METADATA_DIR)
    print(f"[✔] Processed {stats['processed']} new tweets from {stats['users']} users.")

    ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
    print("[✔] Blog scraping completed.")

    print("[✅] Ingestion completed.")

    print("📥 Démarrage du pipeline de prétraitement dataset...")
    # lancer_preprocessing_dataset()