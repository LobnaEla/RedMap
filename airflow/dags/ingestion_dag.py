from datetime import datetime, timedelta
import sys
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# Add the project root to Python path for imports
sys.path.append("/opt/project")  # Path inside Docker container

# Centralized path configuration
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
DATA_DIR = f"{BASE_PROJECT_PATH}/data"
METADATA_DIR = f"{BASE_PROJECT_PATH}/data/metadata"
PDF_DIR = f"{BASE_PROJECT_PATH}/PDFs"

# Default arguments for the DAG
default_args = {
    "owner": "cti-pipeline",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

# Define the DAG
dag = DAG(
    "cti_pipeline",
    default_args=default_args,
    description="Complete CTI Pipeline: Ingestion -> Preprocessing -> Chunking",
    schedule_interval=timedelta(hours=12),  # Run every 12 hours
    catchup=False,
    is_paused_upon_creation=False,
    tags=["cti", "ingestion"],
    max_active_runs=1,  # Prevent concurrent runs
)

# ================================
# INGESTION TASK FUNCTIONS
# ================================


def ingest_rss_feeds():
    """Ingest data from RSS feeds (CERT-FR)"""
    try:
        from cti_pipeline.src.ingestion.ingest_rss import ingest_certfr_rss

        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        result = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
        # result is a dict with statistics
        return {"source": "rss_feeds", "stats": result, "status": "success"}
    except Exception as e:
        raise


def ingest_otx_pulses():
    """Ingest data from OTX pulses"""
    try:
        from cti_pipeline.src.ingestion.ingest_otx import ingest_otx_pulses

        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        result = ingest_otx_pulses(DATA_DIR, METADATA_DIR)
        return {"source": "otx_pulses", "stats": result, "status": "success"}
    except Exception as e:
        raise


def ingest_twitter_users():
    """Ingest data from Twitter users"""
    try:
        from cti_pipeline.src.ingestion.ingest_twitter_users import (
            ingest_all_twitter_users,
        )

        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        twitter_users = ["vxunderground", "CERT_FR", "CISACyber"]
        result = ingest_all_twitter_users(twitter_users, DATA_DIR, METADATA_DIR)
        return {
            "source": "twitter",
            "processed_count": result["processed"],
            "users": len(twitter_users),
            "status": "success",
        }
    except Exception as e:
        raise


def ingest_blogs():
    """Ingest data from blog sources"""
    try:
        from cti_pipeline.src.ingestion.scraper_blog import ingest_all_blog
        from cti_pipeline.config.blog_sources import BLOG_SOURCES

        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        result = ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
        # result is an integer representing total processed items
        return {"source": "blogs", "processed_count": result, "status": "success"}
    except Exception as e:
        raise


def ingest_tuncert():
    """Ingest data from TUNCERT vulnerabilities"""
    try:
        from cti_pipeline.src.ingestion.ingest_tuncert import (
            ingest_tuncert_vulnerabilities,
        )

        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        result = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
        return {"source": "tuncert", "stats": result, "status": "success"}
    except Exception as e:
        raise


def validate_ingestion():
    """Validate that ingestion tasks completed successfully"""
    return "Ingestion validation successful"


# ================================
# PLACEHOLDER TASK FUNCTIONS
# ================================


def preprocessing_placeholder():
    """Placeholder for preprocessing tasks"""
    return "Preprocessing placeholder executed"


def chunking_placeholder():
    """Placeholder for chunking tasks"""
    return "Chunking placeholder executed"


def pipeline_completion():
    """Final task to mark pipeline completion"""
    return "Pipeline completed"


# ================================
# TASK DEFINITIONS
# ================================

# Start task
start_task = DummyOperator(
    task_id="start_pipeline",
    dag=dag,
)

# Ingestion tasks (can run in parallel)
ingest_rss_task = PythonOperator(
    task_id="ingest_rss_feeds",
    python_callable=ingest_rss_feeds,
    dag=dag,
)

ingest_otx_task = PythonOperator(
    task_id="ingest_otx_pulses",
    python_callable=ingest_otx_pulses,
    dag=dag,
)

ingest_twitter_task = PythonOperator(
    task_id="ingest_twitter_users",
    python_callable=ingest_twitter_users,
    dag=dag,
)

ingest_blog_task = PythonOperator(
    task_id="ingest_blogs",
    python_callable=ingest_blogs,
    dag=dag,
)

ingest_tuncert_task = PythonOperator(
    task_id="ingest_tuncert",
    python_callable=ingest_tuncert,
    dag=dag,
)


# Validation task (waits for all ingestion to complete)
validate_task = PythonOperator(
    task_id="validate_ingestion",
    python_callable=validate_ingestion,
    dag=dag,
)

# End task
end_task = PythonOperator(
    task_id="pipeline_completion",
    python_callable=pipeline_completion,
    dag=dag,
)

# Trigger preprocessing DAG after ingestion completes
trigger_preprocessing = TriggerDagRunOperator(
    task_id="trigger_preprocessing_dag",
    trigger_dag_id="preprocess_pipeline",
    wait_for_completion=False,  # Don't wait for preprocessing to complete
    dag=dag,
)

# ================================
# TASK DEPENDENCIES
# ================================

# Define the pipeline flow
(
    start_task
    >> [
        ingest_rss_task,
        ingest_otx_task,
        ingest_twitter_task,
        ingest_blog_task,
        ingest_tuncert_task,
    ]
    >> validate_task
    >> end_task
    >> trigger_preprocessing
)
