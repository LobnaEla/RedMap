cti_pipeline/
└── preprocess/
    
    # Cleaning Step
    cleaning/
    ├── __init__.py
    ├── base.py                      # BaseCleaning class with shared logic
    ├── html_cleaning.py              # HTMLCleaning inherits from BaseCleaning
    └── pdf_cleaning.py               # PDFCleaning inherits from BaseCleaning

    # Extraction Step
    extraction/
    ├── __init__.py
    ├── base.py                      # BaseExtraction class
    └── html_extraction.py           # HTMLExtraction inherits from BaseExtraction

    # Normalization Step
    normalization/
    ├── __init__.py
    └── normalize_generic.py        # Generic normalization step

    # Chunking Step
    chunking/
    ├── __init__.py
    └── chunk_by_sentences.py       # Chunking by sentence logic

    # Preprocess Utilities
    utils/
    ├── __init__.py
    ├── error_handling.py           # Error handling logic
    └── metrics.py                  # Time/performance logging, etc.

    # Preprocess Orchestration
    registry.py                                   # Maps string names to class/function
    runner.py                                     # Executes the preprocessing pipeline from config
    validator.py                                  # Optional: validates pipeline config (YAML schema)

airflow/
├── dags/
│   ├── ingestion_dag.py              # DAG for ingesting data per source
│   └── preprocessing_dag.py          # DAG for dynamic, per-source pipelines
│
├── plugins/                          # Optional custom Airflow plugins (sensors, hooks)
│   └── __init__.py
│
├── config/                           # Airflow runtime config
│   └── airflow.cfg
│
├── Dockerfile                        # Custom image for Airflow workers
├── docker-compose.yml                # Multi-container setup
└── .env                              # Env vars for local orchestration
