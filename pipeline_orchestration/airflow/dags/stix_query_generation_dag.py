"""
STIX Query Generation DAG: Transform Judge Validation Results to Operational Queries

This DAG fetches the final validated techniques from the LLM-as-a-Judge unified analysis
and generates:
1. KQL queries for Microsoft Sentinel
2. Sigma rules for generic SIEM platforms  
3. STIX-formatted indicators for threat intelligence sharing

Pipeline: Judge Results → MITRE Techniques → Query Generation → STIX Format
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from datetime import datetime, timedelta
import os
import sys
import json
import glob
import requests
from typing import Dict, List, Optional, Any

# Add project paths
sys.path.append("/opt/airflow/dags/Implementation")
sys.path.append("/opt/airflow/dags/Implementation/stix-query-generator")

# Import STIX query generator components
try:
    from query_generator import QueryGenerator
    from models import STIXObjectCreate, KQLQueryResponse, SigmaRuleResponse
    from services import STIXService
    from database import SessionLocal
    STIX_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"[STIX-DAG] Warning: STIX components not available: {e}")
    STIX_COMPONENTS_AVAILABLE = False

# === Path Configuration ===
BASE_PROJECT_PATH = "/opt/airflow/dags/Implementation/cti_pipeline"
DATA_DIR = os.path.join(BASE_PROJECT_PATH, "data")
UNIFIED_RESULTS_DIR = os.path.join(DATA_DIR, "unified_analysis_results")
JUDGE_RESULTS_DIR = os.path.join(DATA_DIR, "judge_results")  # Docker Airflow environment path
STIX_QUERIES_DIR = os.path.join(DATA_DIR, "stix_queries")
MITRE_DATA_DIR = os.path.join("/opt/airflow/dags/Implementation/data/MITRE_ATT&CK")
LOGS_DIR = os.path.join(BASE_PROJECT_PATH, "logs")

# API Configuration  
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MITRE_API_URL = "https://attack.mitre.org/api/v1/techniques"

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

# === DAG Configuration ===
default_args = {
    "owner": "cti-stix-queries",
    "depends_on_past": False,
    "start_date": datetime(2025, 8, 7),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

dag = DAG(
    "stix_query_generation_dag",
    default_args=default_args,
    description="Generate KQL, Sigma, and STIX queries from judge validation results",
    schedule_interval=None,  # Manual trigger
    catchup=False,
    max_active_runs=1,
    tags=["cti", "stix", "kql", "sigma", "queries", "judge"],
)


# ================================
# CORE TASK FUNCTIONS
# ================================

def fetch_judge_validation_results():
    """Fetch and aggregate final validated techniques from judge results"""
    print("[STIX-QUERIES] Fetching judge validation results...")
    
    # Create output directory
    os.makedirs(STIX_QUERIES_DIR, exist_ok=True)
    
    # Find judge result files from unified DAG output (format: judge_{base_name}.json)
    judge_files = glob.glob(os.path.join(JUDGE_RESULTS_DIR, "judge_*.json"))
    
    if not judge_files:
        print("[STIX-QUERIES] No judge result files found")
        return {
            "status": "no_data",
            "message": "No judge validation results found"
        }
    
    print(f"[STIX-QUERIES] Found {len(judge_files)} judge result files")
    
    # Aggregate all validated techniques
    all_validated_techniques = {}
    technique_sources = {}  # Track which files contributed each technique
    total_chunks_processed = 0
    successful_files = 0
    
    for judge_file in judge_files:
        try:
            print(f"[STIX-QUERIES] Processing: {os.path.basename(judge_file)}")
            
            with open(judge_file, "r", encoding="utf-8") as f:
                judge_data = json.load(f)
            
            # Check if judge processing was successful
            if not judge_data.get("judge_processing_complete", False):
                print(f"[STIX-QUERIES] Skipping incomplete file: {judge_file}")
                continue
            
            # Extract validation results (structure from unified DAG)
            validation_results = judge_data.get("validation_results", {})
            validations = validation_results.get("validations", [])
            
            file_chunks = 0
            file_techniques = set()
            
            for validation in validations:
                if validation.get("success", False):
                    chunk_id = validation["chunk_id"]
                    techniques = validation.get("final_validated_techniques", [])
                    
                    if techniques:  # Only process chunks with validated techniques
                        all_validated_techniques[chunk_id] = techniques
                        file_techniques.update(techniques)
                        file_chunks += 1
                        
                        # Track sources
                        for technique in techniques:
                            if technique not in technique_sources:
                                technique_sources[technique] = []
                            technique_sources[technique].append(os.path.basename(judge_file))
            
            total_chunks_processed += file_chunks
            successful_files += 1
            print(f"[STIX-QUERIES] ✅ Processed {file_chunks} chunks, {len(file_techniques)} unique techniques")
            
        except Exception as e:
            print(f"[STIX-QUERIES] Error processing {judge_file}: {e}")
            continue
    
    # Prepare aggregation results  
    unique_techniques = set()
    for chunk_techniques in all_validated_techniques.values():
        unique_techniques.update(chunk_techniques)
    
    aggregation_results = {
        "processing_timestamp": datetime.now().isoformat(),
        "source_judge_files": len(judge_files),
        "successful_judge_files": successful_files,
        "total_chunks_processed": total_chunks_processed,
        "unique_techniques_validated": len(unique_techniques),
        "validated_techniques_by_chunk": all_validated_techniques,
        "all_unique_techniques": sorted(list(unique_techniques)),
        "technique_sources": {tech: list(sources) for tech, sources in technique_sources.items()}
    }
    
    # Save aggregated results
    aggregation_file = os.path.join(STIX_QUERIES_DIR, "judge_techniques_aggregation.json")
    with open(aggregation_file, "w", encoding="utf-8") as f:
        json.dump(aggregation_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] Aggregation complete:")
    print(f"  - Files processed: {successful_files}/{len(judge_files)}")
    print(f"  - Chunks processed: {total_chunks_processed}")
    print(f"  - Unique techniques: {len(unique_techniques)}")
    print(f"  - Techniques: {sorted(list(unique_techniques))}")
    print(f"  - Results saved to: {aggregation_file}")
    
    return aggregation_results

def enrich_with_mitre_data(**context):
    """Enrich validated techniques with full MITRE ATT&CK data"""
    print("[STIX-QUERIES] Enriching techniques with MITRE ATT&CK data...")
    
    # Load aggregated judge results
    aggregation_file = os.path.join(STIX_QUERIES_DIR, "judge_techniques_aggregation.json")
    try:
        with open(aggregation_file, "r", encoding="utf-8") as f:
            aggregation_data = json.load(f)
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading aggregation data: {e}")
        return {"status": "error", "message": "Could not load technique aggregation data"}
    
    validated_techniques_by_chunk = aggregation_data.get("validated_techniques_by_chunk", {})
    all_unique_techniques = aggregation_data.get("all_unique_techniques", [])
    
    if not all_unique_techniques:
        print("[STIX-QUERIES] No validated techniques to enrich")
        return {"status": "no_data", "message": "No validated techniques found"}
    
    # Try to load local MITRE data first
    mitre_data = {}
    local_mitre_file = os.path.join(MITRE_DATA_DIR, "enterprise-attack.json")
    
    if os.path.exists(local_mitre_file):
        try:
            print(f"[STIX-QUERIES] Loading local MITRE data from: {local_mitre_file}")
            with open(local_mitre_file, "r", encoding="utf-8") as f:
                local_data = json.load(f)
            
            # Parse STIX objects for techniques
            for obj in local_data.get("objects", []):
                if obj.get("type") == "attack-pattern":
                    external_refs = obj.get("external_references", [])
                    for ref in external_refs:
                        if ref.get("source_name") == "mitre-attack":
                            technique_id = ref.get("external_id", "")
                            if technique_id:
                                mitre_data[technique_id] = obj
                                break
            
            print(f"[STIX-QUERIES] Loaded {len(mitre_data)} techniques from local MITRE data")
        
        except Exception as e:
            print(f"[STIX-QUERIES] Error loading local MITRE data: {e}")
    
    # Enrich each validated technique
    enriched_techniques = {}
    missing_techniques = []
    
    for technique_id in all_unique_techniques:
        # Create basic technique data structure
        technique_data = {
            "technique_id": technique_id,
            "source_chunks": [],
            "occurrence_count": 0
        }
        
        # Count occurrences across all chunks
        for chunk_id, chunk_techniques in validated_techniques_by_chunk.items():
            if technique_id in chunk_techniques:
                technique_data["occurrence_count"] += 1
                technique_data["source_chunks"].append(chunk_id)
        
        # Add MITRE data if available
        if technique_id in mitre_data:
            mitre_technique = mitre_data[technique_id]
            technique_data.update({
                "mitre_name": mitre_technique.get("name", ""),
                "mitre_description": mitre_technique.get("description", ""),
                "kill_chain_phases": mitre_technique.get("kill_chain_phases", []),
                "platforms": mitre_technique.get("x_mitre_platforms", []),
                "data_sources": mitre_technique.get("x_mitre_data_sources", []),
                "detection_notes": mitre_technique.get("x_mitre_detection", ""),
                "mitre_version": mitre_technique.get("modified", ""),
                "external_references": mitre_technique.get("external_references", []),
                "full_stix_object": mitre_technique
            })
        else:
            missing_techniques.append(technique_id)
            # Add placeholder data for missing techniques
            technique_data.update({
                "mitre_name": f"Unknown Technique {technique_id}",
                "mitre_description": "Technique data not available in local MITRE dataset",
                "kill_chain_phases": [],
                "platforms": [],
                "data_sources": [],
                "detection_notes": "",
                "mitre_version": "",
                "external_references": [],
                "full_stix_object": None
            })
        
        enriched_techniques[technique_id] = technique_data
    
    # Prepare enrichment results
    enrichment_results = {
        "processing_timestamp": datetime.now().isoformat(),
        "total_techniques": len(all_unique_techniques),
        "enriched_techniques": len(enriched_techniques) - len(missing_techniques),
        "missing_techniques": len(missing_techniques),
        "missing_technique_ids": missing_techniques,
        "enriched_data": enriched_techniques,
        "mitre_data_source": "local" if mitre_data else "none"
    }
    
    # Save enriched results
    enrichment_file = os.path.join(STIX_QUERIES_DIR, "mitre_enriched_techniques.json")
    with open(enrichment_file, "w", encoding="utf-8") as f:
        json.dump(enrichment_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] MITRE enrichment complete:")
    print(f"  - Total techniques: {len(all_unique_techniques)}")
    print(f"  - Successfully enriched: {len(enriched_techniques) - len(missing_techniques)}")
    print(f"  - Missing MITRE data: {len(missing_techniques)}")
    if missing_techniques:
        print(f"  - Missing IDs: {missing_techniques[:5]}{'...' if len(missing_techniques) > 5 else ''}")
    print(f"  - Results saved to: {enrichment_file}")
    
    return enrichment_results

def generate_kql_queries(**context):
    """Generate KQL queries for Microsoft Sentinel"""
    print("[STIX-QUERIES] Generating KQL queries...")
    
    if not STIX_COMPONENTS_AVAILABLE:
        print("[STIX-QUERIES] STIX components not available, generating basic KQL queries")
        return _generate_basic_kql_queries()
    
    # Load enriched techniques
    enrichment_file = os.path.join(STIX_QUERIES_DIR, "mitre_enriched_techniques.json")
    try:
        with open(enrichment_file, "r", encoding="utf-8") as f:
            enrichment_data = json.load(f)
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading enrichment data: {e}")
        return {"status": "error", "message": "Could not load enriched technique data"}
    
    enriched_techniques = enrichment_data.get("enriched_data", {})
    
    if not enriched_techniques:
        print("[STIX-QUERIES] No enriched techniques available")
        return {"status": "no_data", "message": "No enriched techniques found"}
    
    # Initialize query generator
    try:
        query_generator = QueryGenerator()
    except Exception as e:
        print(f"[STIX-QUERIES] Error initializing QueryGenerator: {e}")
        return _generate_basic_kql_queries()
    
    # Generate KQL queries for each technique
    kql_results = {
        "generation_timestamp": datetime.now().isoformat(),
        "total_techniques": len(enriched_techniques),
        "successful_queries": 0,
        "failed_queries": 0,
        "kql_queries": {},
        "generation_errors": []
    }
    
    for technique_id, technique_data in enriched_techniques.items():
        try:
            print(f"[STIX-QUERIES] Generating KQL for {technique_id}: {technique_data.get('mitre_name', 'Unknown')}")
            
            # Prepare STIX data for query generation
            stix_data = {
                "name": technique_data.get("mitre_name", technique_id),
                "description": technique_data.get("mitre_description", ""),
                "kill_chain_phases": technique_data.get("kill_chain_phases", []),
                "x_mitre_platforms": technique_data.get("platforms", []),
                "x_mitre_data_sources": technique_data.get("data_sources", []),
                "x_mitre_detection": technique_data.get("detection_notes", "")
            }
            
            # Generate KQL query
            kql_result = query_generator.generate_kql_query(stix_data, technique_id)
            
            # Add judge validation metadata
            kql_result["judge_metadata"] = {
                "occurrence_count": technique_data.get("occurrence_count", 0),
                "average_confidence": technique_data.get("average_confidence", 0.0),
                "source_files": technique_data.get("source_files", []),
                "source_chunks": len(technique_data.get("source_chunks", []))
            }
            
            kql_results["kql_queries"][technique_id] = kql_result
            kql_results["successful_queries"] += 1
            
        except Exception as e:
            error_msg = f"Failed to generate KQL for {technique_id}: {str(e)}"
            print(f"[STIX-QUERIES] {error_msg}")
            kql_results["generation_errors"].append({
                "technique_id": technique_id,
                "error": error_msg
            })
            kql_results["failed_queries"] += 1
    
    # Save KQL results
    kql_file = os.path.join(STIX_QUERIES_DIR, "generated_kql_queries.json")
    with open(kql_file, "w", encoding="utf-8") as f:
        json.dump(kql_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] KQL generation complete:")
    print(f"  - Total techniques: {len(enriched_techniques)}")
    print(f"  - Successful queries: {kql_results['successful_queries']}")
    print(f"  - Failed queries: {kql_results['failed_queries']}")
    print(f"  - Results saved to: {kql_file}")
    
    return kql_results

def generate_sigma_rules(**context):
    """Generate Sigma rules for generic SIEM platforms"""
    print("[STIX-QUERIES] Generating Sigma rules...")
    
    if not STIX_COMPONENTS_AVAILABLE:
        print("[STIX-QUERIES] STIX components not available, generating basic Sigma rules")
        return _generate_basic_sigma_rules()
    
    # Load enriched techniques
    enrichment_file = os.path.join(STIX_QUERIES_DIR, "mitre_enriched_techniques.json")
    try:
        with open(enrichment_file, "r", encoding="utf-8") as f:
            enrichment_data = json.load(f)
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading enrichment data: {e}")
        return {"status": "error", "message": "Could not load enriched technique data"}
    
    enriched_techniques = enrichment_data.get("enriched_data", {})
    
    if not enriched_techniques:
        print("[STIX-QUERIES] No enriched techniques available")
        return {"status": "no_data", "message": "No enriched techniques found"}
    
    # Initialize query generator
    try:
        query_generator = QueryGenerator()
    except Exception as e:
        print(f"[STIX-QUERIES] Error initializing QueryGenerator: {e}")
        return _generate_basic_sigma_rules()
    
    # Generate Sigma rules for each technique
    sigma_results = {
        "generation_timestamp": datetime.now().isoformat(),
        "total_techniques": len(enriched_techniques),
        "successful_rules": 0,
        "failed_rules": 0,
        "sigma_rules": {},
        "generation_errors": []
    }
    
    for technique_id, technique_data in enriched_techniques.items():
        try:
            print(f"[STIX-QUERIES] Generating Sigma rule for {technique_id}: {technique_data.get('mitre_name', 'Unknown')}")
            
            # Prepare STIX data for rule generation
            stix_data = {
                "name": technique_data.get("mitre_name", technique_id),
                "description": technique_data.get("mitre_description", ""),
                "kill_chain_phases": technique_data.get("kill_chain_phases", []),
                "x_mitre_platforms": technique_data.get("platforms", []),
                "x_mitre_data_sources": technique_data.get("data_sources", []),
                "x_mitre_detection": technique_data.get("detection_notes", "")
            }
            
            # Generate Sigma rule
            sigma_result = query_generator.generate_sigma_rule(stix_data, technique_id)
            
            # Add judge validation metadata
            sigma_result["judge_metadata"] = {
                "occurrence_count": technique_data.get("occurrence_count", 0),
                "average_confidence": technique_data.get("average_confidence", 0.0),
                "source_files": technique_data.get("source_files", []),
                "source_chunks": len(technique_data.get("source_chunks", []))
            }
            
            sigma_results["sigma_rules"][technique_id] = sigma_result
            sigma_results["successful_rules"] += 1
            
        except Exception as e:
            error_msg = f"Failed to generate Sigma rule for {technique_id}: {str(e)}"
            print(f"[STIX-QUERIES] {error_msg}")
            sigma_results["generation_errors"].append({
                "technique_id": technique_id,
                "error": error_msg
            })
            sigma_results["failed_rules"] += 1
    
    # Save Sigma results
    sigma_file = os.path.join(STIX_QUERIES_DIR, "generated_sigma_rules.json")
    with open(sigma_file, "w", encoding="utf-8") as f:
        json.dump(sigma_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] Sigma rule generation complete:")
    print(f"  - Total techniques: {len(enriched_techniques)}")
    print(f"  - Successful rules: {sigma_results['successful_rules']}")
    print(f"  - Failed rules: {sigma_results['failed_rules']}")
    print(f"  - Results saved to: {sigma_file}")
    
    return sigma_results

def generate_stix_indicators(**context):
    """Generate STIX indicators from queries"""
    print("[STIX-QUERIES] Generating STIX indicators...")
    
    if not STIX_COMPONENTS_AVAILABLE:
        print("[STIX-QUERIES] STIX components not available, skipping STIX generation")
        return {"status": "skipped", "message": "STIX components not available"}
    
    # Load KQL and Sigma results
    try:
        kql_file = os.path.join(STIX_QUERIES_DIR, "generated_kql_queries.json")
        with open(kql_file, "r", encoding="utf-8") as f:
            kql_data = json.load(f)
        
        sigma_file = os.path.join(STIX_QUERIES_DIR, "generated_sigma_rules.json")
        with open(sigma_file, "r", encoding="utf-8") as f:
            sigma_data = json.load(f)
    
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading query data: {e}")
        return {"status": "error", "message": "Could not load query generation results"}
    
    # Initialize query generator
    try:
        query_generator = QueryGenerator()
    except Exception as e:
        print(f"[STIX-QUERIES] Error initializing QueryGenerator: {e}")
        return {"status": "error", "message": "Could not initialize query generator"}
    
    # Generate STIX indicators
    stix_results = {
        "generation_timestamp": datetime.now().isoformat(),
        "total_kql_queries": len(kql_data.get("kql_queries", {})),
        "total_sigma_rules": len(sigma_data.get("sigma_rules", {})),
        "generated_indicators": 0,
        "failed_indicators": 0,
        "stix_indicators": {},
        "generation_errors": []
    }
    
    # Generate STIX indicators for KQL queries
    for technique_id, kql_query_data in kql_data.get("kql_queries", {}).items():
        try:
            kql_query = kql_query_data.get("query", "")
            if kql_query:
                stix_indicator = query_generator.generate_stix_format(
                    query_content=kql_query,
                    query_type="kql",
                    source_technique_id=technique_id
                )
                
                # Add metadata
                stix_indicator["query_metadata"] = kql_query_data.get("metadata", {})
                stix_indicator["judge_metadata"] = kql_query_data.get("judge_metadata", {})
                
                stix_results["stix_indicators"][f"{technique_id}_kql"] = stix_indicator
                stix_results["generated_indicators"] += 1
        
        except Exception as e:
            error_msg = f"Failed to generate STIX for KQL {technique_id}: {str(e)}"
            print(f"[STIX-QUERIES] {error_msg}")
            stix_results["generation_errors"].append({
                "technique_id": technique_id,
                "query_type": "kql",
                "error": error_msg
            })
            stix_results["failed_indicators"] += 1
    
    # Generate STIX indicators for Sigma rules
    for technique_id, sigma_rule_data in sigma_data.get("sigma_rules", {}).items():
        try:
            sigma_rule = sigma_rule_data.get("rule", "")
            if sigma_rule:
                stix_indicator = query_generator.generate_stix_format(
                    query_content=sigma_rule,
                    query_type="sigma",
                    source_technique_id=technique_id
                )
                
                # Add metadata
                stix_indicator["query_metadata"] = sigma_rule_data.get("metadata", {})
                stix_indicator["judge_metadata"] = sigma_rule_data.get("judge_metadata", {})
                
                stix_results["stix_indicators"][f"{technique_id}_sigma"] = stix_indicator
                stix_results["generated_indicators"] += 1
        
        except Exception as e:
            error_msg = f"Failed to generate STIX for Sigma {technique_id}: {str(e)}"
            print(f"[STIX-QUERIES] {error_msg}")
            stix_results["generation_errors"].append({
                "technique_id": technique_id,
                "query_type": "sigma",
                "error": error_msg
            })
            stix_results["failed_indicators"] += 1
    
    # Save STIX results
    stix_file = os.path.join(STIX_QUERIES_DIR, "generated_stix_indicators.json")
    with open(stix_file, "w", encoding="utf-8") as f:
        json.dump(stix_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] STIX indicator generation complete:")
    print(f"  - KQL queries processed: {len(kql_data.get('kql_queries', {}))}")
    print(f"  - Sigma rules processed: {len(sigma_data.get('sigma_rules', {}))}")
    print(f"  - STIX indicators generated: {stix_results['generated_indicators']}")
    print(f"  - Failed indicators: {stix_results['failed_indicators']}")
    print(f"  - Results saved to: {stix_file}")
    
    return stix_results

def generate_final_report(**context):
    """Generate comprehensive final report of query generation pipeline"""
    print("[STIX-QUERIES] Generating final comprehensive report...")
    
    # Load all pipeline results
    try:
        files_to_load = [
            ("judge_techniques_aggregation.json", "aggregation"),
            ("mitre_enriched_techniques.json", "enrichment"),
            ("generated_kql_queries.json", "kql"),
            ("generated_sigma_rules.json", "sigma"),
            ("generated_stix_indicators.json", "stix")
        ]
        
        pipeline_results = {}
        for filename, key in files_to_load:
            filepath = os.path.join(STIX_QUERIES_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    pipeline_results[key] = json.load(f)
            else:
                pipeline_results[key] = None
                print(f"[STIX-QUERIES] Warning: {filename} not found")
    
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading pipeline results: {e}")
        return {"status": "error", "message": "Could not load pipeline results"}
    
    # Generate comprehensive summary
    final_report = {
        "report_metadata": {
            "dag_id": "stix_query_generation_dag",
            "generation_timestamp": datetime.now().isoformat(),
            "pipeline_status": "completed",
            "components_processed": [key for key, data in pipeline_results.items() if data is not None]
        },
        "pipeline_summary": {
            "input_source": "LLM-as-a-Judge unified validation results",
            "total_judge_files": pipeline_results.get("aggregation", {}).get("source_judge_files", 0),
            "total_chunks_processed": pipeline_results.get("aggregation", {}).get("total_chunks_processed", 0),
            "unique_techniques_validated": pipeline_results.get("aggregation", {}).get("unique_techniques_validated", 0),
            "mitre_enriched_techniques": pipeline_results.get("enrichment", {}).get("enriched_techniques", 0),
            "kql_queries_generated": pipeline_results.get("kql", {}).get("successful_queries", 0),
            "sigma_rules_generated": pipeline_results.get("sigma", {}).get("successful_rules", 0),
            "stix_indicators_generated": pipeline_results.get("stix", {}).get("generated_indicators", 0)
        },
        "quality_metrics": {
            "mitre_enrichment_rate": 0.0,
            "kql_generation_success_rate": 0.0,
            "sigma_generation_success_rate": 0.0,
            "stix_generation_success_rate": 0.0,
            "overall_pipeline_success_rate": 0.0
        },
        "technique_analysis": {
            "most_frequent_techniques": [],
            "highest_confidence_techniques": [],
            "coverage_by_platform": {},
            "coverage_by_kill_chain": {}
        },
        "operational_ready_outputs": {
            "kql_queries_for_sentinel": [],
            "sigma_rules_for_siem": [],
            "stix_indicators_for_sharing": [],
            "deployment_recommendations": []
        },
        "pipeline_components": pipeline_results
    }
    
    # Calculate quality metrics
    total_techniques = pipeline_results.get("aggregation", {}).get("unique_techniques_validated", 0)
    if total_techniques > 0:
        enriched = pipeline_results.get("enrichment", {}).get("enriched_techniques", 0)
        final_report["quality_metrics"]["mitre_enrichment_rate"] = enriched / total_techniques
        
        kql_success = pipeline_results.get("kql", {}).get("successful_queries", 0)
        final_report["quality_metrics"]["kql_generation_success_rate"] = kql_success / total_techniques
        
        sigma_success = pipeline_results.get("sigma", {}).get("successful_rules", 0)
        final_report["quality_metrics"]["sigma_generation_success_rate"] = sigma_success / total_techniques
        
        stix_success = pipeline_results.get("stix", {}).get("generated_indicators", 0)
        total_possible_stix = kql_success + sigma_success
        if total_possible_stix > 0:
            final_report["quality_metrics"]["stix_generation_success_rate"] = stix_success / total_possible_stix
        
        # Overall success rate
        success_components = sum([1 for rate in final_report["quality_metrics"].values() if rate > 0.7])
        final_report["quality_metrics"]["overall_pipeline_success_rate"] = success_components / 4
    
    # Analyze technique patterns
    if pipeline_results.get("aggregation"):
        aggregation_data = pipeline_results["aggregation"]
        validated_techniques = aggregation_data.get("validated_techniques", {})
        
        # Most frequent techniques
        technique_freq = [(tid, data.get("occurrence_count", 0), data.get("average_confidence", 0.0)) 
                         for tid, data in validated_techniques.items()]
        technique_freq.sort(key=lambda x: x[1], reverse=True)
        final_report["technique_analysis"]["most_frequent_techniques"] = technique_freq[:10]
        
        # Highest confidence techniques
        technique_conf = [(tid, data.get("average_confidence", 0.0), data.get("occurrence_count", 0)) 
                         for tid, data in validated_techniques.items() if data.get("average_confidence", 0.0) > 0]
        technique_conf.sort(key=lambda x: x[1], reverse=True)
        final_report["technique_analysis"]["highest_confidence_techniques"] = technique_conf[:10]
    
    # Generate operational recommendations
    recommendations = []
    
    if final_report["quality_metrics"]["kql_generation_success_rate"] > 0.7:
        recommendations.append("Deploy KQL queries to Microsoft Sentinel for immediate threat detection")
    
    if final_report["quality_metrics"]["sigma_generation_success_rate"] > 0.7:
        recommendations.append("Implement Sigma rules in SIEM platforms for cross-platform detection")
    
    if final_report["quality_metrics"]["stix_generation_success_rate"] > 0.5:
        recommendations.append("Share STIX indicators with threat intelligence platforms")
    
    if total_techniques > 10:
        recommendations.append(f"Consider prioritizing the top {min(10, total_techniques)} most frequent techniques for immediate deployment")
    
    final_report["operational_ready_outputs"]["deployment_recommendations"] = recommendations
    
    # Save final report
    report_file = os.path.join(STIX_QUERIES_DIR, "stix_query_generation_final_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] Final report generated:")
    print(f"  - Total techniques processed: {total_techniques}")
    print(f"  - KQL queries generated: {final_report['pipeline_summary']['kql_queries_generated']}")
    print(f"  - Sigma rules generated: {final_report['pipeline_summary']['sigma_rules_generated']}")
    print(f"  - STIX indicators generated: {final_report['pipeline_summary']['stix_indicators_generated']}")
    print(f"  - Overall success rate: {final_report['quality_metrics']['overall_pipeline_success_rate']:.1%}")
    print(f"  - Report saved to: {report_file}")
    
    return final_report


# ================================
# FALLBACK FUNCTIONS FOR WHEN STIX COMPONENTS ARE NOT AVAILABLE
# ================================

def _generate_basic_kql_queries():
    """Generate basic KQL queries without STIX components"""
    print("[STIX-QUERIES] Generating basic KQL queries...")
    
    # Load enriched techniques
    enrichment_file = os.path.join(STIX_QUERIES_DIR, "mitre_enriched_techniques.json")
    try:
        with open(enrichment_file, "r", encoding="utf-8") as f:
            enrichment_data = json.load(f)
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading enrichment data: {e}")
        return {"status": "error", "message": "Could not load enriched technique data"}
    
    enriched_techniques = enrichment_data.get("enriched_data", {})
    
    # Generate basic KQL templates
    basic_kql_results = {
        "generation_timestamp": datetime.now().isoformat(),
        "total_techniques": len(enriched_techniques),
        "successful_queries": 0,
        "failed_queries": 0,
        "kql_queries": {},
        "generation_mode": "basic_templates"
    }
    
    for technique_id, technique_data in enriched_techniques.items():
        try:
            technique_name = technique_data.get("mitre_name", technique_id)
            platforms = technique_data.get("platforms", [])
            data_sources = technique_data.get("data_sources", [])
            
            # Generate basic KQL template
            kql_template = f"""// KQL Query for MITRE ATT&CK Technique: {technique_id}
