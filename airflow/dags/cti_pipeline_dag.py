from datetime import datetime, timedelta
import sys
import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator

# Add the project root to Python path for imports
sys.path.append('/opt/project')  # Path inside Docker container

# Default arguments for the DAG
default_args = {
    'owner': 'cti-pipeline',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

# Define the DAG
dag = DAG(
    'cti_pipeline',
    default_args=default_args,
    description='Complete CTI Pipeline: Ingestion -> Preprocessing -> Chunking',
    schedule_interval=timedelta(hours=12),  # Run every 12 hours
    catchup=False,
    tags=['cti', 'ingestion', 'preprocessing', 'chunking'],
    max_active_runs=1,  # Prevent concurrent runs
)

# ================================
# INGESTION TASK FUNCTIONS
# ================================

def ingest_rss_feeds():
    """Ingest data from RSS feeds (CERT-FR)"""
    try:
        from cti_pipeline.scripts.Ingestion.ingest_rss import ingest_certfr_rss
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        result = ingest_certfr_rss(data_dir, metadata_dir)
        return result
    except Exception as e:
        raise

def ingest_otx_pulses():
    """Ingest data from OTX pulses"""
    try:
        from cti_pipeline.scripts.Ingestion.ingest_otx import ingest_otx_pulses
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        result = ingest_otx_pulses(data_dir, metadata_dir)
        return result
    except Exception as e:
        raise

def ingest_pdfs():
    """Ingest data from PDF files"""
    try:
        from cti_pipeline.scripts.Ingestion.ingest_pdf import ingest_all_pdfs
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        pdf_dir = "/opt/project/cti_pipeline/PDFs"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        result = ingest_all_pdfs(pdf_dir, data_dir, metadata_dir)
        return result
    except Exception as e:
        raise

def ingest_twitter_users():
    """Ingest data from Twitter users"""
    try:
        from cti_pipeline.scripts.Ingestion.ingest_twitter_users import ingest_all_twitter_users
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        twitter_users = ["vxunderground", "CERT_FR", "CISACyber"]
        result = ingest_all_twitter_users(twitter_users, data_dir, metadata_dir)
        return result
    except Exception as e:
        raise

def ingest_blogs():
    """Ingest data from blog sources"""
    try:
        from cti_pipeline.scripts.Ingestion.scraper_blog import ingest_all_blog
        from cti_pipeline.blog_sources import BLOG_SOURCES
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        result = ingest_all_blog(BLOG_SOURCES, data_dir, metadata_dir)
        return result
    except Exception as e:
        raise

def ingest_tuncert():
    """Ingest data from TUNCERT vulnerabilities"""
    try:
        from cti_pipeline.scripts.Ingestion.ingest_tuncert import ingest_tuncert_vulnerabilities
        data_dir = "/opt/project/cti_pipeline/data"
        metadata_dir = "/opt/project/cti_pipeline/metadata"
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
        result = ingest_tuncert_vulnerabilities(data_dir, metadata_dir)
        return result
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
    task_id='start_pipeline',
    dag=dag,
)

# Ingestion tasks (can run in parallel)
ingest_rss_task = PythonOperator(
    task_id='ingest_rss_feeds',
    python_callable=ingest_rss_feeds,
    dag=dag,
)

ingest_otx_task = PythonOperator(
    task_id='ingest_otx_pulses',
    python_callable=ingest_otx_pulses,
    dag=dag,
)

ingest_pdf_task = PythonOperator(
    task_id='ingest_pdfs',
    python_callable=ingest_pdfs,
    dag=dag,
)

ingest_twitter_task = PythonOperator(
    task_id='ingest_twitter_users',
    python_callable=ingest_twitter_users,
    dag=dag,
)

ingest_blog_task = PythonOperator(
    task_id='ingest_blogs',
    python_callable=ingest_blogs,
    dag=dag,
)

ingest_tuncert_task = PythonOperator(
    task_id='ingest_tuncert',
    python_callable=ingest_tuncert,
    dag=dag,
)


# Validation task (waits for all ingestion to complete)
validate_task = PythonOperator(
    task_id='validate_ingestion',
    python_callable=validate_ingestion,
    dag=dag,
)

# Preprocessing placeholder
preprocessing_task = PythonOperator(
    task_id='preprocessing_placeholder',
    python_callable=preprocessing_placeholder,
    dag=dag,
)

# Chunking placeholder
chunking_task = PythonOperator(
    task_id='chunking_placeholder',
    python_callable=chunking_placeholder,
    dag=dag,
)

# End task
end_task = PythonOperator(
    task_id='pipeline_completion',
    python_callable=pipeline_completion,
    dag=dag,
)

# ================================
# TASK DEPENDENCIES
# ================================

# Define the pipeline flow
start_task >> [
    ingest_rss_task,
    ingest_otx_task,
    ingest_pdf_task,
    ingest_twitter_task,
    ingest_blog_task,
    ingest_tuncert_task,
] >> validate_task >> preprocessing_task >> chunking_task >> end_task