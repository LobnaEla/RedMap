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

# Add project root to PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "../cti_pipeline"))

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Only import lightweight modules at the top level
# Heavy imports will be done inside task functions

# DAG configuration with Celery-specific settings
default_args = {
    "owner": "wevioo",
    "depends_on_past": False,
    "start_date": datetime(2023, 7, 6),  # Using past date to ensure DAG is immediately available
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),  # Add execution timeout
    "task_concurrency": 1,  # Limit concurrent executions for this task type
}

# DAG definition with explicit tags for better visibility and Celery optimization
dag = DAG(
    "cti_ingestion_pipeline",
    default_args=default_args,
    description="CTI ingestion pipeline",
    schedule="@hourly",  # Using cron preset instead of timedelta
    catchup=False,
    max_active_runs=1,
    max_active_tasks=8,  # Limit concurrent tasks to prevent resource exhaustion
    tags=["cti", "ingestion", "pipeline"],
    # Add DAG-level configuration for better Celery handling
    doc_md="""
    ## CTI Ingestion Pipeline
    
    This DAG performs cyber threat intelligence data ingestion from multiple sources.
    
    ### Task Dependencies:
    1. validate_environment - Validates system environment and permissions
    2. ingest_* tasks - Parallel ingestion from various sources
    3. Data processing and storage
    
    ### Celery Configuration:
    - Uses CeleryExecutor for distributed task execution
    - Tasks are configured with timeouts and retry logic
    - Environment validation ensures worker nodes have proper setup
    """,
)

# Data directories
DATA_DIR = "/opt/airflow/cti_pipeline/data/"
METADATA_DIR = "/opt/airflow/cti_pipeline/metadata/"
PDF_DIR = "/opt/airflow/cti_pipeline/PDFs/"

def ensure_directories():
    """Ensure required directories exist with better error handling"""
    directories = [DATA_DIR, METADATA_DIR, PDF_DIR]
    created_dirs = []
    failed_dirs = []
    
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                created_dirs.append(directory)
                logger.info(f"✅ Directory created: {directory}")
            else:
                logger.info(f"✅ Directory exists: {directory}")
                
            # Test write permissions
            test_file = os.path.join(directory, ".test_write")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as write_error:
                failed_dirs.append(f"{directory} (write test failed: {write_error})")
                
        except PermissionError as e:
            error_msg = f"Permission denied creating {directory}: {e}"
            logger.error(f"❌ {error_msg}")
            failed_dirs.append(error_msg)
        except OSError as e:
            error_msg = f"OS error creating {directory}: {e}"
            logger.error(f"❌ {error_msg}")
            failed_dirs.append(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error with {directory}: {e}"
            logger.error(f"❌ {error_msg}")
            failed_dirs.append(error_msg)
    
    if failed_dirs:
        raise RuntimeError(f"Failed to setup directories: {failed_dirs}")
    
    return {"created": created_dirs, "verified": directories}

def validate_environment():
    """Validate environment variables and dependencies with detailed reporting"""
    issues = []
    warnings = []
    
    # Check if OTX API key is available for OTX tasks
    otx_key = os.getenv("OTX_API_KEY")
    if not otx_key:
        issues.append("OTX_API_KEY environment variable not set - OTX ingestion will fail")
    elif len(otx_key.strip()) < 10:  # Basic validation
        warnings.append("OTX_API_KEY seems too short - please verify it's correct")
    else:
        logger.info("✅ OTX_API_KEY is set and appears valid")
    
    # Check PYTHONPATH
    python_path = os.getenv("PYTHONPATH", "")
    if not python_path:
        warnings.append("PYTHONPATH not set - imports may fail")
    elif "cti_pipeline" not in python_path:
        warnings.append("cti_pipeline not found in PYTHONPATH - imports may fail")
    else:
        logger.info("✅ PYTHONPATH includes cti_pipeline")
    
    # Check if required directories are accessible and writable
    directory_checks = [
        ("DATA_DIR", DATA_DIR), 
        ("METADATA_DIR", METADATA_DIR), 
        ("PDF_DIR", PDF_DIR)
    ]
    
    for dir_name, dir_path in directory_checks:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"✅ Created missing directory {dir_name}: {dir_path}")
            except Exception as e:
                issues.append(f"Cannot create {dir_name}: {dir_path} - {str(e)}")
                continue
        
        # Check write permissions
        if not os.access(dir_path, os.W_OK):
            issues.append(f"{dir_name} is not writable: {dir_path}")
        else:
            logger.info(f"✅ {dir_name} is writable: {dir_path}")
    
    # Log results
    if issues:
        logger.error(f"❌ Environment validation found {len(issues)} critical issues: {issues}")
    if warnings:
        logger.warning(f"⚠️ Environment validation found {len(warnings)} warnings: {warnings}")
    if not issues and not warnings:
        logger.info("✅ Environment validation passed with no issues")
    
    return {"issues": issues, "warnings": warnings}

