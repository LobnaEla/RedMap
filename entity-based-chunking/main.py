import json
import os
from datetime import datetime
from chunking.processor import CTIProcessor
from utils.config import load_config


def main():
    config = load_config()
    processor = CTIProcessor(config=config)

    # Load CTI report from file
    with open("tests/example_cti_report.txt", "r", encoding="utf-8") as f:
        example_text = f.read()

    results = processor.process_report(example_text)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Generate timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"output/chunked_results_{timestamp}.json"
    
    # Save results to JSON file
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_filename}")
    print(f"Total chunks generated: {len(results) if isinstance(results, list) else 'N/A'}")
    
    # Also print results to console for immediate viewing
    print("\nResults preview:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()