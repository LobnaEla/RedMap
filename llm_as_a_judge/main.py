"""Main script to execute LLM-as-a-Judge cross-validation - FIXED VERSION"""

import os
import sys
import json
from typing import List, Dict
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Get current directory and project root
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Load .env file
env_path = current_dir / ".env"
load_dotenv(env_path)

# Add to Python path
sys.path.insert(0, str(project_root))

try:
    from llm_as_a_judge.core.technique_validator import TechniqueValidator
    from llm_as_a_judge.utils.file_utils import (
        save_judge_results,
        save_final_techniques_only,
    )
    from llm_as_a_judge.utils.validation_utils import calculate_validation_metrics

    print("✅ Successfully imported LLM-as-a-Judge modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure the module structure is correct and __init__.py files exist")
    sys.exit(1)


def load_chunk_data(chunks_dir: str) -> List[Dict]:
    """Load CTI chunk data from directory."""
    chunks_path = Path(chunks_dir)
    if not chunks_path.exists():
        print(f"❌ Chunks directory not found: {chunks_dir}")
        return []

    chunk_files = list(chunks_path.glob("chunks_*.json"))
    chunks = []

    print(f"🔍 Found {len(chunk_files)} chunk files")

    for file_path in chunk_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)

            print(f"📄 Processing: {file_path.name}")

            # Handle different JSON structures
            if isinstance(file_data, dict) and "chunks" in file_data:
                chunks_list = file_data["chunks"]
                print(f"  Found {len(chunks_list)} chunks in 'chunks' key")
            elif isinstance(file_data, list):
                chunks_list = file_data
                print(f"  Found {len(chunks_list)} chunks in list format")
            elif isinstance(file_data, dict) and "chunk_id" in file_data:
                chunks_list = [file_data]
                print(f"  Single chunk format")
            else:
                print(f"  ⚠️ Unknown format, skipping")
                continue

            # Process chunks
            for chunk in chunks_list:
                if isinstance(chunk, dict) and "chunk_id" in chunk and "text" in chunk:
                    chunk["chunk_id"] = str(chunk["chunk_id"])
                    chunk["iocs"] = chunk.get("iocs", "")
                    chunks.append(chunk)

        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            continue

    print(f"✅ Total chunks loaded: {len(chunks)}")
    return chunks


def load_rag_results(rag_results_dir: str) -> Dict[str, List[str]]:
    """Load RAG/RAS results from directory."""
    rag_path = Path(rag_results_dir)
    if not rag_path.exists():
        print(f"❌ RAG results directory not found: {rag_results_dir}")
        return {}

    result_files = list(rag_path.glob("*.json"))
    rag_results = {}

    print(f"🔍 Found {len(result_files)} RAG result files")

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"📄 Processing RAG: {file_path.name}")

            # Handle different structures
            if isinstance(data, dict) and "rag_results" in data:
                for item in data["rag_results"]:
                    chunk_id = str(item.get("chunk_id", ""))
                    techniques = item.get("mitre_techniques", [])
                    if chunk_id:
                        rag_results[chunk_id] = techniques

            elif isinstance(data, list):
                for item in data:
                    chunk_id = str(item.get("chunk_id", ""))
                    techniques = item.get("mitre_techniques", [])
                    if chunk_id:
                        rag_results[chunk_id] = techniques

            elif isinstance(data, dict) and "chunk_id" in data:
                chunk_id = str(data.get("chunk_id", ""))
                techniques = data.get("mitre_techniques", [])
                if chunk_id:
                    rag_results[chunk_id] = techniques

        except Exception as e:
            print(f"❌ Error loading RAG file {file_path}: {e}")
            continue

    print(f"✅ RAG results loaded: {len(rag_results)} chunks")
    return rag_results


