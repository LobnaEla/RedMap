"""
Main script to execute LLM-as-a-Judge cross-validation
"""

import os
import sys
import json
from typing import List, Dict

# Add path for imports
sys.path.append("/opt/project/cti_pipeline")

from llm_as_a_judge import (
    TechniqueValidator,
    TechniqueAnalysis,
    save_judge_results,
    PATH_CONFIG,
    calculate_validation_metrics,
    save_final_techniques_only,
)


def load_chunk_data(chunks_dir: str) -> List[Dict]:
    """Load chunk data"""
    import glob

    chunk_files = glob.glob(os.path.join(chunks_dir, "chunks_*.json"))
    chunks = []
    print(f"Found {len(chunk_files)} chunk files")

    for file_path in chunk_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                print(f"Processing chunk file: {os.path.basename(file_path)}")

                if isinstance(file_data, dict) and "chunks" in file_data:
                    chunks_list = file_data["chunks"]
                    print(f"  Found {len(chunks_list)} chunks in 'chunks' key")

                    for chunk in chunks_list:
                        # Check that each chunk has required fields
                        if "chunk_id" in chunk and "text" in chunk:
                            if "iocs" not in chunk:
                                chunk["iocs"] = chunk.get("iocs", "")
                            chunks.append(chunk)

                    print(f"  Loaded {len(chunks_list)} chunks from file")

                elif isinstance(file_data, list):
                    # Direct list format
                    for chunk in file_data:
                        if "chunk_id" in chunk:
                            chunks.append(chunk)
                    print(f"  Loaded {len(file_data)} chunks from list")

                elif isinstance(file_data, dict) and "chunk_id" in file_data:
                    # Direct chunk
                    chunks.append(file_data)
                    print(f"  Loaded 1 chunk directly")

                else:
                    print(f"  Unknown format in file {file_path}")

        except Exception as e:
            print(f"Error loading chunk file {file_path}: {e}")
            continue

    # Ensure all chunks have chunk_id as string
    for chunk in chunks:
        if "chunk_id" in chunk:
            chunk["chunk_id"] = str(chunk["chunk_id"])

    print(f"Total chunks loaded: {len(chunks)}")
    return chunks


def load_rag_results(rag_results_dir: str) -> Dict[str, List[str]]:
    """Load RAG/RAS results"""
    import glob

    rag_results = {}

    # Search for RAG result files
    result_files = glob.glob(os.path.join(rag_results_dir, "*.json"))
    print(f"Found {len(result_files)} RAG result files")

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"Processing RAG file: {os.path.basename(file_path)}")

                if isinstance(data, dict) and "rag_results" in data:
                    rag_results_list = data["rag_results"]
                    processed_count = 0

                    for item in rag_results_list:
                        chunk_id = str(
                            item.get("chunk_id")
                        )  # Convert to string for consistency
                        techniques = item.get("mitre_techniques", [])
                        status = item.get("status", "unknown")

                        # Only process chunks with success and valid techniques
                        if status != "network_error" and techniques:
                            rag_results[chunk_id] = techniques
                            processed_count += 1
                        elif status == "network_error":
                            print(f"  Chunk {chunk_id}: Network error - skipping")
                        else:
                            # Even for chunks without techniques, keep them with empty list
                            rag_results[chunk_id] = []

                    print(
                        f"  Processed {processed_count} chunks with techniques from {len(rag_results_list)} total chunks"
                    )

                elif isinstance(data, dict):
                    # Direct chunk_id
                    chunk_id = data.get("chunk_id")
                    techniques = data.get("mitre_techniques", [])
                    if chunk_id:
                        rag_results[str(chunk_id)] = techniques

                elif isinstance(data, list):
                    # Direct list format
                    for item in data:
                        chunk_id = item.get("chunk_id")
                        techniques = item.get("mitre_techniques", [])
                        if chunk_id:
                            rag_results[str(chunk_id)] = techniques

        except Exception as e:
            print(f"Error loading RAG result file {file_path}: {e}")
            continue

    print(f"Total RAG results loaded: {len(rag_results)} chunks")
    return rag_results


def load_llm_results(llm_results_dir: str) -> Dict[str, List[str]]:
    """Load first LLM (ICL) results"""
    import glob

    llm_results = {}
    result_files = glob.glob(os.path.join(llm_results_dir, "*.json"))

    for file_path in result_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                chunk_id = data.get("chunk_id")
                techniques = data.get("mitre_techniques", [])
                if chunk_id and techniques:
                    llm_results[chunk_id] = techniques
        except Exception as e:
            print(f"Error loading LLM result file {file_path}: {e}")
            continue

    return llm_results


