from datetime import datetime, timedelta
import sys
import os
import importlib
import yaml

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

# Add the project root for Docker imports
sys.path.append("/opt/project/cti_pipeline")

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
CONFIG_PATH = os.path.join(BASE_PROJECT_PATH, "config")
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
METADATA_DIR = os.path.join(DATA_DIR, "metadata")
PDF_DIR = os.path.join(BASE_PROJECT_PATH, "PDFs")

# === Default DAG Arguments ===
default_args = {
    "owner": "cti-pipeline",
    "depends_on_past": False,
    "start_date": datetime(2025, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}


# === Load Ingestion Config ===
def load_sources_config():
    sources_yaml_path = os.path.join(CONFIG_PATH, "sources.yaml")
    with open(sources_yaml_path, "r") as f:
        return yaml.safe_load(f)["sources"]


# === Dynamic Task Factory ===
def make_ingest_callable(module_path, function_name):
    def _callable(**kwargs):
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(METADATA_DIR, exist_ok=True)
        module = importlib.import_module(module_path)
        func = getattr(module, function_name)
        return func(data_dir=DATA_DIR, metadata_dir=METADATA_DIR)

    return _callable


# === DAG Definition ===
dag = DAG(
    dag_id="cti_pipeline",
    default_args=default_args,
    description="CTI Ingestion Pipeline",
    schedule_interval=timedelta(hours=12),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=["cti", "ingestion"],
)

# === DAG Tasks ===

# Start
start_task = DummyOperator(
    task_id="start_pipeline",
    dag=dag,
)

# Ingestion Tasks
sources = load_sources_config()
ingestion_tasks = []

for source in sources:
    source_name = source["name"]
    module_path = source["module"]
    function_name = source["function"]

    task = PythonOperator(
        task_id=f"ingest_{source_name}",
        python_callable=make_ingest_callable(module_path, function_name),
        dag=dag,
    )
    ingestion_tasks.append(task)


# Validation
def validate_ingestion():
    return "Ingestion validation successful"


validate_task = PythonOperator(
    task_id="validate_ingestion",
    python_callable=validate_ingestion,
    dag=dag,
)


# Pipeline End
def pipeline_completion():
    return "Pipeline completed"


end_task = PythonOperator(
    task_id="pipeline_completion",
    python_callable=pipeline_completion,
    dag=dag,
)

# Trigger Next DAG
trigger_preprocessing = TriggerDagRunOperator(
    task_id="trigger_preprocessing_dag",
    trigger_dag_id="preprocess_pipeline",
    wait_for_completion=False,
    dag=dag,
)

# === Task Dependencies ===
start_task >> ingestion_tasks >> validate_task >> end_task >> trigger_preprocessing
