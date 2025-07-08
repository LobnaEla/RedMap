# CTI IOC-Based Chunking

Extract IOCs from CTI reports and chunk text around detected indicators.

## Setup

1. Install dependencies
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. Set API key
```bash
echo "GROQ_API_KEY=your_api_key_here" > .env
```

## Usage

### Command Line
```bash
# Basic usage
python main.py

# Custom input file
python main.py --input your_report.txt

# Adjust context window
python main.py --window 3

# Save to specific file
python main.py --output results.json
```

### Python API
```python
from main import process_cti_text, process_cti_file, extract_iocs_only

# Process text directly
chunks = process_cti_text("Your CTI report text here", window=2)

# Process file
chunks = process_cti_file("report.txt", window=2)

# Extract IOCs only
iocs = extract_iocs_only("Malware connects to 192.168.1.1")

# Reusable processor for multiple reports
from main import create_processor
processor = create_processor()
chunks = processor.process_report(text, window=2)
```


## Output Format
```json
{
  "metadata": {
    "total_chunks": 5,
    "strategy": "ioc_based",
    "window_size": 2
  },
  "chunks": [
    {
      "chunk": "Text containing the IOC...",
      "ioc": "192.168.1.1",
      "type": "ipv4"
    }
  ]
}
```
