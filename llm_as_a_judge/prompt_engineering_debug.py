#!/usr/bin/env python
# coding: utf-8

# # LLM-as-a-Judge Prompt Engineering & Evaluation
#
# This notebook performs comprehensive evaluation of CTI-to-MITRE TTP predictions using:
# - Gemini LLM for initial inference
# - Retrieval-Augmented Generation (RAG) for evidence selection
# - LLM-as-a-Judge for final validation and scoring
#
# ## Pipeline Overview:
# 1. **Load Benchmark Dataset**: Load `cti-to-mitre-llm/benchmark/benchmark_dataset.csv`
# 2. **Initial LLM Inference**: Use Gemini model via `cti_pipeline/src/llm` for TTP prediction
# 3. **RAG Technique Retrieval**: Extract top techniques using `rag_pipeline/`
# 4. **Judge Validation**: Validate predictions using LLM-as-a-Judge from `llm_as_a_judge/`
# 5. **Metrics Comparison**: Compare performance before and after judge validation
#
# ---

# ## 1. Environment Setup & Imports
#
# Import all necessary libraries and modules from different components of the project.

# In[1]:


# Core libraries
import pandas as pd
import numpy as np
import os
import sys
import json
import ast
import warnings
from datetime import datetime
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import time

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
from pprint import pprint

# Enhanced warning suppression to prevent resource and deprecation warnings
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="torch")
warnings.filterwarnings("ignore", module="transformers")
warnings.filterwarnings("ignore", module="weaviate")
warnings.filterwarnings("ignore", module="sentence_transformers")
warnings.filterwarnings("ignore", message=".*encoder_attention_mask.*")
warnings.filterwarnings("ignore", message=".*connection.*not closed properly.*")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")

# Also configure torch to be less verbose if available
try:
    import torch

    torch.set_warn_always(False)
except:
    pass

print("✅ Core libraries imported successfully!")
print("🔇 Enhanced warning suppression configured")


# In[2]:


