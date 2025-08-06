"""Fixed usage examples for LLM-as-a-Judge module."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get current directory and project root
current_dir = Path(__file__).parent
project_root = current_dir.parent

# Load .env file
env_path = current_dir.parent / ".env"
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


def example_single_validation():
    """Example of single chunk validation - FIXED."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")

    validator = TechniqueValidator(api_key=api_key)

    # Sample CTI chunk
    chunk_data = {
        "chunk_id": "example_001",
        "text": "The malware uses PowerShell scripts to download additional payloads from remote servers. "
        "It establishes persistence through scheduled tasks and modifies registry entries.",
        "iocs": "powershell.exe, schtasks.exe, reg.exe",
        "source_file": "example_report.pdf",
    }

    # Simulated results
    rag_results = ["T1059.001", "T1105", "T1053.005"]  # RAG/RAS
    llm_results = ["T1059.001", "T1053.005", "T1547.001"]  # LLM/ICL

    print("=" * 60)
    print("SINGLE CHUNK VALIDATION EXAMPLE")
    print("=" * 60)

    print(f"🔍 Input Analysis:")
    print(f"  RAG techniques: {rag_results}")
    print(f"  LLM techniques: {llm_results}")

    # Calculate overlap manually
    rag_set = set(rag_results)
    llm_set = set(llm_results)
    common = rag_set & llm_set
    rag_only = rag_set - llm_set
    llm_only = llm_set - rag_set

    print(f"  Common: {sorted(common)}")
    print(f"  RAG-only: {sorted(rag_only)}")
    print(f"  LLM-only: {sorted(llm_only)}")
    print(f"  Overlap rate: {len(common) / len(rag_set | llm_set) * 100:.1f}%")

    # Cross-validation via LLM-as-a-Judge
    print(f"\n⚖️ Running LLM-as-a-Judge validation...")

    result = validator.validate_single_chunk(
        chunk_data=chunk_data, rag_results=rag_results, llm_results=llm_results
    )

    print(f"\n📊 Validation Results:")
    print(f"  Chunk ID: {result.get('chunk_id')}")
    print(f"  Success: {result.get('success')}")

    if result.get("success"):
        final_techniques = result.get("final_validated_techniques", [])
        print(f"  Final techniques: {sorted(final_techniques)}")

        # Detailed analysis
        judge_result = result.get("judge_result", {})
        analysis = judge_result.get("technique_analysis", {})

        if analysis:
            print(f"\n🔍 Technique Analysis:")
            for tech_id, details in analysis.items():
                status = details.get("status", "unknown")
                confidence = details.get("confidence", 0)
                evidence = details.get("evidence", "N/A")
                source = details.get("source", "unknown")

                print(
                    f"  {tech_id}: {status.upper()} (conf={confidence:.2f}, source={source})"
                )
                print(f"    Evidence: {evidence}")

                reasoning = details.get("reasoning", "")
                if reasoning:
                    print(f"    Reasoning: {reasoning[:100]}...")

    else:
        print(f"  Error: {result.get('error', 'Unknown error')}")

    return result


def example_batch_validation():
    """Example of batch validation - FIXED."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")

    validator = TechniqueValidator(api_key=api_key)

    # Sample chunks
    chunks = [
        {
            "chunk_id": "batch_001",
            "text": "The attacker used RDP to move laterally across the network after "
            "obtaining valid credentials through credential dumping.",
            "iocs": "mstsc.exe, 3389/tcp, lsadump",
        },
        {
            "chunk_id": "batch_002",
            "text": "Sensitive data was collected from file shares and compressed using "
            "WinRAR before being exfiltrated to cloud storage services.",
            "iocs": "winrar.exe, *.rar files, network uploads",
        },
    ]

    # Simulated results
    rag_results_list = [
        ["T1021.001", "T1078", "T1003"],
        ["T1005", "T1560.001", "T1567.002"],
    ]
    llm_results_list = [
        ["T1021.001", "T1078", "T1090"],
        ["T1560.001", "T1567.002", "T1041"],
    ]

    print("=" * 60)
    print("BATCH VALIDATION EXAMPLE")
    print("=" * 60)

    # Run batch validation
    print(f"⚖️ Running batch validation for {len(chunks)} chunks...")
    results = validator.batch_validate(
        chunks=chunks,
        rag_results_list=rag_results_list,
        llm_results_list=llm_results_list,
    )

    # Metrics
    validation_metrics = calculate_validation_metrics(results["validations"])
    results["detailed_metrics"] = validation_metrics

    stats = results.get("statistics", {})
    print(f"\n📊 Batch Results:")
    print(f"  Total chunks: {stats.get('total_chunks', 0)}")
    print(f"  Successful: {stats.get('successful_validations', 0)}")
    print(f"  Success rate: {stats.get('success_rate', 0):.1%}")
    print(f"  Techniques analyzed: {stats.get('total_techniques_analyzed', 0)}")
    print(f"  Techniques validated: {stats.get('total_techniques_validated', 0)}")
    print(f"  Validation rate: {stats.get('average_validation_rate', 0):.1%}")
    print(f"  Consensus accuracy: {stats.get('consensus_accuracy', 0):.1%}")

    # Print source contribution
    print(f"  RAG contribution: {stats.get('rag_only_contribution', 0):.1%}")
    print(f"  LLM contribution: {stats.get('llm_only_contribution', 0):.1%}")

    # Extract and display final techniques
    print("\n✅ Final Validated Techniques:")
    final_techniques = validator.extract_final_techniques(results)
    for chunk_id, techniques in final_techniques.items():
        print(f"  {chunk_id}: {sorted(techniques)}")

    # Optional: Save results to disk
    full_results_path = save_judge_results(results, include_detailed=True)
    final_only_path = save_final_techniques_only(results)

    print(f"\n💾 Results saved:")
    print(f"  📄 Full: {full_results_path}")
    print(f"  📄 Final only: {final_only_path}")

    return results


if __name__ == "__main__":
    # Run both examples if file is executed directly
    example_single_validation()
    print("\n" + "=" * 60 + "\n")
    example_batch_validation()
