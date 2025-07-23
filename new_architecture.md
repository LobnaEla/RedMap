cti_pipeline/
├── config/
│   ├── blog_sources.py
│   ├── pipelines.yaml
│   ├── sources.yaml
│   └── .env.example
├── data/
├── logs/
├── PDFs/
├── samples/
├── src/
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── ingest_otx.py
│   │   ├── ingest_rss.py
│   │   ├── ingest_tuncert.py
│   │   ├── ingest_twitter_users.py
│   │   └── scraper_blog.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── anthropic_client.py
│   │   │   ├── chunk_processor.py
│   │   │   ├── config.py
│   │   │   ├── file_utils.py
│   │   │   └── prompt_utils.py
│   │   ├── tests/
│   │   │   ├── __main__.py
│   │   │   └── test.py
│   │   └── .env.example
│   ├── preprocess/
│   │   ├── __init__.py
│   │   ├── chunking/
│   │   │   ├── __init__.py
│   │   │   └── chunker.py
│   │   ├── cleaning/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── cleaning_patterns.py
│   │   │   ├── html_cleaner.py
│   │   │   ├── json_cleaner.py
│   │   │   ├── ocr_cleaner.py
│   │   │   ├── pdf_cleaner.py
│   │   │   └── tests/
│   │   │       ├── __init__.py
│   │   │       ├── run_tests.py
│   │   │       ├── test_base_cleaning.py
│   │   │       ├── test_html_cleaning.py
│   │   │       ├── test_json_cleaning.py
│   │   │       ├── test_ocr_cleaning.py
│   │   │       └── test_pdf_cleaning.py
│   │   ├── extraction/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── csv_extractor.py
│   │   │   ├── html_extractor.py
│   │   │   ├── json_extractor.py
│   │   │   ├── pdf_extractor.py
│   │   │   ├── txt_extractor.py
│   │   │   └── tests/
│   │   │       ├── __init__.py
│   │   │       ├── run_tests.py
│   │   │       ├── test_base_extraction.py
│   │   │       ├── test_csv_extraction.py
│   │   │       ├── test_html_extraction.py
│   │   │       ├── test_json_extraction.py
│   │   │       ├── test_pdf_extraction.py
│   │   │       └── test_txt_extraction.py
│   │   ├── normalizing/
│   │   │   ├── __init__.py
│   │   │   ├── normalization.py
│   │   │   └── tests/
│   │   │       ├── __init__.py
│   │   │       ├── debug_tests.py
│   │   │       ├── run_tests.py
│   │   │       └── test_normalization.py
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   ├── error_handling.py
│   │   │   ├── patterns.py
│   │   │   ├── preservers.py
│   │   │   └── utilities.py
│   ├── run_all.py
│   ├── utilities.py
│   └── __init__.py
└── __init__.py

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
