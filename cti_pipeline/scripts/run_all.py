from cti_pipeline.scripts.ingest_rss import ingest_rss
from cti_pipeline.scripts.ingest_otx import ingest_otx
from cti_pipeline.scripts.ingest_pdf import ingest_pdf
from cti_pipeline.scripts.ingest_twitter_users import get_tweets_from_user, save_tweets
from cti_pipeline.scripts.ingest_twitter import search_tweets
from cti_pipeline.pdf_sources import PDF_SOURCES
import time
import os


### PDF Ingestion
def run_pdf_ingestion():
    # # 1. Collecter tous les PDFs depuis les sources connues
    # for source in PDF_SOURCES:
    #     print(f"[🌐] Collecte des PDFs depuis {source['name']}...")
    #     collect_pdfs(source["url"])

    # 2. Ingestion des PDFs téléchargés
    PDF_DIR = "cti_pipeline/PDFs"
    for filename in os.listdir(PDF_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(PDF_DIR, filename)
            ingest_pdf(filepath, output_file="raw_pdf.jsonl")


### Twitter Ingestion
def run_twitter_ingestion():
    users = ["vxunderground", "CERT_FR", "CISACyber"]
    for user in users:
        print(f"[🔍] Collecte depuis @{user}...")
        tweets = get_tweets_from_user(user)
        save_tweets(user, tweets)


if __name__ == "__main__":
    CTI_KEYWORDS = [
        "Advanced Persistent Threat",
        "CVE",
        "IOC",
        "phishing",
        "ransomware",
        "malware",
        "exploit",
        "MITRE",
        "threat",
        "vulnerability",
    ]

    print("[🏁] Démarrage de l'ingestion complète...")
    ingest_otx()
    ingest_rss()
    run_pdf_ingestion()
    run_twitter_ingestion()

    print("[✅] Ingestion terminée.")
