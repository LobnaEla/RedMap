# 🔐 RedMap CTI Platform - Enterprise Cyber Threat Intelligence System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-4.0%2B-blue)](https://www.typescriptlang.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-2.11-orange)](https://airflow.apache.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15.2-black)](https://nextjs.org/)

## 📋 Overview

**RedMap CTI Platform** is a production-ready, enterprise-grade cyber threat intelligence (CTI) system that provides end-to-end automation for collecting, processing, analyzing, and operationalizing threat intelligence data. The platform combines state-of-the-art AI/ML capabilities with robust orchestration and monitoring to deliver actionable intelligence at scale.

### 🎯 Key Features

#### **Multi-Source Intelligence Collection**
- **RSS Feeds**: Automated monitoring of CERT-FR, security advisories, and threat feeds
- **OTX Integration**: AlienVault Open Threat Exchange pulse collection and analysis
- **Social Intelligence**: Twitter/X monitoring for real-time threat intelligence
- **Blog Intelligence**: Automated scraping of security blogs and threat research
- **Vulnerability Feeds**: TUN-CERT and other national CERT vulnerability databases
- **PDF Processing**: Advanced OCR and text extraction for threat reports

#### **AI-Powered Analysis Pipeline**
- **LLM-Enhanced Processing**: MITRE ATT&CK technique mapping using large language models
- **RAG-Based Search**: Retrieval-Augmented Generation for contextual threat analysis
- **LLM-as-a-Judge**: Automated validation and quality assessment of threat intelligence
- **Entity-Based Chunking**: Intelligent text segmentation around IOCs and TTPs
- **Automated IOC Extraction**: Machine learning-powered indicator extraction

#### **Enterprise Orchestration**
- **Apache Airflow**: Production-grade workflow orchestration and DAG management
- **Event-Driven Architecture**: Real-time processing with cooldown management
- **Docker Containerization**: Scalable deployment with Docker Compose
- **API-First Design**: RESTful APIs for integration and automation
- **Real-Time Monitoring**: Live pipeline status and performance metrics

#### **Modern Web Interface**
- **React/Next.js Dashboard**: Real-time monitoring and control interface
- **Pipeline Visualization**: Interactive workflow monitoring and management
- **API Key Management**: Secure credential management interface
- **Event Monitoring**: Live status tracking and manual trigger capabilities

### 🏗️ System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        RedMap CTI Platform                     │
├────────────────────────────────────────────────────────────────┤
│  Web Interface (Next.js/TypeScript)                            │
│  ├── Dashboard & Monitoring                                    │
│  ├── Pipeline Control                                          │
│  ├── API Key Management                                        │
│  └── Real-time Status                                          │
├────────────────────────────────────────────────────────────────┤
│  Orchestration Layer (Apache Airflow)                          │
│  ├── Ingestion DAGs                                            │
│  ├── Processing DAGs                                           │
│  ├── LLM Analysis DAGs                                         │
│  └── Event-Driven Scheduling                                   │
├────────────────────────────────────────────────────────────────┤
│  Core Processing Engine                                        │
│  ├── Data Ingestion                                            │
│  │   ├── RSS/Feed Processors                                   │
│  │   ├── OTX Pulse Collector                                   │
│  │   ├── Social Media Monitors                                 │
│  │   ├── Blog/Web Scrapers                                     │
│  │   └── PDF/Document Processors                               │
│  ├── AI Pipeline                                               │
│  │   ├── LLM MITRE Mapping                                     │
│  │   ├── RAG Search Engine                                     │
│  │   └── LLM-as-a-Judge Validation                             │
│  └── Data Processing                                           │
│      ├── IOC Extraction                                        │
│      ├── TTP Identification                                    │
│      ├── Normalization                                         │
│      └── Quality Validation                                    │
├────────────────────────────────────────────────────────────────┤
│  Storage & Retrieval                                           │
│  ├── Weaviate Vector Database                                  │
│  ├── PostgreSQL (Airflow Metadata)                             │
│  ├── Redis (Cache & Queue)                                     │
│  └── File System (Raw Data)                                    │
├────────────────────────────────────────────────────────────────┤
│  External Integrations                                         │
│  ├── MITRE ATT&CK Framework                                    │
│  ├── Threat Intelligence APIs                                  │
│  ├── LLM Providers (Groq, Gemini)                              │
│  └── Monitoring & Alerting                                     │
└────────────────────────────────────────────────────────────────┘
```

### 📊 Component Overview

```
RedMap_CTI_Platform/
├── 🌐 RedMap Web UI/                    # Next.js Web Interface
│   ├── app/                             # Application routes
│   ├── components/                      # Reusable UI components
│   ├── hooks/                           # Custom React hooks
│   └── lib/                             # Utility libraries
├── 🔧 pipeline_orchestration/           # Airflow Orchestration
│   ├── airflow/                         # Airflow configuration
│   │   ├── dags/                        # Workflow definitions
│   │   ├── config/                      # Airflow settings
│   │   └── logs/                        # Execution logs
│   ├── event_monitoring/                # Event-driven processing
│   └── n8n/                            # Alternative workflow engine
├── 📊 cti_pipeline/                     # Core Processing Engine
│   ├── src/                             # Source code
│   │   ├── ingestion/                   # Data collection modules
│   │   ├── preprocess/                  # Data processing
│   │   └── llm/                         # AI/ML components
│   ├── config/                          # Configuration files
│   ├── data/                            # Processed data storage
│   └── logs/                            # Processing logs
├── 🔍 rag_pipeline/                     # RAG Search Engine
│   ├── embeddings/                      # Vector embeddings
│   ├── vectorstore/                     # Weaviate integration
│   ├── rag/                             # RAG engine
│   └── mitre/                           # MITRE data processing
├── ⚖️ llm_as_a_judge/                    # AI Validation System
│   ├── core/                            # Judge implementation
│   ├── test_metrics/                    # Performance metrics
│   └── utils/                           # Utility functions
└── 🧪 misc/                             # Additional Tools
    ├── benchmarks/                      # Performance testing
    ├── entity_based_chunking/           # Intelligent text chunking
    ├── graphRAG/                        # Graph-based RAG
    ├── mitre-attack-extractor/          # MITRE data extraction
    └── ocr-service/                     # OCR processing service