// Technique: {technique_name}
// Platforms: {', '.join(platforms) if platforms else 'Unknown'}
// Data Sources: {', '.join(data_sources) if data_sources else 'Unknown'}

// Basic detection query - customize based on your environment
SecurityEvent
| where TimeGenerated >= ago(24h)
| where EventID in (4688, 4624, 4625)  // Process creation, logon events
| where CommandLine has_any ("{technique_id.lower()}", "{technique_name.lower().replace(' ', '')}")
| project TimeGenerated, Computer, Account, CommandLine, EventID
| limit 100

// Additional data sources to consider:
// - Sysmon (Event ID 1 for process creation)
// - Windows Security logs
// - Application logs
// Customize filters based on technique specifics"""
            
            basic_kql_results["kql_queries"][technique_id] = {
                "query": kql_template,
                "technique_name": technique_name,
                "confidence_score": 50,  # Basic template
                "metadata": {
                    "technique_id": technique_id,
                    "platforms": platforms,
                    "data_sources": data_sources,
                    "generation_mode": "basic_template"
                },
                "judge_metadata": technique_data.get("judge_metadata", {})
            }
            
            basic_kql_results["successful_queries"] += 1
            
        except Exception as e:
            print(f"[STIX-QUERIES] Error generating basic KQL for {technique_id}: {e}")
            basic_kql_results["failed_queries"] += 1
    
    # Save results
    kql_file = os.path.join(STIX_QUERIES_DIR, "generated_kql_queries.json")
    with open(kql_file, "w", encoding="utf-8") as f:
        json.dump(basic_kql_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] Basic KQL generation complete: {basic_kql_results['successful_queries']} queries")
    return basic_kql_results

