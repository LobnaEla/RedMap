from ingest_rss import ingest_rss
from ingest_otx import ingest_otx
from ingest_pdf import ingest_pdf
from ingest_twitter_users import get_tweets_from_user, save_tweets
from ingest_twitter import search_tweets
import time
import os


### PDF Ingestion
def run_pdf_ingestion():
    PDF_DIR = "cti-pipeline/PDFs"
    if not os.path.exists(PDF_DIR):
        print(f"[!] Dossier PDF introuvable : {PDF_DIR}")
        return

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
    # ingest_otx()
    # ingest_rss()
    # # run_pdf_ingestion()
    # run_twitter_ingestion()
    for keyword in CTI_KEYWORDS:
        print(f"[🔍] Searching tweets for keyword: {keyword}")
        safe_label = keyword.replace(" ", "_")
        search_tweets(query=keyword, label=safe_label, max_results=20)
        time.sleep(3)  # Attendre 3 secondes entre chaque requête

    print("[✅] Ingestion terminée.")
