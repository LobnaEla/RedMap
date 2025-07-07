from datetime import datetime, timedelta
import os
import json
import hashlib
from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import logging

# Imports des modules CTI
from cti_pipeline.scripts.ingest_rss import ingest_rss
from cti_pipeline.scripts.ingest_otx import ingest_otx
from cti_pipeline.scripts.ingest_pdf import ingest_pdf
from cti_pipeline.scripts.ingest_twitter_users import get_tweets_from_user, save_tweets
from cti_pipeline.scripts.scraper_blog import scrape_blog
from cti_pipeline.pdf_sources import PDF_SOURCES
from cti_pipeline.blog_sources import BLOG_SOURCES

# Configuration du DAG
default_args = {
    "owner": "wevioo",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# Définition du DAG
dag = DAG(
    "cti_ingestion_pipeline",
    default_args=default_args,
    description="Pipeline d'ingestion CTI avec gestion des doublons",
    schedule_interval=timedelta(hours=1),  # Exécution toutes les heures
    catchup=False,
    max_active_runs=1,
    tags=["cti", "cybersecurity", "ingestion"],
)

# Répertoires de données
DATA_DIR = "cti_pipeline/data/"
METADATA_DIR = "cti_pipeline/metadata/"
PDF_DIR = "cti_pipeline/PDFs/"

# Création des répertoires nécessaires
for directory in [DATA_DIR, METADATA_DIR, PDF_DIR]:
    os.makedirs(directory, exist_ok=True)


# Utilitaires pour la gestion des doublons
def get_content_hash(content):
    """Génère un hash MD5 du contenu pour détecter les doublons."""
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def load_processed_items(source_name):
    """Charge la liste des éléments déjà traités pour une source."""
    metadata_file = os.path.join(METADATA_DIR, f"{source_name}_processed.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"hashes": [], "urls": [], "last_run": None}


def save_processed_items(source_name, processed_data):
    """Sauvegarde la liste des éléments traités pour une source."""
    metadata_file = os.path.join(METADATA_DIR, f"{source_name}_processed.json")
    processed_data["last_run"] = datetime.now().isoformat()
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)


def is_duplicate(content, url, processed_data):
    """Vérifie si le contenu est un doublon."""
    content_hash = get_content_hash(content)
    return content_hash in processed_data["hashes"] or url in processed_data["urls"]


# Tâches d'ingestion
@task()
def ingest_rss_feed():
    """Ingestion des flux RSS CERT-FR avec gestion des doublons."""
    logging.info("🔄 Début ingestion RSS CERT-FR")

    processed_data = load_processed_items("rss_certfr")

    try:
        import feedparser

        url = "https://www.cert.ssi.gouv.fr/feed/"
        feed = feedparser.parse(url)

        new_items = 0
        output_file = f"raw_rss_certfr_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"

        with open(os.path.join(DATA_DIR, output_file), "w", encoding="utf-8") as f:
            for entry in feed.entries:
                content = entry.get("summary", "")
                url_entry = entry.link

                if not is_duplicate(content, url_entry, processed_data):
                    doc = {
                        "source": "CERT-FR RSS",
                        "type": "rss_bulletin",
                        "title": entry.title,
                        "link": url_entry,
                        "date_published": entry.published,
                        "content": content,
                        "date_collected": datetime.now().isoformat(),
                    }

                    json.dump(doc, f, ensure_ascii=False)
                    f.write("\n")

                    # Mettre à jour les éléments traités
                    processed_data["hashes"].append(get_content_hash(content))
                    processed_data["urls"].append(url_entry)
                    new_items += 1

        save_processed_items("rss_certfr", processed_data)
        logging.info(f"✅ RSS: {new_items} nouveaux bulletins collectés")

    except Exception as e:
        logging.error(f"❌ Erreur ingestion RSS: {e}")
        raise


@task()
def ingest_otx_pulses():
    """Ingestion des pulses OTX avec gestion des doublons."""
    logging.info("🔄 Début ingestion OTX")

    processed_data = load_processed_items("otx")

    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv(dotenv_path="cti_pipeline/config/.env")
        OTX_API_KEY = os.getenv("OTX_API_KEY")

        if not OTX_API_KEY:
            raise Exception("OTX API Key manquante")

        headers = {"X-OTX-API-KEY": OTX_API_KEY}
        response = requests.get(
            "https://otx.alienvault.com/api/v1/pulses/subscribed",
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()
        pulses = data.get("results", [])

        new_items = 0
        output_file = f"raw_otx_pulses_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"

        with open(os.path.join(DATA_DIR, output_file), "w", encoding="utf-8") as f:
            for pulse in pulses:
                pulse_id = pulse.get("id", "")
                content = pulse.get("description", "")

                if pulse_id not in processed_data.get("pulse_ids", []):
                    doc = {
                        "source": "OTX",
                        "type": "cti_pulse",
                        "pulse_id": pulse_id,
                        "title": pulse.get("name"),
                        "description": content,
                        "tags": pulse.get("tags", []),
                        "created": pulse.get("created"),
                        "modified": pulse.get("modified"),
                        "indicators": pulse.get("indicators", []),
                        "tlp": pulse.get("tlp", "TLP:WHITE"),
                        "date_collected": datetime.now().isoformat(),
                    }

                    json.dump(doc, f, ensure_ascii=False)
                    f.write("\n")

                    # Mettre à jour les éléments traités
                    if "pulse_ids" not in processed_data:
                        processed_data["pulse_ids"] = []
                    processed_data["pulse_ids"].append(pulse_id)
                    new_items += 1

        save_processed_items("otx", processed_data)
        logging.info(f"✅ OTX: {new_items} nouveaux pulses collectés")

    except Exception as e:
        logging.error(f"❌ Erreur ingestion OTX: {e}")
        raise


@task()
def ingest_twitter_data():
    """Ingestion des données Twitter avec gestion des doublons."""
    logging.info("🔄 Début ingestion Twitter")

    processed_data = load_processed_items("twitter")

    try:
        from cti_pipeline.scripts.ingest_twitter_users import get_tweets_from_user

        users = ["vxunderground", "CERT_FR", "CISACyber"]
        total_new_tweets = 0

        for user in users:
            user_processed = processed_data.get(user, {"tweet_ids": []})
            tweets = get_tweets_from_user(user, max_scrolls=3)

            new_tweets = []
            for tweet in tweets:
                tweet_id = tweet.get("tweet_url", "").split("/")[-1]
                if tweet_id not in user_processed["tweet_ids"]:
                    new_tweets.append(tweet)
                    user_processed["tweet_ids"].append(tweet_id)

            if new_tweets:
                now = datetime.now().strftime("%Y%m%d_%H%M")
                output_file = f"twitter_{user}_{now}.jsonl"

                with open(
                    os.path.join(DATA_DIR, output_file), "w", encoding="utf-8"
                ) as f:
                    for tweet in new_tweets:
                        json.dump(tweet, f, ensure_ascii=False)
                        f.write("\n")

                total_new_tweets += len(new_tweets)
                processed_data[user] = user_processed

        save_processed_items("twitter", processed_data)
        logging.info(f"✅ Twitter: {total_new_tweets} nouveaux tweets collectés")

    except Exception as e:
        logging.error(f"❌ Erreur ingestion Twitter: {e}")
        raise


@task()
def ingest_blog_articles():
    """Ingestion des articles de blogs CTI avec gestion des doublons."""
    logging.info("🔄 Début ingestion blogs")

    processed_data = load_processed_items("blogs")

    try:
        total_new_articles = 0

        for blog in BLOG_SOURCES:
            blog_name = blog["name"]
            blog_processed = processed_data.get(blog_name, {"urls": []})

            # Scraper personnalisé pour éviter les doublons
            from cti_pipeline.scripts.scraper_blog import (
                extract_article_links,
                extract_text_from_url,
            )

            links = extract_article_links(blog["url"])
            new_articles = []

            for url in links:
                if url not in blog_processed["urls"]:
                    text = extract_text_from_url(url, source_name=blog_name)
                    if text:
                        doc = {
                            "url": url,
                            "source": blog_name,
                            "format": "HTML",
                            "date": datetime.now().isoformat(),
                            "content": text,
                        }
                        new_articles.append(doc)
                        blog_processed["urls"].append(url)

            if new_articles:
                now = datetime.now().strftime("%Y%m%d_%H%M")
                output_file = f"blog_{blog_name}_{now}.jsonl"

                with open(
                    os.path.join(DATA_DIR, output_file), "w", encoding="utf-8"
                ) as f:
                    for article in new_articles:
                        json.dump(article, f, ensure_ascii=False)
                        f.write("\n")

                total_new_articles += len(new_articles)
                processed_data[blog_name] = blog_processed

        save_processed_items("blogs", processed_data)
        logging.info(f"✅ Blogs: {total_new_articles} nouveaux articles collectés")

    except Exception as e:
        logging.error(f"❌ Erreur ingestion blogs: {e}")
        raise


@task()
def ingest_pdf_reports():
    """Ingestion des rapports PDF avec gestion des doublons."""
    logging.info("🔄 Début ingestion PDFs")

    processed_data = load_processed_items("pdfs")

    try:
        from cti_pipeline.scripts.ExtractionTexte import extraire_texte

        total_new_pdfs = 0

        # Traiter tous les PDFs dans le répertoire
        for filename in os.listdir(PDF_DIR):
            if filename.endswith(".pdf"):
                filepath = os.path.join(PDF_DIR, filename)
                file_stat = os.stat(filepath)
                file_key = f"{filename}_{file_stat.st_size}_{file_stat.st_mtime}"

                if file_key not in processed_data.get("processed_files", []):
                    logging.info(f"📄 Traitement PDF: {filename}")

                    full_text = extraire_texte(filepath)
                    if full_text:
                        doc = {
                            "source": filename,
                            "type": "report",
                            "content": full_text.strip(),
                            "date": datetime.now().isoformat(),
                            "format": "PDF",
                            "file_size": file_stat.st_size,
                        }

                        output_file = (
                            f"raw_pdf_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
                        )

                        with open(
                            os.path.join(DATA_DIR, output_file), "a", encoding="utf-8"
                        ) as f:
                            json.dump(doc, f, ensure_ascii=False)
                            f.write("\n")

                        # Marquer comme traité
                        if "processed_files" not in processed_data:
                            processed_data["processed_files"] = []
                        processed_data["processed_files"].append(file_key)
                        total_new_pdfs += 1

        save_processed_items("pdfs", processed_data)
        logging.info(f"✅ PDFs: {total_new_pdfs} nouveaux rapports traités")

    except Exception as e:
        logging.error(f"❌ Erreur ingestion PDFs: {e}")
        raise


@task()
def cleanup_old_data():
    """Nettoyage des anciens fichiers de données (> 30 jours)."""
    logging.info("🧹 Nettoyage des anciennes données")

    try:
        import time

        current_time = time.time()
        retention_days = 30
        retention_seconds = retention_days * 24 * 60 * 60

        cleaned_files = 0

        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                file_age = current_time - os.path.getctime(file_path)

                if file_age > retention_seconds:
                    os.remove(file_path)
                    cleaned_files += 1
                    logging.info(f"🗑️ Fichier supprimé: {file}")

        logging.info(f"✅ Nettoyage terminé: {cleaned_files} fichiers supprimés")

    except Exception as e:
        logging.error(f"❌ Erreur nettoyage: {e}")
        raise


@task()
def generate_ingestion_report():
    """Génération d'un rapport d'ingestion."""
    logging.info("📊 Génération rapport d'ingestion")

    try:
        report = {
            "timestamp": datetime.now().isoformat(),
            "sources_status": {},
            "total_files": 0,
            "total_size_mb": 0,
        }

        # Compter les fichiers et tailles
        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                if file.endswith(".jsonl"):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)

                    report["total_files"] += 1
                    report["total_size_mb"] += file_size / (1024 * 1024)

                    # Catégoriser par source
                    source = file.split("_")[0]
                    if source not in report["sources_status"]:
                        report["sources_status"][source] = {"files": 0, "size_mb": 0}

                    report["sources_status"][source]["files"] += 1
                    report["sources_status"][source]["size_mb"] += file_size / (
                        1024 * 1024
                    )

        # Sauvegarder le rapport
        report_file = os.path.join(
            METADATA_DIR,
            f"ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logging.info(f"✅ Rapport sauvegardé: {report_file}")
        logging.info(
            f"📈 Total: {report['total_files']} fichiers, {report['total_size_mb']:.2f} MB"
        )

    except Exception as e:
        logging.error(f"❌ Erreur génération rapport: {e}")
        raise


# Définition des tâches du DAG
with dag:
    # Tâches d'ingestion en parallèle
    rss_task = ingest_rss_feed()
    otx_task = ingest_otx_pulses()
    twitter_task = ingest_twitter_data()
    blog_task = ingest_blog_articles()
    pdf_task = ingest_pdf_reports()

    # Tâches de maintenance
    cleanup_task = cleanup_old_data()
    report_task = generate_ingestion_report()

    # Définition des dépendances
    # Toutes les tâches d'ingestion s'exécutent en parallèle
    (
        [rss_task, otx_task, twitter_task, blog_task, pdf_task]
        >> cleanup_task
        >> report_task
    )