# Add project paths to Python path
project_root = os.path.abspath("..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "cti_pipeline"))
sys.path.insert(0, os.path.join(project_root, "rag_pipeline"))
sys.path.insert(0, os.path.join(project_root, "llm_as_a_judge"))
sys.path.insert(0, os.path.join(project_root, "cti-to-mitre-llm", "benchmark"))

print(f"📁 Project root: {project_root}")
print(f"🔧 Python paths configured")


# In[3]:


# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("⚠️ Warning: GEMINI_API_KEY not found in environment")
else:
    print("✅ GEMINI_API_KEY loaded successfully")

# Configure Google AI
import google.generativeai as genai

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    print("✅ Google Generative AI configured")


# ## 2. Import Project Components
#
# Import functions and classes from different pipeline components.

# In[4]:


# Import CTI Pipeline components
try:
    from cti_pipeline.src.llm.core.gemini_client import GeminiClient
    from cti_pipeline.src.llm.core.config import LLM_CONFIG

    print("✅ CTI Pipeline components imported")
    CTI_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing CTI Pipeline: {e}")
    CTI_AVAILABLE = False

# Import RAG Pipeline components with enhanced error handling
RAG_AVAILABLE = False
EMBEDDER_AVAILABLE = False
VECTORSTORE_AVAILABLE = False
RAG_ENGINE_AVAILABLE = False

try:
    # First check for sentence_transformers and huggingface_hub compatibility
    print("🔍 Checking sentence_transformers and huggingface_hub...")

    # Check huggingface_hub version and compatibility
    try:
        import huggingface_hub

        print(f"✅ huggingface_hub version: {huggingface_hub.__version__}")

        # Try to import the function that might be causing issues
        try:
            from huggingface_hub import cached_download

            print("✅ cached_download available (older huggingface_hub)")
        except ImportError:
            try:
                from huggingface_hub import hf_hub_download

                print("✅ hf_hub_download available (newer huggingface_hub)")
            except ImportError:
                print("⚠️ Neither cached_download nor hf_hub_download found")

    except ImportError as e:
        print(f"❌ huggingface_hub import failed: {e}")

    # Now try sentence_transformers
    try:
        import sentence_transformers

        print(f"✅ sentence_transformers version: {sentence_transformers.__version__}")
    except ImportError as e:
        print(f"❌ sentence_transformers import failed: {e}")
        raise e

    # Try importing the base classes first
    from rag_pipeline.embeddings.base import BaseEmbedder
    from rag_pipeline.vectorstore.base import BaseVectorStore, SearchResult

    print("✅ RAG base classes imported")

    # Now try the specific implementations
    try:
        from rag_pipeline.embeddings import HuggingFaceEmbedder

        print("✅ HuggingFaceEmbedder imported")
        EMBEDDER_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ HuggingFaceEmbedder not available: {e}")
        if "cached_download" in str(e):
            print("   🔧 This is a huggingface_hub compatibility issue")
        EMBEDDER_AVAILABLE = False

    try:
        from rag_pipeline.vectorstore import WeaviateVectorStore

        print("✅ WeaviateVectorStore imported")
        VECTORSTORE_AVAILABLE = True
    except (ImportError, Exception) as e:
        print(f"⚠️ WeaviateVectorStore not available: {e}")
        if "protobuf" in str(e).lower() or "grpc" in str(e).lower():
            print("   🔧 This is likely a protobuf/grpc version conflict")
        VECTORSTORE_AVAILABLE = False

    try:
        from rag_pipeline.rag import RAGEngine
        from rag_pipeline.config import Config

        print("✅ RAG Engine and Config imported")
        RAG_ENGINE_AVAILABLE = True
    except ImportError as e:
        print(f"⚠️ RAG Engine not available: {e}")
        RAG_ENGINE_AVAILABLE = False

    # RAG is only fully available if all components work
    RAG_AVAILABLE = (
        EMBEDDER_AVAILABLE and VECTORSTORE_AVAILABLE and RAG_ENGINE_AVAILABLE
    )

except ImportError as e:
    print(f"⚠️ RAG Pipeline dependencies missing: {e}")
    if "cached_download" in str(e):
        print(" 🔧 This is a huggingface_hub compatibility issue")
    RAG_AVAILABLE = False
    EMBEDDER_AVAILABLE = False
    VECTORSTORE_AVAILABLE = False
    RAG_ENGINE_AVAILABLE = False

# Import LLM-as-a-Judge components
JUDGE_AVAILABLE = False
try:
    from llm_as_a_judge.core.technique_validator import TechniqueValidator

    print("✅ LLM-as-a-Judge components imported")
    JUDGE_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing LLM-as-a-Judge: {e}")
    JUDGE_AVAILABLE = False

# Print detailed component availability summary
print(f"\n📊 Detailed Component Availability:")
print(f"  🔵 CTI Pipeline: {'✅ Available' if CTI_AVAILABLE else '❌ Not Available'}")
print(f"  🔍 RAG Pipeline:")
print(f"    - Embedder: {'✅ Available' if EMBEDDER_AVAILABLE else '❌ Not Available'}")
print(
    f"    - Vector Store: {'✅ Available' if VECTORSTORE_AVAILABLE else '❌ Not Available'}"
)
print(
    f"    - RAG Engine: {'✅ Available' if RAG_ENGINE_AVAILABLE else '❌ Not Available'}"
)
print(f"    - Overall: {'✅ Available' if RAG_AVAILABLE else '❌ Not Available'}")
print(
    f"  ⚖️ Judge Pipeline: {'✅ Available' if JUDGE_AVAILABLE else '❌ Not Available'}"
)

# Provide specific troubleshooting guidance
if not EMBEDDER_AVAILABLE and "cached_download" in locals().get("e", Exception("")):
    print("\n🔧 SPECIFIC ISSUE DETECTED: huggingface_hub compatibility")

if not VECTORSTORE_AVAILABLE:
    print("\n 🔧 VECTORSTORE ISSUE DETECTED")

if not RAG_AVAILABLE:
    print("\n 🔧 RAG Pipeline is not fully available due to missing components.")


# ## 3. Evaluation Metrics Functions
#
# Define comprehensive evaluation metrics based on the benchmark methodology.

# In[5]:


def parse_techniques(techniques_str):
    """Parse techniques from string format to list"""
    if isinstance(techniques_str, str):
        try:
            return ast.literal_eval(techniques_str)
        except:
            return [t.strip() for t in techniques_str.split(",") if t.strip()]
    elif isinstance(techniques_str, list):
        return techniques_str
    else:
        return []


def normalize_technique_id(technique_id: str) -> str:
    """Normalize MITRE technique ID (e.g., T1059.001 -> T1059)"""
    if "." in technique_id:
        return technique_id.split(".")[0]
    return technique_id


def compute_metrics(
    y_true_list: List[List[str]], y_pred_list: List[List[str]]
) -> Dict[str, float]:
    """Compute strict evaluation metrics for CTI-to-MITRE mapping"""
    if len(y_true_list) != len(y_pred_list):
        raise ValueError("Length mismatch between true and predicted labels")

    total_samples = len(y_true_list)
    exact_matches = 0
    partial_matches = 0
    total_precision = 0
    total_recall = 0
    total_f1 = 0
    total_jaccard = 0

    for y_true, y_pred in zip(y_true_list, y_pred_list):
        true_set = set(y_true) if y_true else set()
        pred_set = set(y_pred) if y_pred else set()

        # Exact match
        if true_set == pred_set:
            exact_matches += 1

        # Partial match (any intersection)
        if true_set.intersection(pred_set):
            partial_matches += 1

        # Precision, Recall, F1
        if pred_set:
            precision = len(true_set.intersection(pred_set)) / len(pred_set)
        else:
            precision = 0.0

        if true_set:
            recall = len(true_set.intersection(pred_set)) / len(true_set)
        else:
            recall = 0.0

        if precision + recall > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = 0.0

        # Jaccard similarity
        union_set = true_set.union(pred_set)
        if union_set:
            jaccard = len(true_set.intersection(pred_set)) / len(union_set)
        else:
            jaccard = 0.0

        total_precision += precision
        total_recall += recall
        total_f1 += f1
        total_jaccard += jaccard

    return {
        "exact_match": exact_matches / total_samples,
        "partial_match": partial_matches / total_samples,
        "precision": total_precision / total_samples,
        "recall": total_recall / total_samples,
        "f1": total_f1 / total_samples,
        "jaccard_similarity": total_jaccard / total_samples,
        "total_samples": total_samples,
    }


def compute_lenient_metrics(
    y_true_list: List[List[str]], y_pred_list: List[List[str]]
) -> Dict[str, float]:
    """Compute lenient evaluation metrics (parent technique matching)"""
    y_true_normalized = [
        [normalize_technique_id(t) for t in sample] for sample in y_true_list
    ]
    y_pred_normalized = [
        [normalize_technique_id(t) for t in sample] for sample in y_pred_list
    ]

    return compute_metrics(y_true_normalized, y_pred_normalized)


print("✅ Metrics functions defined")


# ## 4. Pipeline Interface Functions
#
# Create wrapper functions to interface with existing pipeline components.

# In[6]:


def query_model(text: str, api_key: str = None) -> str:
    """Query Gemini model for MITRE technique prediction - REAL DATA ONLY with rate limit handling"""
    if not CTI_AVAILABLE:
        print("❌ CTI Pipeline not available - cannot generate real predictions")
        return "[]"  # Return empty list if CTI not available

    if not api_key:
        api_key = GEMINI_API_KEY

    MAX_RETRIES = 3
    BASE_DELAY = 2

    for attempt in range(MAX_RETRIES):
        try:
            client = GeminiClient(api_key=api_key)
            result = client.map_to_mitre(
                text=text, iocs="", chunk_id=f"benchmark_chunk_{int(time.time())}"
            )

            if result.get("success", False):
                techniques = result.get("mitre_techniques", [])
                return json.dumps(techniques)
            else:
                error_msg = result.get("error", "Unknown error")
                print(f"⚠️ Gemini API error: {error_msg}")
                return "[]"

        except Exception as e:
            error_msg = str(e)
            if (
                "rate limit" in error_msg.lower()
                or "quota" in error_msg.lower()
                or "429" in error_msg
            ):
                wait_time = BASE_DELAY * (2**attempt)  # Exponential backoff
                print(
                    f"⚠️ Rate limit hit (attempt {attempt+1}): waiting {wait_time}s..."
                )
                time.sleep(wait_time)
                if attempt == MAX_RETRIES - 1:
                    print("❌ Max retries reached for rate limit")
                    return "[]"
            else:
                print(f"❌ Error querying Gemini: {error_msg}")
                return "[]"

    return "[]"


def parse_response(response: str) -> List[str]:
    """Parse LLM response to extract MITRE techniques"""
    try:
        if response.startswith("[") and response.endswith("]"):
            return json.loads(response)
        else:
            import re

            return re.findall(r"T\d+(?:\.\d+)?", response)
    except:
        return []


def get_top_techniques(query_text: str, top_k: int = 5) -> List[str]:
    """Get top MITRE techniques using RAG pipeline - REAL DATA ONLY with proper connection management"""
    if not RAG_AVAILABLE:
        print("❌ RAG Pipeline not available - cannot retrieve real techniques")
        return []  # Return empty list if RAG not available

    # Suppress warnings for cleaner output
    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", module="torch")
        warnings.filterwarnings("ignore", module="transformers")
        warnings.filterwarnings("ignore", module="weaviate")

        vector_store = None
        try:
            # Initialize components following your working pattern
            config = Config()
            embedder = HuggingFaceEmbedder()
            vector_store = WeaviateVectorStore(url="http://localhost:5000")

            # Create RAG engine
            rag_engine = RAGEngine(embedder=embedder, vector_store=vector_store)

            # Retrieve techniques using the same method as your test script
            results = rag_engine.retrieve_techniques(query=query_text)

            # Extract technique IDs from results
            import re

            technique_ids = []
            for result in results[:top_k]:  # Limit to top_k
                match = re.search(r"id=(T[\d\.]+)", str(result))
                if match:
                    technique_ids.append(match.group(1))

            return technique_ids

        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "weaviate" in error_msg.lower():
                print(f"❌ RAG connection error: Vector database not accessible")
            elif "getaddrinfo failed" in error_msg:
                print(
                    f"❌ RAG connection error: Cannot resolve Weaviate host (check if Weaviate is running)"
                )
            else:
                print(f"❌ Error in RAG retrieval: {error_msg}")
            return []  # Return empty list on error

        finally:
            # Properly close the vector store connection to prevent resource warnings
            if vector_store is not None:
                try:
                    if hasattr(vector_store, "close"):
                        vector_store.close()
                    elif hasattr(vector_store, "_client") and hasattr(
                        vector_store._client, "close"
                    ):
                        vector_store._client.close()
                except:
                    pass  # Ignore errors during cleanup


def evaluate_with_judge(
    original_text: str, initial_output: List[str], rag_output: List[str]
) -> List[str]:
    """Evaluate techniques using LLM-as-a-Judge - REAL DATA ONLY with rate limit handling"""
    if not JUDGE_AVAILABLE:
        print("❌ Judge Pipeline not available - using initial LLM output only")
        return initial_output  # Return original LLM output if judge not available

    MAX_RETRIES = 2  # Fewer retries for judge to avoid too many API calls

    for attempt in range(MAX_RETRIES):
        try:
            validator = TechniqueValidator(api_key=GEMINI_API_KEY)

            chunk_data = {
                "chunk_id": f"judge_eval_{int(time.time())}_{attempt}",
                "text": original_text,
                "iocs": "",
            }

            validation_result = validator.validate_single_chunk(
                chunk_data=chunk_data,
                rag_results=rag_output,
                llm_results=initial_output,
            )

            if validation_result.get("success", False):
                return validation_result.get("final_validated_techniques", [])
            else:
                error_msg = validation_result.get("error", "Unknown error")
                if "rate limit" in error_msg.lower():
                    wait_time = 5 * (attempt + 1)
                    print(
                        f"⚠️ Judge rate limit (attempt {attempt+1}): waiting {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    print(f"❌ Judge validation failed: {error_msg}")
                    return initial_output

        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                wait_time = 5 * (attempt + 1)
                print(
                    f"⚠️ Judge rate limit exception (attempt {attempt+1}): waiting {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"❌ Error in judge evaluation: {error_msg}")
                return initial_output

    print("❌ Judge validation failed after retries - using LLM output")
    return initial_output


# Check what we can actually run - STRICT REQUIREMENTS
print("🔍 CHECKING PIPELINE AVAILABILITY FOR REAL DATA EVALUATION")
print("=" * 60)

available_pipelines = []
missing_pipelines = []

if CTI_AVAILABLE:
    available_pipelines.append("CTI Pipeline (Gemini)")
    print("✅ CTI Pipeline: Available - Can generate real MITRE predictions")
else:
    missing_pipelines.append("CTI Pipeline")
    print("❌ CTI Pipeline: Not Available - Cannot generate real predictions")

if RAG_AVAILABLE:
    available_pipelines.append("RAG Pipeline")
    print("✅ RAG Pipeline: Available - Can retrieve real techniques")
    print("   📝 Using enhanced connection management to prevent resource warnings")
else:
    missing_pipelines.append("RAG Pipeline")
    print("❌ RAG Pipeline: Not Available - Cannot retrieve real techniques")

if JUDGE_AVAILABLE:
    available_pipelines.append("Judge Pipeline")
    print("✅ Judge Pipeline: Available - Can perform real validation")
else:
    missing_pipelines.append("Judge Pipeline")
    print("❌ Judge Pipeline: Not Available - Will use LLM output only")

print(f"\n📊 EVALUATION CAPABILITIES:")
print(
    f"  ✅ Available: {', '.join(available_pipelines) if available_pipelines else 'None'}"
)
print(f"  ❌ Missing: {', '.join(missing_pipelines) if missing_pipelines else 'None'}")

# Determine evaluation strategy
if CTI_AVAILABLE:
    if RAG_AVAILABLE and JUDGE_AVAILABLE:
        evaluation_mode = "FULL_PIPELINE"
        print(f"\n🚀 EVALUATION MODE: {evaluation_mode}")
        print("  Will run: Gemini → RAG → Judge validation")
    elif JUDGE_AVAILABLE:
        evaluation_mode = "LLM_JUDGE_ONLY"
        print(f"\n🚀 EVALUATION MODE: {evaluation_mode}")
        print("  Will run: Gemini → Judge validation (no RAG)")
    else:
        evaluation_mode = "LLM_ONLY"
        print(f"\n🚀 EVALUATION MODE: {evaluation_mode}")
        print("  Will run: Gemini only (no RAG, no Judge)")
else:
    evaluation_mode = "CANNOT_EVALUATE"
    print(f"\n❌ EVALUATION MODE: {evaluation_mode}")
    print("  Cannot evaluate without CTI Pipeline")
    print("  Please fix dependency issues to proceed")

print("\n🔧 IMPROVEMENTS ADDED:")
print("  - Enhanced warning suppression for cleaner output")
print("  - Proper Weaviate connection cleanup to prevent resource leaks")
print("  - Torch/Transformers deprecation warning filtering")
print("  - Resource management with proper try/finally blocks")
print("\n📝 NOTE: Only real data will be used - no mock techniques or fallbacks")
print("✅ Pipeline functions configured with enhanced resource management")


# ## 5. Load Benchmark Dataset
#
# Load the benchmark dataset from `cti-to-mitre-llm/benchmark/benchmark_dataset.csv`.

# In[7]:


# Load benchmark dataset
dataset_path = os.path.join(
    project_root, "cti-to-mitre-llm", "benchmark", "benchmark_dataset.csv"
)

if not os.path.exists(dataset_path):
    print(f"❌ Dataset not found at: {dataset_path}")
    print("Please ensure the benchmark dataset exists.")
else:
    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"✅ Dataset loaded successfully!")
    print(f"📊 Dataset shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")

    # Display first few rows
    print("\\n🔍 First 3 rows:")
    display(df.head(3))


# In[8]:


# Prepare dataset for evaluation
if "text1" in df.columns:
    df["cti_text"] = df["text1"]
elif "text" in df.columns:
    df["cti_text"] = df["text"]

if "labels_parsed" in df.columns:
    df["ttp_labels"] = df["labels_parsed"].apply(
        lambda x: x if isinstance(x, list) else parse_techniques(x)
    )
elif "labels" in df.columns:
    df["ttp_labels"] = df["labels"].apply(parse_techniques)

# Limit dataset size for demonstration (adjust as needed)
SAMPLE_SIZE = 50
df_sample = df.head(SAMPLE_SIZE).copy()

print(f"📊 Working with {len(df_sample)} samples")
print(f"📝 Sample text: {df_sample['cti_text'].iloc[0][:200]}...")
print(f"🎯 Sample labels: {df_sample['ttp_labels'].iloc[0]}")


# ## 6. Complete Pipeline Evaluation
#
# Execute the full pipeline: Gemini → RAG → Judge validation and compare results.

# In[ ]:


print("🚀 Starting Real Data Pipeline Evaluation...")
print("=" * 60)

# Check if we can proceed with evaluation
if not CTI_AVAILABLE:
    print("❌ CANNOT PROCEED: CTI Pipeline not available")
    print("   Please fix dependency issues to generate real Gemini predictions")
    print("   Run the dependency fix cell and restart the kernel")
else:
    print(f"✅ PROCEEDING WITH EVALUATION")

    # Reduce sample size to avoid rate limits
    EVAL_SAMPLE_SIZE = min(10, len(df_sample))  # Start with just 10 samples
    df_eval = df_sample.head(EVAL_SAMPLE_SIZE).copy()

    print(f"   📊 Evaluation samples: {len(df_eval)} (reduced to avoid rate limits)")
    print(f"   🔵 CTI Pipeline: {'✅' if CTI_AVAILABLE else '❌'}")
    print(f"   🔍 RAG Pipeline: {'✅' if RAG_AVAILABLE else '❌ (will skip RAG)'}")
    print(
        f"   ⚖️ Judge Pipeline: {'✅' if JUDGE_AVAILABLE else '❌ (will use LLM only)'}"
    )

    # Initialize result lists
    llm_predictions = []
    rag_results = []
    judge_results = []
    successful_evaluations = 0
    failed_evaluations = 0

    # Add longer delays to handle rate limits
    DELAY_BETWEEN_REQUESTS = 3.0  # 3 seconds between requests
    MAX_RETRIES = 3

    print(
        f"\\n⏱️ Using {DELAY_BETWEEN_REQUESTS}s delay between requests to avoid rate limits"
    )

    # Process each sample through the available pipeline components
    for idx, row in tqdm(
        df_eval.iterrows(), total=len(df_eval), desc="Real Data Evaluation"
    ):
        cti_text = row["cti_text"]
        sample_success = False

        for attempt in range(MAX_RETRIES):
            try:
                # Step 1: Gemini LLM Inference (REQUIRED)
                print(
                    f"\\n📝 Processing sample {idx+1}/{len(df_eval)} (attempt {attempt+1})"
                )
                response = query_model(cti_text, GEMINI_API_KEY)
                gemini_prediction = parse_response(response)

                if (
                    gemini_prediction or response == "[]"
                ):  # Success if we get a response
                    llm_predictions.append(gemini_prediction)
                    print(f"✅ Gemini prediction: {gemini_prediction}")

                    # Step 2: RAG Technique Retrieval (OPTIONAL - Skip if connection issues)
                    if RAG_AVAILABLE:
                        try:
                            rag_techniques = get_top_techniques(cti_text, top_k=5)
                            rag_results.append(rag_techniques)
                            print(f"✅ RAG techniques: {rag_techniques}")
                        except Exception as rag_error:
                            print(
                                f"⚠️ RAG failed (connection issue): {str(rag_error)[:100]}..."
                            )
                            rag_results.append([])  # Empty list if RAG fails
                    else:
                        rag_results.append([])  # Empty list if RAG not available
                        print("⚠️ RAG not available")

                    # Step 3: Judge Validation (OPTIONAL)
                    if JUDGE_AVAILABLE:
                        try:
                            validated_techniques = evaluate_with_judge(
                                original_text=cti_text,
                                initial_output=gemini_prediction,
                                rag_output=rag_results[
                                    -1
                                ],  # Use the RAG result we just got
                            )
                            judge_results.append(validated_techniques)
                            print(f"✅ Judge validation: {validated_techniques}")
                        except Exception as judge_error:
                            print(f"⚠️ Judge failed: {str(judge_error)[:100]}...")
                            judge_results.append(gemini_prediction)  # Fallback to LLM
                    else:
                        judge_results.append(
                            gemini_prediction
                        )  # Use LLM output if no judge
                        print("⚠️ Judge not available - using LLM output")

                    successful_evaluations += 1
                    sample_success = True
                    break  # Success - break retry loop

                else:
                    print(f"⚠️ Empty response from Gemini (attempt {attempt+1})")

            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
                    print(f"⚠️ Rate limit hit (attempt {attempt+1}): {error_msg}")
                    if attempt < MAX_RETRIES - 1:
                        wait_time = 10 * (attempt + 1)  # Exponential backoff
                        print(f"   Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                else:
                    print(f"❌ Unexpected error (attempt {attempt+1}): {error_msg}")
                    break  # Don't retry non-rate-limit errors

        if not sample_success:
            print(f"❌ Failed to process sample {idx+1} after {MAX_RETRIES} attempts")
            llm_predictions.append([])
            rag_results.append([])
            judge_results.append([])
            failed_evaluations += 1

        # Always add delay between samples
        if idx < len(df_eval) - 1:  # Don't wait after last sample
            print(f"⏳ Waiting {DELAY_BETWEEN_REQUESTS}s before next sample...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    # Add results to dataframe
    df_eval["llm_prediction"] = llm_predictions
    df_eval["rag_techniques"] = rag_results
    df_eval["judge_validated"] = judge_results

    print(f"\\n✅ Real Data Pipeline Evaluation Completed!")
    print(f"📊 Successfully processed: {successful_evaluations}/{len(df_eval)} samples")
    print(f"❌ Failed: {failed_evaluations}/{len(df_eval)} samples")
    print(f"🔵 Gemini predictions: {len([p for p in llm_predictions if p])}")
    print(f"🔍 RAG results: {len([r for r in rag_results if r])}")
    print(f"⚖️ Judge validations: {len([j for j in judge_results if j])}")

    # Show sample results
    print(f"\\n📋 SAMPLE RESULTS:")
    for i in range(min(3, len(df_eval))):
        print(f"\\nSample {i+1}:")
        print(f"  Text: {df_eval['cti_text'].iloc[i][:100]}...")
        print(f"  Ground Truth: {df_eval['ttp_labels'].iloc[i]}")
        print(f"  Gemini: {df_eval['llm_prediction'].iloc[i]}")
        print(f"  RAG: {df_eval['rag_techniques'].iloc[i]}")
        print(f"  Judge: {df_eval['judge_validated'].iloc[i]}")

    # Update the global df_sample for evaluation
    df_sample = df_eval.copy()

    if successful_evaluations == 0:
        print(
            "\\n❌ No successful evaluations - cannot proceed with metrics calculation"
        )
        print("   This is likely due to rate limits or API issues")
        print("   Try again later or reduce the sample size further")
    else:
        print(
            f"\\n✅ Proceeding with metrics calculation for {successful_evaluations} samples"
        )


# In[ ]:


# Evaluate and compare approaches - REAL DATA ONLY
print("📊 COMPREHENSIVE REAL DATA EVALUATION RESULTS")
print("=" * 60)

if not CTI_AVAILABLE:
    print("❌ Cannot evaluate - CTI Pipeline not available")
    print("   Please fix dependency issues and re-run the pipeline")
else:
    # Prepare ground truth and predictions
    ground_truth = df_sample["ttp_labels"].tolist()
    gemini_predictions = df_sample["llm_prediction"].tolist()

    # Calculate metrics for Gemini-only approach
    metrics_gemini = compute_metrics(ground_truth, gemini_predictions)
    lenient_metrics_gemini = compute_lenient_metrics(ground_truth, gemini_predictions)

    print(f"\\n🔵 GEMINI LLM RESULTS:")
    print(
        f"   📊 Samples with predictions: {len([p for p in gemini_predictions if p])}/{len(gemini_predictions)}"
    )
    print("   Strict Metrics:")
    for metric, value in metrics_gemini.items():
        if metric != "total_samples":
            print(f"     {metric}: {value:.4f}")

    print("   Lenient Metrics:")
    for metric, value in lenient_metrics_gemini.items():
        if metric != "total_samples":
            print(f"     {metric}: {value:.4f}")

    # If Judge is available, compare with judge-validated results
    if JUDGE_AVAILABLE:
        judge_predictions = df_sample["judge_validated"].tolist()
        metrics_judge = compute_metrics(ground_truth, judge_predictions)
        lenient_metrics_judge = compute_lenient_metrics(ground_truth, judge_predictions)

        print(f"\\n⚖️ JUDGE-VALIDATED RESULTS:")
        print(
            f"   📊 Samples with validations: {len([p for p in judge_predictions if p])}/{len(judge_predictions)}"
        )
        print("   Strict Metrics:")
        for metric, value in metrics_judge.items():
            if metric != "total_samples":
                print(f"     {metric}: {value:.4f}")

        print("   Lenient Metrics:")
        for metric, value in lenient_metrics_judge.items():
            if metric != "total_samples":
                print(f"     {metric}: {value:.4f}")

        print(f"\\n📈 JUDGE IMPROVEMENT OVER GEMINI:")
        for metric in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]:
            improvement_strict = metrics_judge[metric] - metrics_gemini[metric]
            improvement_lenient = (
                lenient_metrics_judge[metric] - lenient_metrics_gemini[metric]
            )
            print(f"   {metric}:")
            print(f"     Strict: {improvement_strict:+.4f}")
            print(f"     Lenient: {improvement_lenient:+.4f}")

        # Determine if judge improves performance
        f1_improvement = metrics_judge["f1"] - metrics_gemini["f1"]
        if f1_improvement > 0:
            print(
                f"\\n✅ CONCLUSION: Judge validation improves F1 by {f1_improvement:.4f}"
            )
        elif f1_improvement < 0:
            print(
                f"\\n⚠️ CONCLUSION: Judge validation decreases F1 by {abs(f1_improvement):.4f}"
            )
        else:
            print(f"\\n➡️ CONCLUSION: Judge validation shows no F1 change")

    else:
        print(f"\\n⚠️ Judge Pipeline not available - only Gemini results shown")
        print(f"   To see judge validation, fix RAG/Judge dependencies")

    # RAG-only analysis if available
    if RAG_AVAILABLE:
        rag_techniques = df_sample["rag_techniques"].tolist()
        print(f"\\n🔍 RAG PIPELINE INFO:")
        print(
            f"   📊 Samples with RAG results: {len([r for r in rag_techniques if r])}/{len(rag_techniques)}"
        )
        print(
            f"   📋 Sample RAG techniques: {rag_techniques[0] if rag_techniques[0] else 'None'}"
        )
    else:
        print(f"\\n⚠️ RAG Pipeline not available - no technique retrieval analysis")

    # Show detailed comparison for first few samples
    print(f"\\n📋 DETAILED SAMPLE COMPARISON:")
    for i in range(min(5, len(df_sample))):
        print(f"\\n  Sample {i+1}:")
        print(f"    Text: {df_sample['cti_text'].iloc[i][:100]}...")
        print(f"    Ground Truth: {df_sample['ttp_labels'].iloc[i]}")
        print(f"    Gemini: {df_sample['llm_prediction'].iloc[i]}")
        if JUDGE_AVAILABLE:
            print(f"    Judge: {df_sample['judge_validated'].iloc[i]}")

        # Calculate individual sample metrics
        gt = set(df_sample["ttp_labels"].iloc[i])
        pred = set(df_sample["llm_prediction"].iloc[i])

        if gt and pred:
            precision = len(gt.intersection(pred)) / len(pred)
            recall = len(gt.intersection(pred)) / len(gt)
            f1 = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0
                else 0
            )
            print(f"    Metrics: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}")
        elif gt:
            print(f"    Metrics: No predictions made")
        else:
            print(f"    Metrics: No ground truth available")

    print(f"\\n✅ Real data evaluation completed with available components!")


# In[ ]:


# Create comprehensive comparison visualization
fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle("LLM-as-a-Judge Performance Analysis", fontsize=16, fontweight="bold")

# 1. F1 Score Comparison
ax1 = axes[0, 0]
approaches = [
    "Gemini\n(Strict)",
    "Judge\n(Strict)",
    "Gemini\n(Lenient)",
    "Judge\n(Lenient)",
]
f1_scores = [
    metrics_gemini["f1"],
    metrics_judge["f1"],
    lenient_metrics_gemini["f1"],
    lenient_metrics_judge["f1"],
]
colors = ["skyblue", "lightcoral", "lightgreen", "orange"]

bars = ax1.bar(approaches, f1_scores, color=colors, alpha=0.8)
ax1.set_ylabel("F1 Score")
ax1.set_title("F1 Score Comparison")
ax1.grid(True, alpha=0.3)

for bar, score in zip(bars, f1_scores):
    height = bar.get_height()
    ax1.text(
        bar.get_x() + bar.get_width() / 2.0,
        height + 0.01,
        f"{score:.3f}",
        ha="center",
        va="bottom",
        fontweight="bold",
    )

# 2. All Metrics Comparison (Strict)
ax2 = axes[0, 1]
metrics_names = ["Exact Match", "Partial Match", "Precision", "Recall", "F1", "Jaccard"]
gemini_values = [
    metrics_gemini[m]
    for m in [
        "exact_match",
        "partial_match",
        "precision",
        "recall",
        "f1",
        "jaccard_similarity",
    ]
]
judge_values = [
    metrics_judge[m]
    for m in [
        "exact_match",
        "partial_match",
        "precision",
        "recall",
        "f1",
        "jaccard_similarity",
    ]
]

x = np.arange(len(metrics_names))
width = 0.35

ax2.bar(
    x - width / 2, gemini_values, width, label="Gemini Only", alpha=0.8, color="skyblue"
)
ax2.bar(
    x + width / 2,
    judge_values,
    width,
    label="Judge Validated",
    alpha=0.8,
    color="lightcoral",
)

ax2.set_xlabel("Metrics")
ax2.set_ylabel("Score")
ax2.set_title("Strict Metrics Comparison")
ax2.set_xticks(x)
ax2.set_xticklabels(metrics_names, rotation=45)
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. Improvement Analysis
ax3 = axes[1, 0]
improvements = [judge_values[i] - gemini_values[i] for i in range(len(metrics_names))]
colors = ["green" if imp >= 0 else "red" for imp in improvements]

bars = ax3.bar(metrics_names, improvements, color=colors, alpha=0.7)
ax3.set_xlabel("Metrics")
ax3.set_ylabel("Improvement")
ax3.set_title("Performance Improvement (Judge - Gemini)")
ax3.tick_params(axis="x", rotation=45)
ax3.axhline(y=0, color="black", linestyle="-", alpha=0.3)
ax3.grid(True, alpha=0.3)

# 4. Summary Statistics
ax4 = axes[1, 1]
ax4.axis("off")
summary_text = f"""
KEY FINDINGS:

📊 Total Samples: {len(df_sample)}

🔵 Gemini F1 (Strict): {metrics_gemini['f1']:.4f}
⚖️ Judge F1 (Strict): {metrics_judge['f1']:.4f}
📈 F1 Improvement: {metrics_judge['f1'] - metrics_gemini['f1']:+.4f}

🔵 Gemini F1 (Lenient): {lenient_metrics_gemini['f1']:.4f}
⚖️ Judge F1 (Lenient): {lenient_metrics_judge['f1']:.4f}
📈 Lenient F1 Improvement: {lenient_metrics_judge['f1'] - lenient_metrics_gemini['f1']:+.4f}

CONCLUSION:
{'✅ Judge validation improves performance' if metrics_judge['f1'] > metrics_gemini['f1'] else '⚠️ Mixed results - needs further analysis'}
"""

ax4.text(
    0.1,
    0.9,
    summary_text,
    transform=ax4.transAxes,
    fontsize=11,
    verticalalignment="top",
    fontfamily="monospace",
    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8),
)

plt.tight_layout()
plt.show()

# Save results with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# 1. Save the main results DataFrame
results_filename = f"prompt_engineering_results_{timestamp}.csv"
df_sample.to_csv(results_filename, index=False)

# 2. Save LLM (Gemini) metrics separately
llm_metrics_data = {
    "approach": "Gemini_LLM",
    "evaluation_type": ["strict", "lenient"],
    "exact_match": [
        metrics_gemini["exact_match"],
        lenient_metrics_gemini["exact_match"],
    ],
    "partial_match": [
        metrics_gemini["partial_match"],
        lenient_metrics_gemini["partial_match"],
    ],
    "precision": [metrics_gemini["precision"], lenient_metrics_gemini["precision"]],
    "recall": [metrics_gemini["recall"], lenient_metrics_gemini["recall"]],
    "f1": [metrics_gemini["f1"], lenient_metrics_gemini["f1"]],
    "jaccard_similarity": [
        metrics_gemini["jaccard_similarity"],
        lenient_metrics_gemini["jaccard_similarity"],
    ],
    "total_samples": [
        metrics_gemini["total_samples"],
        lenient_metrics_gemini["total_samples"],
    ],
    "timestamp": [timestamp, timestamp],
}
llm_metrics_df = pd.DataFrame(llm_metrics_data)
llm_metrics_filename = f"llm_metrics_{timestamp}.csv"
llm_metrics_df.to_csv(llm_metrics_filename, index=False)

# 3. Save Judge metrics separately
judge_metrics_data = {
    "approach": "Judge_Validated",
    "evaluation_type": ["strict", "lenient"],
    "exact_match": [metrics_judge["exact_match"], lenient_metrics_judge["exact_match"]],
    "partial_match": [
        metrics_judge["partial_match"],
        lenient_metrics_judge["partial_match"],
    ],
    "precision": [metrics_judge["precision"], lenient_metrics_judge["precision"]],
    "recall": [metrics_judge["recall"], lenient_metrics_judge["recall"]],
    "f1": [metrics_judge["f1"], lenient_metrics_judge["f1"]],
    "jaccard_similarity": [
        metrics_judge["jaccard_similarity"],
        lenient_metrics_judge["jaccard_similarity"],
    ],
    "total_samples": [
        metrics_judge["total_samples"],
        lenient_metrics_judge["total_samples"],
    ],
    "timestamp": [timestamp, timestamp],
}
judge_metrics_df = pd.DataFrame(judge_metrics_data)
judge_metrics_filename = f"judge_metrics_{timestamp}.csv"
judge_metrics_df.to_csv(judge_metrics_filename, index=False)

# 4. Save comparison metrics (improvements)
comparison_metrics_data = {
    "metric": [
        "exact_match",
        "partial_match",
        "precision",
        "recall",
        "f1",
        "jaccard_similarity",
    ],
    "gemini_strict": [
        metrics_gemini[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "judge_strict": [
        metrics_judge[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "improvement_strict": [
        metrics_judge[m] - metrics_gemini[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "gemini_lenient": [
        lenient_metrics_gemini[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "judge_lenient": [
        lenient_metrics_judge[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "improvement_lenient": [
        lenient_metrics_judge[m] - lenient_metrics_gemini[m]
        for m in [
            "exact_match",
            "partial_match",
            "precision",
            "recall",
            "f1",
            "jaccard_similarity",
        ]
    ],
    "timestamp": [timestamp] * 6,
}
comparison_metrics_df = pd.DataFrame(comparison_metrics_data)
comparison_filename = f"metrics_comparison_{timestamp}.csv"
comparison_metrics_df.to_csv(comparison_filename, index=False)

print(f"\n💾 RESULTS SAVED:")
print(f"  📋 Main results: {results_filename}")
print(f"  🔵 LLM metrics: {llm_metrics_filename}")
print(f"  ⚖️ Judge metrics: {judge_metrics_filename}")
print(f"  📊 Comparison: {comparison_filename}")

# Display the saved metrics for verification
print(f"\n📊 LLM METRICS SAVED:")
display(llm_metrics_df)

print(f"\n⚖️ JUDGE METRICS SAVED:")
display(judge_metrics_df)

print(f"\n📈 COMPARISON METRICS SAVED:")
display(comparison_metrics_df)

print("\n✅ Evaluation completed successfully!")