def analyze_input_overlap(rag_results: Dict, llm_results: Dict) -> None:
    """Analyze overlap between RAG and LLM results"""

    common_chunks = set(rag_results.keys()).intersection(set(llm_results.keys()))
    print(f"\n=== INPUT ANALYSIS ===")
    print(f"RAG results: {len(rag_results)} chunks")
    print(f"LLM results: {len(llm_results)} chunks")
    print(f"Common chunks: {len(common_chunks)} chunks")

    if common_chunks:
        # Analysis of a few examples
        sample_chunks = list(common_chunks)[:3]

        for chunk_id in sample_chunks:
            rag_techs = rag_results[chunk_id]
            llm_techs = llm_results[chunk_id]

            analysis = TechniqueAnalysis(rag_techs, llm_techs)
            stats = analysis.get_overlap_stats()

            print(f"\nChunk {chunk_id}:")
            print(f"  RAG: {rag_techs}")
            print(f"  LLM: {llm_techs}")
            print(f"  Common: {analysis.common}")
            print(f"  Overlap: {stats['overlap_percentage']:.1f}%")


def main():
    """Main function"""
    # Configuration
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    # Data paths
    chunks_dir = "cti_pipeline/data/chunks"
    rag_results_dir = "cti_pipeline/data/rag_results"
    llm_results_dir = "cti_pipeline/data/llm_results"

    print("Loading data...")

    # Data loading
    chunks = load_chunk_data(chunks_dir)
    rag_results = load_rag_results(rag_results_dir)
    llm_results = load_llm_results(llm_results_dir)

    print(f"Loaded {len(chunks)} chunks")
    print(f"RAG results for {len(rag_results)} chunks")
    print(f"LLM results for {len(llm_results)} chunks")

    # Overlap analysis
    analyze_input_overlap(rag_results, llm_results)

    # Data preparation for validation
    validation_data = []
    rag_results_list = []
    llm_results_list = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in rag_results and chunk_id in llm_results:
            validation_data.append(chunk)
            rag_results_list.append(rag_results[chunk_id])
            llm_results_list.append(llm_results[chunk_id])

    print(
        f"\nWill validate {len(validation_data)} chunks with both RAG and LLM results"
    )

    if not validation_data:
        print("No chunks with both RAG and LLM results found")
        sys.exit(1)

    # Validator initialization
    validator = TechniqueValidator(api_key=api_key)

    print("Starting cross-validation...")

    # Cross-validation
    results = validator.batch_validate(
        chunks=validation_data,
        rag_results_list=rag_results_list,
        llm_results_list=llm_results_list,
    )

    # Validation metrics calculation
    validation_metrics = calculate_validation_metrics(results["validations"])
    results["validation_metrics"] = validation_metrics

    # Save complete results
    full_results_file = save_judge_results(results, include_detailed=True)
    print(f"Detailed results saved to: {full_results_file}")

    # Save final techniques only
    final_techniques_file = save_final_techniques_only(results)
    print(f"Final validated techniques saved to: {final_techniques_file}")

    # Display main results
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION SUMMARY")
    print("=" * 60)

    stats = results["statistics"]
    print(f"Total chunks processed: {stats['total_chunks']}")
    print(f"Successful validations: {stats['successful_validations']}")
    print(f"Success rate: {stats['success_rate']:.2%}")
    print(f"Total techniques analyzed: {stats['total_techniques_analyzed']}")
    print(f"Total techniques validated: {stats['total_techniques_validated']}")
    print(f"Overall validation rate: {stats['average_validation_rate']:.2%}")
    print(f"Consensus accuracy: {stats['consensus_accuracy']:.2%}")

    if "validation_metrics" in results:
        metrics = results["validation_metrics"]
        if "error" not in metrics:
            overall = metrics["overall_metrics"]
            source_analysis = metrics["source_analysis"]

            print(f"\n--- TECHNIQUE SOURCE ANALYSIS ---")
            print(f"Common techniques (both approaches):")
            print(f"  Total: {source_analysis['common_techniques']['total']}")
            print(f"  Validated: {source_analysis['common_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['common_techniques']['validation_rate']:.2%}"
            )

            print(f"\nRAG-only techniques:")
            print(f"  Total: {source_analysis['rag_only_techniques']['total']}")
            print(f"  Validated: {source_analysis['rag_only_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['rag_only_techniques']['validation_rate']:.2%}"
            )

            print(f"\nLLM-only techniques:")
            print(f"  Total: {source_analysis['llm_only_techniques']['total']}")
            print(f"  Validated: {source_analysis['llm_only_techniques']['validated']}")
            print(
                f"  Validation rate: {source_analysis['llm_only_techniques']['validation_rate']:.2%}"
            )

            insights = metrics["insights"]
            print(f"\n--- INSIGHTS ---")
            print(f"Consensus reliability: {insights['consensus_reliability']}")
            print(f"RAG contribution: {insights['rag_contribution']}")
            print(f"LLM contribution: {insights['llm_contribution']}")

    # Extract final techniques for use
    final_techniques = validator.extract_final_techniques(results)
    print(f"\n--- FINAL VALIDATED TECHNIQUES ---")
    print(f"Chunks with validated techniques: {len(final_techniques)}")

    total_final_techniques = sum(len(techs) for techs in final_techniques.values())
    print(f"Total final validated techniques: {total_final_techniques}")

    # Display some examples
    sample_chunks = list(final_techniques.keys())[:3]
    for chunk_id in sample_chunks:
        techniques = final_techniques[chunk_id]
        print(f"\n{chunk_id}: {techniques}")


if __name__ == "__main__":
    main()
