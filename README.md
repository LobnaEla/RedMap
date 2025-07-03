# 🔐 CTI Pipeline - Cyber Threat Intelligence Data Collection

## 📋 Overview

The **CTI Pipeline** is a comprehensive cyber threat intelligence data collection system that automatically gathers, processes, and stores threat intelligence data from multiple sources. This pipeline is designed to help security analysts and researchers aggregate threat intelligence from various feeds and formats into a centralized, structured format.

### 🎯 Key Features

- **Multi-source data collection**: RSS feeds, OTX pulses, PDF reports, Twitter feeds, HTML blogs
- **Intelligent text extraction**: Advanced OCR and PDF processing capabilities
- **Automated data ingestion**: Configurable pipeline for continuous data collection
- **Structured output**: All data stored in JSON Lines format for easy analysis
- **Web scraping**: Selenium-based Twitter monitoring for real-time threat intelligence

### 🏗️ Architecture

```
cti_pipeline/
├── __init__.py                 # Init package file
├── scripts/                    # Core ingestion and scraping modules
│   ├── __init__.py             # Init package file
│   ├── run_all.py              # Main orchestration script
│   ├── ingest_rss.py           # RSS feed ingestion
│   ├── ingest_otx.py           # OTX pulse ingestion
│   ├── ingest_pdf.py           # PDF report processing
│   ├── ingest_twitter.py       # Twitter keyword search
│   ├── ingest_twitter_users.py # Twitter user monitoring
│   ├── scraper_blog.py         # HTML blog scraping
│   ├── ExtractionTexte.py      # Text extraction tools for PDFs
│   └── ocr_library.py          # OCR-based extraction utilities
├── blog_sources.py             # List of blog URLs for scraping
├── pdf_sources.py              # List of PDF source URLs (optional)
├── config/
│   └── .env                    # API keys and configurations
├── data/                       # All collected data (ignored by Git)
│   ├── blogs/
│   ├── twitter/
│   └── ...
├── PDFs/                       # Local folder for PDF files
├── mitre_attack/               # ⚠️ Legacy or unused (ignored)
└── requirements.txt            # Dependencies

```

---

## 🚀 Quick Start Guide

### Step 1: Environment Setup