# Adding a simple test task to ensure DAG is loaded
@task(task_id="test_task")
def test_task():
    logger.info("Test task is running!")
    return "Task completed successfully"

@task(
    task_id="validate_environment",
    execution_timeout=timedelta(minutes=10),
    retries=1,
    retry_delay=timedelta(minutes=2),
    pool="default_pool",
    priority_weight=10,  # High priority for validation task
)
def validate_environment_task():
    """Validate environment before running ingestion tasks"""
    import os
    import logging
    from datetime import datetime
    
    # Use task instance logger for better integration with Airflow
    logger = logging.getLogger(__name__)
    logger.info("🔍 Starting environment validation...")
    
    validation_results = {
        "task": "validate_environment",
        "status": "success",
        "issues": [],
        "directories": {},
        "environment_vars": {},
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        # Directory validation with detailed error handling
        directories_to_check = {
            "DATA_DIR": "/opt/airflow/cti_pipeline/data/",
            "METADATA_DIR": "/opt/airflow/cti_pipeline/metadata/",
            "PDF_DIR": "/opt/airflow/cti_pipeline/PDFs/"
        }
        
        for dir_name, dir_path in directories_to_check.items():
            dir_status = {"path": dir_path, "exists": False, "writable": False, "created": False}
            
            try:
                # Check if directory exists
                if os.path.exists(dir_path):
                    dir_status["exists"] = True
                    logger.info(f"✅ Directory exists: {dir_path}")
                else:
                    logger.info(f"� Creating directory: {dir_path}")
                    os.makedirs(dir_path, exist_ok=True)
                    dir_status["created"] = True
                    dir_status["exists"] = True
                    logger.info(f"✅ Directory created: {dir_path}")
                
                # Check if directory is writable
                if os.access(dir_path, os.W_OK):
                    dir_status["writable"] = True
                    logger.info(f"✅ Directory is writable: {dir_path}")
                else:
                    error_msg = f"Directory is not writable: {dir_path}"
                    logger.error(f"❌ {error_msg}")
                    validation_results["issues"].append(error_msg)
                    
                # Test write permissions by creating a test file
                test_file = os.path.join(dir_path, ".airflow_test_write")
                try:
                    with open(test_file, 'w') as f:
                        f.write("test")
                    os.remove(test_file)
                    dir_status["write_test"] = True
                    logger.info(f"✅ Write test successful: {dir_path}")
                except Exception as write_error:
                    dir_status["write_test"] = False
                    error_msg = f"Write test failed for {dir_path}: {str(write_error)}"
                    logger.error(f"❌ {error_msg}")
                    validation_results["issues"].append(error_msg)
                    
            except OSError as e:
                error_msg = f"Failed to handle directory {dir_path}: {str(e)} (Error code: {e.errno})"
                logger.error(f"❌ {error_msg}")
                validation_results["issues"].append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error with directory {dir_path}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                validation_results["issues"].append(error_msg)
                
            validation_results["directories"][dir_name] = dir_status
        
        # Environment variable validation
        env_vars_to_check = ["OTX_API_KEY", "PYTHONPATH"]
        
        for env_var in env_vars_to_check:
            env_value = os.getenv(env_var)
            if env_value:
                validation_results["environment_vars"][env_var] = {
                    "set": True,
                    "value_length": len(env_value),
                    "value_preview": env_value[:10] + "..." if len(env_value) > 10 else env_value
                }
                logger.info(f"✅ Environment variable {env_var} is set")
            else:
                validation_results["environment_vars"][env_var] = {"set": False}
                if env_var == "OTX_API_KEY":
                    error_msg = f"Required environment variable {env_var} is not set"
                    logger.error(f"❌ {error_msg}")
                    validation_results["issues"].append(error_msg)
                else:
                    warning_msg = f"Optional environment variable {env_var} is not set"
                    logger.warning(f"⚠️ {warning_msg}")
        
        # Additional system checks
        try:
            # Check available disk space
            import shutil
            for dir_name, dir_path in directories_to_check.items():
                if os.path.exists(dir_path):
                    total, used, free = shutil.disk_usage(dir_path)
                    free_gb = free // (1024**3)
                    validation_results["directories"][dir_name]["free_space_gb"] = free_gb
                    if free_gb < 1:  # Less than 1GB free
                        warning_msg = f"Low disk space for {dir_path}: {free_gb}GB free"
                        logger.warning(f"⚠️ {warning_msg}")
                        validation_results["issues"].append(warning_msg)
                    else:
                        logger.info(f"✅ Sufficient disk space for {dir_path}: {free_gb}GB free")
        except Exception as space_error:
            logger.warning(f"⚠️ Could not check disk space: {str(space_error)}")
        
        # Check Python path accessibility
        try:
            python_path = os.getenv("PYTHONPATH", "")
            if python_path:
                import sys
                if "/opt/airflow/cti_pipeline" in python_path or "cti_pipeline" in python_path:
                    logger.info("✅ CTI pipeline is in PYTHONPATH")
                else:
                    warning_msg = "CTI pipeline directory may not be in PYTHONPATH"
                    logger.warning(f"⚠️ {warning_msg}")
                    validation_results["issues"].append(warning_msg)
        except Exception as path_error:
            logger.warning(f"⚠️ Could not validate PYTHONPATH: {str(path_error)}")
        
        # Determine final status
        if validation_results["issues"]:
            critical_issues = [issue for issue in validation_results["issues"] 
                             if "not writable" in issue or "Failed to handle directory" in issue or "OTX_API_KEY" in issue]
            if critical_issues:
                validation_results["status"] = "failed"
                logger.error(f"❌ Environment validation failed with {len(critical_issues)} critical issues")
            else:
                validation_results["status"] = "warning"
                logger.warning(f"⚠️ Environment validation completed with {len(validation_results['issues'])} warnings")
        else:
            logger.info("✅ Environment validation completed successfully")
        
        logger.info(f"📊 Validation summary: {len(validation_results['issues'])} issues found")
        
        return validation_results
        
    except Exception as e:
        import traceback
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        logger.error(f"❌ Environment validation failed with unexpected error: {error_details}")
        
        # Return detailed error information instead of raising
        validation_results.update({
            "status": "error",
            "error_details": error_details
        })
        
        # Only raise if it's a critical system error
        if isinstance(e, (SystemError, MemoryError)):
            raise RuntimeError(f"Critical system error during environment validation: {str(e)}")
        
        return validation_results

# Add the test task to the DAG
test_task_instance = test_task()

# This ensures that the DAG is properly loaded into Airflow
# Keep this at the bottom of the file
if __name__ != "__main__":
    # The remaining tasks and code will be kept as is
    pass


# Ingestion tasks
@task()
def ingest_rss_feed():
    """Airflow task for CERT-FR RSS ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.ingest_rss import ingest_certfr_rss

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting RSS ingestion")

    try:
        # Ensure directories exist
        ensure_directories()
        
        result = ingest_certfr_rss(DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(result, dict) or 'processed' not in result or 'total' not in result:
            raise ValueError(f"Invalid result format from RSS ingestion: {result}")
        
        logger.info(
            f"✅ RSS: {result['processed']} new bulletins collected (out of {result['total']})"
        )
        
        # Return structured result for Airflow
        return {
            "task": "ingest_rss_feed",
            "status": "success",
            "processed": result['processed'],
            "total": result['total'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ RSS ingestion failed: {str(e)}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"RSS ingestion failed: {str(e)}")


@task()
def ingest_tuncert_vulnerabilities_task():
    """Airflow task for TUNCERT ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.ingest_tuncert import ingest_tuncert_vulnerabilities

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting TUNCERT ingestion")

    try:
        # Ensure directories exist
        ensure_directories()
        
        result = ingest_tuncert_vulnerabilities(DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(result, dict) or 'processed' not in result or 'total' not in result:
            raise ValueError(f"Invalid result format from TUNCERT ingestion: {result}")
        
        logger.info(
            f"✅ TUNCERT: {result['processed']} new vulnerabilities collected (out of {result['total']})"
        )
        
        # Return structured result for Airflow
        return {
            "task": "ingest_tuncert_vulnerabilities",
            "status": "success",
            "processed": result['processed'],
            "total": result['total'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ TUNCERT ingestion failed: {str(e)}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"TUNCERT ingestion failed: {str(e)}")


@task()
def ingest_otx_task():
    """Airflow task for OTX pulse ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.ingest_otx import (
        ingest_otx_pulses as ingest_otx_pulses_func,
    )

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting OTX ingestion")

    try:
        # Check if OTX API key is available
        if not os.getenv("OTX_API_KEY"):
            logger.warning("⚠️ OTX_API_KEY not found, skipping OTX ingestion")
            return {
                "task": "ingest_otx_pulses",
                "status": "skipped",
                "reason": "OTX_API_KEY not configured",
                "processed": 0,
                "total": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Ensure directories exist
        ensure_directories()
        
        result = ingest_otx_pulses_func(DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(result, dict) or 'processed' not in result or 'total' not in result:
            raise ValueError(f"Invalid result format from OTX ingestion: {result}")
        
        logger.info(
            f"✅ OTX: {result['processed']} new pulses collected (out of {result['total']})"
        )
        
        # Return structured result for Airflow
        return {
            "task": "ingest_otx_pulses",
            "status": "success",
            "processed": result['processed'],
            "total": result['total'],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ OTX ingestion failed: {str(e)}")
        # Log additional info for debugging
        logger.error(f"Exception type: {type(e).__name__}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"OTX ingestion failed: {str(e)}")


@task()
def ingest_twitter_data():
    """Tâche Airflow pour l'ingestion Twitter"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.ingest_twitter_users import ingest_all_twitter_users

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting Twitter ingestion")

    users = ["vxunderground", "CERT_FR", "CISACyber"]

    try:
        # Ensure directories exist
        ensure_directories()
        
        result = ingest_all_twitter_users(users, DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(result, dict):
            raise ValueError(f"Invalid result format from Twitter ingestion: {result}")
        
        logger.info(f"✅ Twitter: {result.get('processed', 0)} nouveaux tweets collectés")
        logger.info(f"👤 Utilisateurs traités: {result.get('users', [])}")
        
        # Return structured result for Airflow
        return {
            "task": "ingest_twitter_data",
            "status": "success",
            "processed": result.get('processed', 0),
            "users": result.get('users', []),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Échec de l'ingestion Twitter: {str(e)}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"Twitter ingestion failed: {str(e)}")


@task()
def ingest_blog_articles():
    """Airflow task for blog ingestion"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.scraper_blog import ingest_all_blog
    from cti_pipeline.blog_sources import BLOG_SOURCES

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting blogs ingestion")

    try:
        # Ensure directories exist
        ensure_directories()
        
        total_processed = ingest_all_blog(BLOG_SOURCES, DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(total_processed, int):
            raise ValueError(f"Invalid result format from blog ingestion: {total_processed}")
        
        logger.info(f"✅ Blogs: {total_processed} articles processed")
        
        # Return structured result for Airflow
        return {
            "task": "ingest_blog_articles",
            "status": "success",
            "processed": total_processed,
            "sources": len(BLOG_SOURCES),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Blog ingestion failed: {str(e)}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"Blog ingestion failed: {str(e)}")


@task()
def ingest_pdf_reports():
    """Ingest PDF threat reports"""
    # Import inside task to avoid slow DAG loading
    from cti_pipeline.scripts.Ingestion.ingest_pdf import ingest_all_pdfs

    logger = logging.getLogger("airflow.task")
    logger.info("🔄 Starting PDF ingestion")

    try:
        # Ensure directories exist
        ensure_directories()
        
        # Call the function that handles ingestion of all PDFs
        total_new_pdfs = ingest_all_pdfs(PDF_DIR, DATA_DIR, METADATA_DIR)
        
        # Validate result
        if not isinstance(total_new_pdfs, int):
            raise ValueError(f"Invalid result format from PDF ingestion: {total_new_pdfs}")
        
        logger.info(f"✅ PDFs: {total_new_pdfs} new reports processed")
        
        # Return structured result for Airflow
        return {
            "task": "ingest_pdf_reports",
            "status": "success",
            "processed": total_new_pdfs,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Error during PDF ingestion: {e}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"PDF ingestion failed: {str(e)}")


@task()
def cleanup_old_data():
    """Nettoyage des anciens fichiers de données (> 30 jours)."""
    logger = logging.getLogger("airflow.task")
    logger.info("🧹 Nettoyage des anciennes données")

    try:
        import time

        current_time = time.time()
        retention_days = 30
        retention_seconds = retention_days * 24 * 60 * 60

        cleaned_files = 0

        for root, dirs, files in os.walk(DATA_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_age = current_time - os.path.getctime(file_path)

                    if file_age > retention_seconds:
                        os.remove(file_path)
                        cleaned_files += 1
                        logger.info(f"🗑️ Fichier supprimé: {file}")
                except (OSError, FileNotFoundError) as e:
                    logger.warning(f"Could not process file {file_path}: {e}")
                    continue

        logger.info(f"✅ Nettoyage terminé: {cleaned_files} fichiers supprimés")
        
        # Return structured result for Airflow
        return {
            "task": "cleanup_old_data",
            "status": "success",
            "cleaned_files": cleaned_files,
            "retention_days": retention_days,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Erreur nettoyage: {e}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"Cleanup failed: {str(e)}")


@task()
def generate_ingestion_report():
    """Génération d'un rapport d'ingestion."""
    logger = logging.getLogger("airflow.task")
    logger.info("📊 Génération rapport d'ingestion")

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
                    try:
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
                    except (OSError, FileNotFoundError) as e:
                        logger.warning(f"Could not process file {file_path}: {e}")
                        continue

        # Sauvegarder le rapport
        report_file = os.path.join(
            METADATA_DIR,
            f"ingestion_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        )
        
        # Ensure metadata directory exists
        os.makedirs(METADATA_DIR, exist_ok=True)
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ Rapport sauvegardé: {report_file}")
        logger.info(
            f"📈 Total: {report['total_files']} fichiers, {report['total_size_mb']:.2f} MB"
        )
        
        # Return structured result for Airflow
        return {
            "task": "generate_ingestion_report",
            "status": "success",
            "report_file": report_file,
            "total_files": report["total_files"],
            "total_size_mb": round(report["total_size_mb"], 2),
            "sources": list(report["sources_status"].keys()),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Erreur génération rapport: {e}")
        # Re-raise to mark task as failed
        raise RuntimeError(f"Report generation failed: {str(e)}")


@task()
def preprocess_cti_data():
    """Placeholder for CTI preprocessing - currently disabled"""
    logger = logging.getLogger("airflow.task")
    logger.info("📝 Preprocessing task skipped - focusing on ingestion only")
    return {"status": "skipped", "reason": "preprocessing_disabled"}


# Définition des tâches du DAG
with dag:
    # Environment validation task first
    validate_env_task = validate_environment_task()
    
    # Tâches d'ingestion en parallèle
    rss_task = ingest_rss_feed()
    tuncert_task = ingest_tuncert_vulnerabilities_task()
    otx_task = ingest_otx_task()
    twitter_task = ingest_twitter_data()
    blog_task = ingest_blog_articles()
    pdf_task = ingest_pdf_reports()

    # Tâches de maintenance
    cleanup_task = cleanup_old_data()
    report_task = generate_ingestion_report()
    preprocess_task = preprocess_cti_data()

    # Définition des dépendances
    # Environment validation first, then all ingestion tasks in parallel
    validate_env_task >> [rss_task, tuncert_task, otx_task, twitter_task, blog_task, pdf_task]
    
    # After all ingestion tasks complete
    (
        [rss_task, tuncert_task, otx_task, twitter_task, blog_task, pdf_task]
        >> preprocess_task  # Process data after ingestion
        >> cleanup_task     # Clean up after processing
        >> report_task      # Generate final report
    )