def load_llm_results(llm_results_dir: str) -> Dict[str, List[str]]:
    """Load LLM (ICL) results from directory."""
    llm_path = Path(llm_results_dir)
    if not llm_path.exists():
        print(f"❌ LLM results directory not found: {llm_results_dir}")
        return {}

    result_files = list(llm_path.glob("*.json"))
    llm_results = {}

    print(f"🔍 Found {len(result_files)} LLM result files")

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            chunk_id = str(data.get("chunk_id", ""))
            techniques = data.get("mitre_techniques", [])

            if chunk_id and techniques:
                llm_results[chunk_id] = techniques

        except Exception as e:
            print(f"❌ Error loading LLM file {file_path}: {e}")
            continue

    print(f"✅ LLM results loaded: {len(llm_results)} chunks")
    return llm_results


def analyze_input_overlap(rag_results: Dict, llm_results: Dict) -> None:
    """Analyze overlap between RAG and LLM results."""
    common_chunks = set(rag_results.keys()).intersection(set(llm_results.keys()))

    print("\n" + "=" * 50)
    print("INPUT ANALYSIS")
    print("=" * 50)
    print(f"📊 RAG results: {len(rag_results)} chunks")
    print(f"📊 LLM results: {len(llm_results)} chunks")
    print(f"📊 Common chunks: {len(common_chunks)} chunks")

    if common_chunks:
        print(f"\n🔍 Sample analysis (first 2 chunks):")
        sample_chunks = list(common_chunks)[:2]

        for chunk_id in sample_chunks:
            rag_techs = rag_results.get(chunk_id, [])
            llm_techs = llm_results.get(chunk_id, [])
            common_techs = set(rag_techs) & set(llm_techs)

            print(f"\nChunk {chunk_id}:")
            print(f"  RAG: {rag_techs}")
            print(f"  LLM: {llm_techs}")
            print(f"  Common: {list(common_techs)}")

            if rag_techs or llm_techs:
                total_unique = len(set(rag_techs) | set(llm_techs))
                overlap_rate = (
                    len(common_techs) / total_unique if total_unique > 0 else 0
                )
                print(f"  Overlap: {overlap_rate:.1%}")


def main():
    """Main function to run LLM-as-a-Judge validation."""
    print("🚀 Starting LLM-as-a-Judge Cross-Validation")
    print("=" * 60)

    # Check environment setup
    env_path = current_dir / ".env"
    if not env_path.exists():
        print(f"⚠️ .env file not found at: {env_path}")
        print("Please create .env file with: GEMINI_API_KEY=your_api_key")
        return

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Make sure .env file contains: GEMINI_API_KEY=your_actual_api_key")
        return

    print(f"✅ API key loaded (length: {len(api_key)} chars)")

    # Define data paths using os.path.join for cross-platform compatibility
    data_base = os.path.join(str(project_root), "cti_pipeline", "data")
    chunks_dir = os.path.join(data_base, "chunks")
    rag_results_dir = os.path.join(data_base, "rag_results")
    llm_results_dir = os.path.join(data_base, "llm_results")

    print(f"\n📁 Data directories:")
    print(f"  Chunks: {chunks_dir}")
    print(f"  RAG results: {rag_results_dir}")
    print(f"  LLM results: {llm_results_dir}")

    # Load all data
    print(f"\n🔄 Loading data...")
    chunks = load_chunk_data(str(chunks_dir))
    rag_results = load_rag_results(str(rag_results_dir))
    llm_results = load_llm_results(str(llm_results_dir))

    if not chunks:
        print("❌ No chunks loaded. Check chunks directory and file format.")
        return
    if not rag_results:
        print("❌ No RAG results loaded. Check RAG results directory.")
        return
    if not llm_results:
        print("❌ No LLM results loaded. Check LLM results directory.")
        return

    # Analyze input data
    analyze_input_overlap(rag_results, llm_results)

    # Prepare validation data - only chunks with both RAG and LLM results
    validation_data = []
    rag_list = []
    llm_list = []

    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id"))
        if chunk_id in rag_results and chunk_id in llm_results:
            validation_data.append(chunk)
            rag_list.append(rag_results[chunk_id])
            llm_list.append(llm_results[chunk_id])

            # LIMIT TO ONLY 2 CHUNKS FOR TESTING
            if len(validation_data) >= 2:
                break

    print(
        f"\n✅ Ready to validate {len(validation_data)} chunks with both RAG and LLM results (LIMITED TO 2 FOR TESTING)"
    )

    if not validation_data:
        print("❌ No chunks found with both RAG and LLM results")
        return

    # Initialize validator
    try:
        validator = TechniqueValidator(api_key=api_key)
        print("✅ TechniqueValidator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize validator: {e}")
        return

    # Run cross-validation
    print(f"\n⚖️ Starting LLM-as-a-Judge validation...")
    print("=" * 50)

    try:
        results = validator.batch_validate(
            chunks=validation_data,
            rag_results_list=rag_list,
            llm_results_list=llm_list,
        )
        print("✅ Batch validation completed")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return

    # Calculate detailed metrics
    try:
        validation_metrics = calculate_validation_metrics(results["validations"])
        results["detailed_metrics"] = validation_metrics
        print("✅ Detailed metrics calculated")
    except Exception as e:
        print(f"⚠️ Failed to calculate detailed metrics: {e}")

    # Save results
    try:
        full_results_file = save_judge_results(results, include_detailed=True)
        final_techniques_file = save_final_techniques_only(results)

        print(f"\n💾 Results saved:")
        print(f"  📄 Detailed: {full_results_file}")
        print(f"  📄 Summary: {final_techniques_file}")

    except Exception as e:
        print(f"❌ Failed to save results: {e}")

    # Print comprehensive summary
    print_validation_summary(results, validator)