def _generate_basic_sigma_rules():
    """Generate basic Sigma rules without STIX components"""
    print("[STIX-QUERIES] Generating basic Sigma rules...")
    
    # Load enriched techniques
    enrichment_file = os.path.join(STIX_QUERIES_DIR, "mitre_enriched_techniques.json")
    try:
        with open(enrichment_file, "r", encoding="utf-8") as f:
            enrichment_data = json.load(f)
    except Exception as e:
        print(f"[STIX-QUERIES] Error loading enrichment data: {e}")
        return {"status": "error", "message": "Could not load enriched technique data"}
    
    enriched_techniques = enrichment_data.get("enriched_data", {})
    
    # Generate basic Sigma templates
    basic_sigma_results = {
        "generation_timestamp": datetime.now().isoformat(),
        "total_techniques": len(enriched_techniques),
        "successful_rules": 0,
        "failed_rules": 0,
        "sigma_rules": {},
        "generation_mode": "basic_templates"
    }
    
    for technique_id, technique_data in enriched_techniques.items():
        try:
            technique_name = technique_data.get("mitre_name", technique_id)
            description = technique_data.get("mitre_description", "")[:200] + "..." if len(technique_data.get("mitre_description", "")) > 200 else technique_data.get("mitre_description", "")
            
            # Generate basic Sigma rule template
            sigma_template = f"""title: Detection of {technique_name} ({technique_id})
id: {technique_id.lower()}-basic-detection
description: Basic detection rule for MITRE ATT&CK technique {technique_id} - {technique_name}
author: CTI Pipeline Automated Generation
date: {datetime.now().strftime('%Y/%m/%d')}
references:
    - https://attack.mitre.org/techniques/{technique_id}/
tags:
    - attack.{technique_id.lower()}
    - attack.technique
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|contains:
            - '{technique_name.lower().replace(' ', '')}'
            - '{technique_id.lower()}'
        CommandLine|contains:
            - '{technique_name.lower()}'
    condition: selection
falsepositives:
    - Legitimate administrative activities
    - Software installations
level: medium
status: experimental

# Note: This is a basic template. Customize based on:
# - Specific technique behaviors
# - Your environment
# - Available log sources
# - False positive analysis"""
            
            basic_sigma_results["sigma_rules"][technique_id] = {
                "rule": sigma_template,
                "technique_name": technique_name,
                "confidence_score": 50,  # Basic template
                "metadata": {
                    "technique_id": technique_id,
                    "rule_format": "sigma",
                    "generation_mode": "basic_template"
                },
                "judge_metadata": technique_data.get("judge_metadata", {})
            }
            
            basic_sigma_results["successful_rules"] += 1
            
        except Exception as e:
            print(f"[STIX-QUERIES] Error generating basic Sigma for {technique_id}: {e}")
            basic_sigma_results["failed_rules"] += 1
    
    # Save results
    sigma_file = os.path.join(STIX_QUERIES_DIR, "generated_sigma_rules.json")
    with open(sigma_file, "w", encoding="utf-8") as f:
        json.dump(basic_sigma_results, f, indent=2, ensure_ascii=False)
    
    print(f"[STIX-QUERIES] Basic Sigma generation complete: {basic_sigma_results['successful_rules']} rules")
    return basic_sigma_results