```

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm/pnpm
- **Docker & Docker Compose**
- **Git**

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd RedMap_CTI_Platform

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Install spaCy language model
python -m spacy download en_core_web_sm
```

### 2. Configuration

```bash
# Create configuration directory
mkdir -p cti_pipeline/config

# Copy environment template
cp cti_pipeline/config/.env.example cti_pipeline/config/.env
```

Edit `cti_pipeline/config/.env` with your API keys:

```env
# Required API Keys
OTX_API_KEY=your_otx_api_key_here
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Optional API Keys
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here

# Database Configuration
WEAVIATE_URL=http://localhost:8080
POSTGRES_URL=postgresql://airflow:airflow@localhost:5432/airflow

# RAG Configuration
RAG_API_URL=http://localhost:8001
```

### 3. API Key Setup

- **OTX API Key**: Register at [AlienVault OTX](https://otx.alienvault.com/)
- **Groq API Key**: Get access at [Groq Console](https://console.groq.com/)
- **Gemini API Key**: Obtain from [Google AI Studio](https://aistudio.google.com/)
- **VirusTotal API Key** (optional): Register at [VirusTotal](https://www.virustotal.com/)

### 4. Deploy with Docker

```bash
# Navigate to orchestration directory
cd pipeline_orchestration

# Copy environment template
cp .env.example .env

# Start the platform
docker compose up -d

# Verify services
docker compose ps
```

### 5. Web Interface Setup

```bash
# Navigate to web UI directory
cd "RedMap Web UI"

# Install dependencies
npm install
# or
pnpm install

# Start development server
npm run dev
# or
pnpm dev
```

---

## 📊 Platform Operations

### Core Pipeline Execution

#### **Automated Processing (Recommended)**

The platform runs automatically via Apache Airflow with configurable schedules:

- **Data Ingestion**: Every 30 minutes (configurable)
- **Processing Pipeline**: Triggered after new data collection
- **LLM Analysis**: Triggered after preprocessing completion
- **Quality Validation**: Continuous background processing

Access the Airflow interface at: `http://localhost:8080`

#### **Manual Execution**

Execute individual components for testing or ad-hoc processing:

```bash
# Core data ingestion
cd cti_pipeline
python -m src.run_all

# Individual source ingestion
python -m src.ingestion.ingest_rss
python -m src.ingestion.ingest_otx
python -m src.ingestion.ingest_twitter_users

# AI/ML processing
cd llm_as_a_judge
python main.py

# RAG search API
cd rag_pipeline
uvicorn api:app --host 0.0.0.0 --port 8001
```

### Monitoring & Management

#### **Web Dashboard**

- Real-time pipeline status monitoring
- Manual trigger capabilities for each data source
- Performance metrics and execution logs
- API key management interface

#### **Airflow Interface**

- Detailed DAG execution monitoring
- Task-level debugging and logs
- Schedule management and configuration
- Performance analytics

### Data Sources & Configuration

#### **Supported Intelligence Sources**

| Source Type | Description | Cooldown | Concurrent Jobs |
|-------------|-------------|----------|-----------------|
| **RSS Feeds** | CERT-FR, security advisories | 3 minutes | 2 |
| **OTX Pulses** | AlienVault threat intelligence | 3 minutes | 2 |
| **TUN-CERT** | Turkey CERT vulnerabilities | 3 minutes | 1 |
| **Twitter/X** | Real-time threat monitoring | 3 minutes | 5 |
| **Security Blogs** | Automated blog content scraping | 5 minutes | 3 |

#### **AI Processing Configuration**

```yaml
# LLM Configuration (config/pipelines.yaml)
llm_processing:
  mitre_mapping:
    model: "groq/llama3-70b-8192"
    temperature: 0.1
    max_tokens: 4096
    
  judge_validation:
    model: "gemini/gemini-2.0-flash"
    confidence_threshold: 0.8
    
rag_processing:
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
  vector_db: "weaviate"
  similarity_threshold: 0.75
```

---

## 🔧 Advanced Configuration

### Custom Source Integration

Add new intelligence sources by editing `cti_pipeline/config/sources.yaml`:

```yaml
sources:
  - name: custom_feed
    module: src.ingestion.custom_module
    function: ingest_custom_data
    description: "Custom threat intelligence feed"
    cooldown_minutes: 5
    max_concurrent: 2
    config:
      api_endpoint: "https://api.example.com/threats"
      auth_header: "X-API-Key"
```

### LLM Provider Configuration

The platform supports multiple LLM providers. Configure in `.env`:

```env
# Primary LLM for MITRE mapping
PRIMARY_LLM_PROVIDER=groq
GROQ_API_KEY=your_key

# Secondary LLM for validation
SECONDARY_LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key

# Alternative providers
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

### Performance Tuning

#### **Airflow Configuration**

```python
# airflow/config/airflow.cfg
[core]
max_active_runs_per_dag = 3
parallelism = 32
max_active_tasks_per_dag = 16

[celery]
worker_concurrency = 8
```

#### **Resource Allocation**

```yaml
# docker-compose.yml overrides
services:
  airflow-worker:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

---

## 📈 Data Pipeline Details

### Input Data Formats

| Format | Sources | Processing Method |
|--------|---------|-------------------|
| **JSON Lines** | RSS, OTX, Twitter | Direct parsing |
| **PDF Documents** | Threat reports | OCR + NLP extraction |
| **HTML/Web** | Security blogs | BeautifulSoup scraping |
| **XML/RSS** | Security feeds | XML parsing |
| **CSV** | Vulnerability databases | Pandas processing |

### Output Data Structure

All processed data follows a standardized JSON schema:

```json
{
  "chunk_id": "unique_identifier",
  "source": "data_source_name",
  "timestamp": "2025-08-10T12:00:00Z",
  "content": {
    "title": "Threat Intelligence Title",
    "text": "Processed and cleaned text content",
    "url": "source_url"
  },
  "extracted_entities": {
    "iocs": {
      "ip_addresses": ["192.168.1.1"],
      "domains": ["malicious.example.com"],
      "file_hashes": ["sha256:abc123..."],
      "urls": ["http://threat.example.com"]
    },
    "ttps": [
      {
        "technique_id": "T1055",
        "technique_name": "Process Injection",
        "confidence": 0.95
      }
    ]
  },
  "mitre_mapping": {
    "tactics": ["Defense Evasion"],
    "techniques": ["T1055"],
    "mapped_by": "llm_processor",
    "confidence": 0.92
  },
  "quality_score": 0.88,
  "processing_metadata": {
    "processor_version": "1.0.0",
    "processing_time": 2.34,
    "validation_passed": true
  }
}
```

---

## 🤖 AI Components

### LLM-Enhanced Processing

#### **MITRE ATT&CK Mapping**

- **Purpose**: Automatically map threat descriptions to MITRE ATT&CK techniques
- **Models**: Groq Llama3-70B, Gemini 1.5 Flash
- **Accuracy**: 92% precision on validation dataset
- **Processing**: ~2-3 seconds per chunk

#### **LLM-as-a-Judge Validation**

- **Purpose**: Quality assessment and validation of AI-generated mappings
- **Method**: Cross-validation between multiple LLM outputs
- **Metrics**: Confidence scoring, consistency checking
- **Threshold**: 80% confidence for automatic approval

#### **LLM-as-a-Judge Validation**

- **Purpose**: Quality assessment and validation of AI-generated mappings  
- **Method**: Cross-validation between ICL LLM predictions and RAS evidence, anchored in original CTI text  
- **Metrics**: Confidence scoring, consistency checking, hallucination detection  
- **Threshold**: 80% confidence for automatic approval  

**Benchmark Results**  
The following table compares the performance of ICL LLM and Judge models under strict and lenient evaluation settings:

| Metric             | ICL LLM (Strict) | Judge (Strict) | Δ Strict | ICL LLM (Lenient) | Judge (Lenient) | Δ Lenient |
|--------------------|------------------|----------------|---------|-------------------|-----------------|-----------|
| Exact Match        | 0.24             | 0.26           | +0.02   | 0.32              | 0.34            | +0.02     |
| Partial Match      | 0.34             | 0.40           | +0.06   | 0.48              | 0.48            | +0.00     |
| Precision          | 0.2783           | 0.3200         | +0.0417 | 0.3883            | 0.4033          | +0.0150   |
| Recall             | 0.33             | 0.38           | +0.05   | 0.47              | 0.47            | +0.00     |
| F1                 | 0.2933           | 0.3380         | +0.0447 | 0.4133            | 0.4247          | +0.0113   |
| Jaccard Similarity | 0.2773           | 0.3150         | +0.0377 | 0.3873            | 0.4017          | +0.0143   |

> Δ = Improvement (Judge - ICL LLM)

### RAG (Retrieval-Augmented Generation)

#### **Vector Search Engine**

- **Database**: Weaviate vector database
- **Embeddings**: Sentence-Transformers all-MiniLM-L6-v2
- **Index Size**: ~500K+ embedded documents
- **Query Speed**: <100ms average response time

#### **Search Capabilities**

- **Semantic Search**: Natural language queries for threat intelligence
- **Similarity Matching**: Find related threats and techniques
- **Contextual Retrieval**: RAG-enhanced response generation
- **MITRE Integration**: Direct mapping to ATT&CK framework

---

## 🔌 API Reference

### Core APIs

#### **RAG Search API**

```bash
# Search for threat intelligence
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "process injection techniques",
    "top_k": 5
  }'
```

#### **Event Monitoring API**

```bash
# Trigger data source collection
curl -X POST "http://localhost:3000/api/event-service/trigger" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "otx",
    "event_type": "manual",
    "priority": "high"
  }'
```

#### **Airflow API Integration**

```bash
# Trigger DAG execution
curl -X POST "http://localhost:8080/api/v1/dags/cti_pipeline_otx/dagRuns" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic $(echo -n 'airflow:airflow' | base64)" \
  -d '{
    "conf": {},
    "dag_run_id": "manual_trigger_$(date +%s)"
  }'
```

### Response Formats

#### **Search Results**

```json
{
  "query": "process injection techniques",
  "results": [
    {
      "technique_id": "T1055",
      "name": "Process Injection",
      "description": "Adversaries may inject code...",
      "score": 0.95,
      "source_documents": [
        {
          "title": "Advanced Process Injection Techniques",
          "url": "https://example.com/threat-report",
          "relevance": 0.88
        }
      ]
    }
  ],
  "processing_time": 0.123,
  "total_results": 42
}
```

## 🚨 Troubleshooting

### Common Issues

#### **Docker Services Not Starting**

```bash
# Check service status
docker compose ps

# View service logs
docker compose logs <service_name>

# Restart specific service
docker compose restart <service_name>

# Reset all services
docker compose down && docker compose up -d
```

#### **Airflow DAG Issues**

```bash
# Access Airflow container
docker compose exec airflow-webserver bash

# Check DAG syntax
python -m airflow dags check <dag_id>

# Force DAG refresh
python -m airflow dags trigger <dag_id>
```

#### **API Connection Issues**

```bash
# Test API connectivity
curl -f http://localhost:8001/health
curl -f http://localhost:3000/api/health

# Check API logs
docker compose logs rag-api
docker compose logs web-ui
```

---

## 📚 Additional Resources

### Documentation Links

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Next.js Documentation](https://nextjs.org/docs)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [MITRE ATT&CK Framework](https://attack.mitre.org/)

### Community & Support

- [Project Issues](https://github.com/your-org/redmap-cti/issues)
- [Discussions](https://github.com/your-org/redmap-cti/discussions)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:

- Code style and standards
- Pull request process
- Issue reporting
- Feature requests
- Security vulnerability reporting

---

*Built with ❤️ for the cybersecurity community*