def print_validation_summary(results: Dict, validator: TechniqueValidator):
    """Print comprehensive validation summary."""
    stats = results.get("statistics", {})

    print("\n" + "=" * 60)
    print("🎯 CROSS-VALIDATION SUMMARY")
    print("=" * 60)

    # Basic stats
    print(f"📊 Processing Statistics:")
    print(f"  Total chunks: {stats.get('total_chunks', 0)}")
    print(f"  Successful validations: {stats.get('successful_validations', 0)}")
    print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
    print(f"  Errors: {stats.get('errors', 0)}")

    # Technique stats
    print(f"\n🎯 Technique Statistics:")
    print(f"  Total analyzed: {stats.get('total_techniques_analyzed', 0)}")
    print(f"  Total validated: {stats.get('total_techniques_validated', 0)}")
    print(f"  Validation rate: {stats.get('average_validation_rate', 0):.1%}")

    # Source analysis
    print(f"\n🔍 Source Performance:")
    print(f"  Consensus accuracy: {stats.get('consensus_accuracy', 0):.1%}")
    print(f"  RAG contribution: {stats.get('rag_only_contribution', 0):.1%}")
    print(f"  LLM contribution: {stats.get('llm_only_contribution', 0):.1%}")

    # Sample final techniques
    try:
        final_techniques = validator.extract_final_techniques(results)
        print(f"\n✅ Final Validated Techniques ({len(final_techniques)} chunks):")

        sample_chunks = list(final_techniques.keys())[:3]
        for chunk_id in sample_chunks:
            techniques = final_techniques[chunk_id]
            print(f"  {chunk_id}: {techniques}")

        if len(final_techniques) > 3:
            print(f"  ... and {len(final_techniques) - 3} more chunks")

    except Exception as e:
        print(f"⚠️ Could not extract final techniques: {e}")

    # Detailed metrics if available
    detailed_metrics = results.get("detailed_metrics", {})
    if detailed_metrics and "insights" in detailed_metrics:
        insights = detailed_metrics["insights"]
        print(f"\n🔍 System Insights:")
        for key, value in insights.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")


if __name__ == "__main__":
    main()
