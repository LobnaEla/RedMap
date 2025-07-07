from cti_pipeline.scripts.ingest_rss import ingest_rss
from cti_pipeline.scripts.ingest_otx import ingest_otx
from cti_pipeline.scripts.ingest_pdf import run_pdf_ingestion
from cti_pipeline.scripts.ingest_twitter_users import get_tweets_from_user, save_tweets
from cti_pipeline.scripts.ingest_twitter import search_tweets
from cti_pipeline.pdf_sources import PDF_SOURCES
from cti_pipeline.blog_sources import BLOG_SOURCES
from cti_pipeline.scripts.scraper_blog import scrape_blog
import time
import os
from bs4 import XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


### Blog Scraping
def run_blog_scraping():
    for blog in BLOG_SOURCES:
        print(f"[🌐] Scraping blog : {blog['name']} ...")
        scrape_blog(index_url=blog["url"], blog_name=blog["name"])
    print(f"[📊] Ingestion terminée pour les blogs CTI.")


### Twitter Ingestion
def run_twitter_ingestion():
    users = ["vxunderground", "CERT_FR", "CISACyber"]
    for user in users:
        print(f"[🔍] Collecte depuis @{user}...")
        tweets = get_tweets_from_user(user)
        save_tweets(user, tweets)


if __name__ == "__main__":
    print("[🏁] Démarrage de l'ingestion complète...")
    ingest_otx()
    ingest_rss()
    run_pdf_ingestion()
    run_twitter_ingestion()
    run_blog_scraping()

    print("[✅] Ingestion terminée.")