# ================================
# TASK DEFINITIONS
# ================================

start_task = DummyOperator(
    task_id="start_stix_query_generation",
    dag=dag,
)

fetch_judge_results_task = PythonOperator(
    task_id="fetch_judge_validation_results",
    python_callable=fetch_judge_validation_results,
    dag=dag,
)

enrich_mitre_task = PythonOperator(
    task_id="enrich_with_mitre_data",
    python_callable=enrich_with_mitre_data,
    dag=dag,
)

generate_kql_task = PythonOperator(
    task_id="generate_kql_queries",
    python_callable=generate_kql_queries,
    dag=dag,
)

generate_sigma_task = PythonOperator(
    task_id="generate_sigma_rules",
    python_callable=generate_sigma_rules,
    dag=dag,
)

generate_stix_task = PythonOperator(
    task_id="generate_stix_indicators",
    python_callable=generate_stix_indicators,
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id="generate_final_report",
    python_callable=generate_final_report,
    dag=dag,
)

completion_task = DummyOperator(
    task_id="stix_query_generation_complete",
    dag=dag,
)


# ================================
# TASK DEPENDENCIES
# ================================

# Sequential pipeline: 
# start → fetch judge results → enrich with MITRE data → (parallel: generate KQL + Sigma) → generate STIX → final report → complete
start_task >> fetch_judge_results_task >> enrich_mitre_task

# Parallel query generation
enrich_mitre_task >> [generate_kql_task, generate_sigma_task] >> generate_stix_task

# Final processing
generate_stix_task >> generate_report_task >> completion_task
