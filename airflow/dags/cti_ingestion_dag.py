from datetime import datetime, timedelta
import os
import json
import hashlib
import re
from airflow import DAG
from airflow.decorators import task
from airflow.operators.python import PythonOperator
import logging
import sys

# Ajoutez le chemin racine du projet au PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "../cti_pipeline"))

# Only import lightweight modules at the top level
# Heavy imports will be done inside task functions

# DAG configuration
default_args = {
    "owner": "wevioo",
    "depends_on_past": False,
    "start_date": datetime(2025, 7, 6),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    "cti_ingestion_pipeline",
    default_args=default_args,
    description="CTI ingestion pipeline",
    schedule=timedelta(hours=1),  # Run every hour
    catchup=False,
    max_active_runs=1,
)

# Data directories
DATA_DIR = "/opt/airflow/cti_pipeline/data/"
METADATA_DIR = "/opt/airflow/cti_pipeline/metadata/"
PDF_DIR = "/opt/airflow/cti_pipeline/PDFs/"

# Create required directories
for directory in [DATA_DIR, METADATA_DIR, PDF_DIR]:
    os.makedirs(directory, exist_ok=True)


# Ingestion tasks
@task()
def ingest_rss_feed():
    """Airflow task for CERT-FR RSS ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.ingest_rss import ingest_certfr_rss
    
    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting RSS ingestion")

    try:
        result = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
        logger.info(
            f"✅ RSS: {result['processed']} new bulletins collected (out of {result['total']})"
        )
        return result

    except Exception as e:
        logger.error(f"❌ RSS ingestion failed: {str(e)}")
        raise


@task()
def ingest_tuncert_vulnerabilities_task():
    """Airflow task for TUNCERT ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.ingest_tuncert import ingest_tuncert_vulnerabilities
    
    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting TUNCERT ingestion")

    try:
        result = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
        logger.info(
            f"✅ TUNCERT: {result['processed']} new vulnerabilities collected (out of {result['total']})"
        )
        return result

    except Exception as e:
        logger.error(f"❌ TUNCERT ingestion failed: {str(e)}")
        raise


@task()
def ingest_otx_task():
    """Airflow task for OTX pulse ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.ingest_otx import ingest_otx_pulses as ingest_otx_pulses_func
    
    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting OTX ingestion")

    try:
        result = ingest_otx_pulses_func(DATA_DIR, METADATA_DIR)
        logger.info(
            f"✅ OTX: {result['processed']} new pulses collected (out of {result['total']})"
        )
        return result

    except Exception as e:
        logger.error(f"❌ OTX ingestion failed: {str(e)}")
        raise


@task()
def ingest_twitter_data():
    """Tâche Airflow pour l'ingestion Twitter"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.ingest_twitter_users import ingest_all_twitter_users
    
    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting Twitter ingestion")

    users = ["vxunderground", "CERT_FR", "CISACyber"]

    try:
        result = ingest_all_twitter_users(users, DATA_DIR, METADATA_DIR)
        logger.info(f"✅ Twitter: {result['processed']} nouveaux tweets collectés")
        logger.info(f"👤 Utilisateurs traités: {result['users']}")
        return result

    except Exception as e:
        logger.error(f"❌ Échec de l'ingestion Twitter: {str(e)}")
        raise


@task()
def ingest_blog_articles():
    """Airflow task for blog ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.scraper_blog import ingest_all_blog
    from cti_pipeline.blog_sources import BLOG_SOURCES
    
    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting blogs ingestion")

    total_processed = 0

    try:
        total_processed = ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
        return total_processed

    except Exception as e:
        logger.error(f"❌ Blog ingestion failed: {str(e)}")
        raise


@task()
def ingest_pdf_reports():
    """Ingest PDF threat reports"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.ingest_pdf import ingest_all_pdfs
    
    logging.info("🔄 Starting PDF ingestion")

    try:
        # Call the function that handles ingestion of all PDFs
        total_new_pdfs = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
        logging.info(f"✅ PDFs: {total_new_pdfs} new reports processed")
        return total_new_pdfs

    except Exception as e:
        logging.error(f"❌ Error during PDF ingestion: {e}")
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
    tuncert_task = ingest_tuncert_vulnerabilities_task()
    otx_task = ingest_otx_task()
    twitter_task = ingest_twitter_data()
    blog_task = ingest_blog_articles()
    pdf_task = ingest_pdf_reports()
    tuncert_task = ingest_tuncert()

    # Tâches de maintenance
    cleanup_task = cleanup_old_data()
    report_task = generate_ingestion_report()

    # Définition des dépendances
    # Toutes les tâches d'ingestion s'exécutent en parallèle
    (
        [rss_task, tuncert_task, otx_task, twitter_task, blog_task, pdf_task]
        >> cleanup_task
        >> report_task
    )
