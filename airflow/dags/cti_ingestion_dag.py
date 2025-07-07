from asyncio import Task
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
import os
from cti_pipeline.scripts import ingest_rss
from cti_pipeline.scripts import ingest_otx
from cti_pipeline.scripts import ingest_pdf
from cti_pipeline.scripts import ingest_twitter_users

sys.path.insert(0, "/opt/airflow/cti_pipeline")


def run_ingestion():
    ingest_rss.main()


with DAG(
    dag_id="cti_ingestion_dag",
    start_date=datetime(2025, 7, 1),
    schedule_interval="@hourly",
    catchup=False,
) as dag:

    @Task
    def ingest_otx_pulses():
        ingest_otx.main()

    @Task
    def ingest_pdf_documents():
        ingest_pdf.main()

    @Task
    def ingest_twitter_users():
        ingest_twitter_users.main()

    @Task
    def ingest_rss_feeds():
        run_ingestion()
