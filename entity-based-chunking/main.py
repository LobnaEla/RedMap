import json
from chunking.processor import CTIProcessor
from utils.config import load_config


def main():
    config = load_config()
    processor = CTIProcessor(config=config)

    # Load CTI report from file
    with open("tests/example_cti_report.txt", "r", encoding="utf-8") as f:
        example_text = f.read()

    results = processor.process_report(example_text)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()