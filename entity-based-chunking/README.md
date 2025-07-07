# Entity-Based Chunking 
This feature provides a  pipeline for extracting Indicators of Compromise (IOCs) from Cyber Threat Intelligence (CTI) reports using a Groq-hosted LLM (e.g., LLaMA 3), and chunking the report text based on the detected IOCs.

## Features
- **IOC Extraction:** Uses Groq API to extract IOCs (IP addresses, domains, URLs, file hashes, emails) from raw CTI text.
- **Contextual Chunking:** Finds each IOC in the original text and extracts a window of sentences around it.
- **Modular Design:** Easily swap out the LLM, chunker, or config loader.
- **Configurable:** Prompts and model settings are managed in `config.yaml`.
- **Testable:** Example CTI reports are stored in the `tests/` folder for easy experimentation.

##  Structure
```
entity-based-chunking/
│
├── main.py                # Entry point: loads a CTI report and prints chunked results
├── config.yaml            # Model and prompt configuration
├── requirements.txt       # Python dependencies
│
├── chunking/
│   ├── groq_client.py     # Handles Groq API and IOC extraction
│   ├── text_chunker.py    # Handles sentence splitting and chunking
│   ├── processor.py       # Orchestrates the pipeline
│   └── __init__.py
│
├── utils/
│   ├── config.py          # Loads config and environment variables
│   └── __init__.py
│
└── tests/
    └── example_cti_report.txt  # Example CTI report for testing
```

## How It Works
1. **IOC Extraction:**
   - The CTI report is sent to the Groq LLM with a system prompt instructing it to return all IOCs in JSON format.
2. **Chunking:**
   - The text is split into sentences (using spaCy or NLTK).
   - For each IOC, the code finds all sentences containing it and extracts a window of sentences around each occurrence.
   - Each chunk is tagged with its IOC and type.
3. **Output:**
   - The result is a list of chunks, each with its text, IOC, and type.

## Quickstart
1. **Clone the repository and install dependencies:**
   ```sh
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```
2. **Set your Groq API key:**
   - Create a `.env` file in the project root:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```
3. **Run the pipeline:**
   ```sh
   python main.py
   ```
   - The script will load the example CTI report from `tests/example_cti_report.txt` and print the chunked results.

## Customization
- **To test other CTI reports:**
  - Add a `.txt` file to the `tests/` folder and update the path in `main.py`.
- **To change the LLM prompt or model:**
  - Edit `config.yaml`.
- **To adjust chunk size:**
  - Change the `window` parameter in `main.py` or in the `process_report` call.

