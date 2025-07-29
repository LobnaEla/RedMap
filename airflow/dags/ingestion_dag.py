from datetime import datetime, timedelta
import sys
import os
import importlib
import yaml
import requests

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

# === N8N Configuration ===
N8N_BASE_URL = "http://n8n:5678"

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


# === Validation Function (per source) ===
def make_validate_callable(source_name):
    def _validate(**kwargs):
        # Your validation logic here - adapt as needed
        print(f"Validating ingestion for {source_name}")
        return f"Ingestion validation successful for {source_name}"

    return _validate


# === Pipeline Completion (per source) ===
def make_completion_callable(source_name):
    def _complete(**kwargs):
        return f"Pipeline completed for {source_name}"

    return _complete


# === N8N Trigger Function ===
def make_n8n_trigger_callable(source_name):
    def _trigger(**kwargs):
        payload = {
            "source_name": source_name,
            "data_dir": DATA_DIR,
            "metadata_dir": METADATA_DIR,
            "timestamp": datetime.now().isoformat(),
            "status": "ready_for_preprocessing",
        }

        try:
            webhook_url = f"{N8N_BASE_URL}/webhook/process-source"
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                print(f"{source_name} sent to n8n for preprocessing")
                return {
                    "source": source_name,
                    "n8n_trigger": "success",
                    "response": response.json() if response.content else "OK",
                }
            else:
                print(f"n8n trigger failed for {source_name}: {response.status_code}")
                return {
                    "source": source_name,
                    "n8n_trigger": "failed",
                    "error": f"HTTP {response.status_code}",
                }

        except Exception as e:
            print(f"N8N trigger failed for {source_name}: {str(e)}")
            raise e

    return _trigger


# === Individual DAGs for Each Source ===
sources = load_sources_config()

for source in sources:
    source_name = source["name"]
    module_path = source["module"]
    function_name = source["function"]

    # Create individual DAG for this source
    source_dag = DAG(
        dag_id=f"cti_pipeline_{source_name}",
        default_args=default_args,
        description=f"CTI Ingestion Pipeline for {source_name}",
        schedule_interval=timedelta(hours=12),
        catchup=False,
        is_paused_upon_creation=False,
        max_active_runs=1,
        tags=["cti", "ingestion", source_name],
    )

    # === DAG Tasks ===
    # Start
    start_task = DummyOperator(
        task_id="start_pipeline",
        dag=source_dag,
    )

    # Ingestion Task
    ingestion_task = PythonOperator(
        task_id=f"ingest_{source_name}",
        python_callable=make_ingest_callable(module_path, function_name),
        dag=source_dag,
    )

    # Validation
    validate_task = PythonOperator(
        task_id="validate_ingestion",
        python_callable=make_validate_callable(source_name),
        dag=source_dag,
    )

    # Pipeline End
    end_task = PythonOperator(
        task_id="pipeline_completion",
        python_callable=make_completion_callable(source_name),
        dag=source_dag,
    )

    # Trigger Preprocessing via N8N
    trigger_preprocessing = PythonOperator(
        task_id="trigger_preprocessing",
        python_callable=make_n8n_trigger_callable(source_name),
        dag=source_dag,
    )

    # === Task Dependencies ===
    start_task >> ingestion_task >> validate_task >> end_task >> trigger_preprocessing

    # Register the DAG in globals
    globals()[f"cti_pipeline_{source_name}"] = source_dag
