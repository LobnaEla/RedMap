"""
This DAG contains a basic task that prints a message to test if DAGs work correctly.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'cti-pipeline',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'test_dag',
    default_args=default_args,
    description='A simple test DAG to verify Airflow setup',
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=['test', 'cti-pipeline'],
)

def print_hello_world():
    """Simple function that prints a test message"""
    print("Hello from Airflow 2.11!")
    print("DAG is working correctly!")
    print("CTI Pipeline orchestration is ready!")
    return "Task completed successfully"

def print_system_info():
    """Print some system information"""
    import sys
    import platform
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Current time: {datetime.now()}")
    print("Airflow is configured and running!")
    return "System info printed"

def print_completion():
    """Print completion message"""
    print("Test DAG completed successfully!")
    print("Airflow 2.11 setup is working properly.")
    return "Test completed"

# Define tasks
hello_task = PythonOperator(
    task_id='print_hello_world',
    python_callable=print_hello_world,
    dag=dag,
)

system_info_task = PythonOperator(
    task_id='print_system_info',
    python_callable=print_system_info,
    dag=dag,
)

completion_task = PythonOperator(
    task_id='print_completion',
    python_callable=print_completion,
    dag=dag,
)

# Set task dependencies
hello_task >> system_info_task >> completion_task