1. **Clone and navigate to the project directory**:
   ```bash
   cd your_directory
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Step 2: Configuration

1. **Create the configuration directory**:
   ```bash
   mkdir cti_pipeline\config
   ```

2. **Create environment file** `cti_pipeline\config\.env`:
   ```env
   # OTX API Configuration
   OTX_API_KEY=your_otx_api_key_here
   
   # VirusTotal API (optional)
   VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
   ```

3. **Get your API keys**:
   - **OTX API Key**: Register at [AlienVault OTX](https://otx.alienvault.com/) and get your API key
   - **VirusTotal API Key** (optional): Register at [VirusTotal](https://www.virustotal.com/) for enhanced threat analysis

### Step 3: Setup Chrome WebDriver

For Twitter ingestion, you need Chrome WebDriver:

1. **Install Chrome browser** (if not already installed)
2. **Download ChromeDriver** from [here](https://chromedriver.chromium.org/) matching your Chrome version
3. **Add ChromeDriver to your PATH** or place it in the project directory

### Step 4: Prepare Data Sources

1. **Create data directories**:
   ```bash
   mkdir cti_pipeline\data
   mkdir cti_pipeline\data\twitter
   mkdir cti_pipeline\data\blogs
   ```

2. **Add PDF reports** (optional):
   - Place any PDF threat intelligence reports in the `cti_pipeline\PDFs\` directory
   - The pipeline will automatically process all PDF files in this directory

---

## 📊 Running the Pipeline

### Option A: Run Complete Pipeline

Execute all data collection modules at once:

```bash
python -m cti_pipeline.scripts.run_all
```

This will:
- ✅ Collect OTX threat intelligence pulses
- ✅ Ingest RSS feeds from CERT-FR
- ✅ Process PDF reports in the PDFs directory
- ✅ Monitor specified Twitter accounts for threat intelligence
- ✅ collect blog posts (HTML scraping)

### Option B: Run Individual Modules

#### 1. RSS Feed Ingestion
```bash
python -m cti_pipeline.scripts.ingest_rss
```
**Output**: `cti_pipeline/data/raw_rss_certfr.jsonl`

#### 2. OTX Pulse Collection
```bash
python -m cti_pipeline.scripts.ingest_otx
```
**Output**: `cti_pipeline/data/raw_otx_pulses.jsonl`

#### 3. PDF Report Processing
```bash
python -m cti_pipeline.scripts.ingest_pdf
```
**Output**: `cti_pipeline/data/raw_pdf.jsonl`

#### 4. Twitter Monitoring
```bash
python -m cti_pipeline.scripts.ingest_twitter_users
```
**Output**: `cti_pipeline/data/twitter/[username].jsonl`

---

## 🔧 Configuration Options

### Monitored Twitter Accounts
Edit `cti_pipeline/scripts/run_all.py` to modify the Twitter accounts being monitored:

```python
users = ["vxunderground", "CERT_FR", "CISACyber", "your_account_here"]
```

### CTI Keywords
The pipeline filters content based on these cybersecurity keywords:

```python
CTI_KEYWORDS = [
    "Advanced Persistent Threat", "CVE", "IOC", "phishing", 
    "ransomware", "malware", "exploit", "MITRE", "threat", 
    "vulnerability", "APT", "TTPs", "attack"
]
```

### PDF Sources
Add new PDF sources in `cti_pipeline/pdf_sources.py`:

```python
PDF_SOURCES = [
    {
        "name": "Your Source Name",
        "url": "https://example.com/threat-reports"
    }
]
```

---

## 📄 Output Data Format

All collected data is stored in JSON Lines format. Each record contains:

### RSS Feed Records
```json
{
  "source": "CERT-FR RSS",
  "type": "rss_bulletin",
  "title": "Alert Title",
  "link": "https://cert.ssi.gouv.fr/...",
  "date_published": "2024-01-01T00:00:00Z",
  "content": "Alert content...",
  "date_collected": "2024-01-01 12:00:00"
}
```

### OTX Pulse Records
```json
{
  "source": "OTX",
  "type": "cti_pulse",
  "title": "Threat Campaign Name",
  "description": "Detailed description...",
  "tags": ["malware", "apt", "ransomware"],
  "indicators": [...],
  "tlp": "TLP:WHITE",
  "date_collected": "2024-01-01 12:00:00"
}
```

### PDF Report Records
```json
{
  "source": "report.pdf",
  "type": "report",
  "content": "Extracted text content...",
  "date": "2024-01-01 12:00:00",
  "format": "PDF"
}
```

### Twitter Records
```json
{
  "source": "twitter",
  "type": "tweet",
  "username": "vxunderground",
  "text": "Tweet content...",
  "date_collected": "2024-01-01 12:00:00",
  "cti_relevant": true
}
```

---

## 🛠️ Advanced Features

### OCR Processing
The pipeline includes advanced OCR capabilities for processing image-based PDFs:

- **DocTR integration**: State-of-the-art document text recognition
- **spaCy processing**: Intelligent text cleaning and token boundary detection
- **Custom post-processing**: Fixes common OCR errors and formatting issues

### Automated Filtering
Content is automatically filtered based on:
- **Keyword matching**: CTI-relevant terms
- **Source credibility**: Trusted threat intelligence sources
- **Content type**: Structured threat intelligence formats

### Error Handling
- **Robust error recovery**: Continues processing even if individual sources fail
- **Detailed logging**: Comprehensive error reporting and debugging information
- **Graceful degradation**: Partial success when some modules encounter issues

---

## 📁 Directory Structure After Setup

```
Implementation/
├── .venv/                    # Virtual environment
├── cti_pipeline/
│   ├── config/
│   │   └── .env              # API keys and configuration
│   ├── data/                 # Output data directory
│   │   ├── raw_rss_certfr.jsonl
│   │   ├── raw_otx_pulses.jsonl
│   │   ├── raw_pdf.jsonl
│   │   └── twitter/
│   │       ├── vxunderground.jsonl
│   │       ├── CERT_FR.jsonl
│   │       └── CISACyber.jsonl
│   ├── PDFs/                 # PDF storage
│   │   └── [your-pdf-reports.pdf]
│   └── scripts/              # Core modules
├── requirements.txt          # Dependencies
└── README.md                 # This file
```

*Last updated: July 2025*                                                                            
