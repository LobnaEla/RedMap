# LLM-as-a-Judge Module

## 📌 Overview
The **LLM-as-a-Judge** module is a specialized evaluation and validation component for Large Language Model (LLM) outputs, primarily designed for mapping **Cyber Threat Intelligence (CTI)** to the **MITRE ATT&CK** framework.  
It operates by validating the predictions of a primary LLM against evidence retrieved from a **Retrieval-Augmented Search (RAS)** process, providing an additional expert-like layer of assessment.

This module is part of the larger **REDMAP** pipeline, but it can also be used independently for LLM output validation tasks.

---

## ⚙️ Features
- **Forensic-style evaluation** of LLM predictions.
- **Cross-validation with RAS evidence** to reduce hallucinations.
- Modular and reusable **prompt creation utilities**.
- **Configurable LLM client** for different providers (OpenAI, Gemini, etc.).
- Metrics logging for **pre- and post-validation comparisons**.
- Easy integration with **FastAPI**, **Airflow**, or **n8n** pipelines.

---

## 📂 Project Structure
llm_as_a_judge/
│── main.py # Entry point for running validations
│── init.py
│
├── core/
│ ├── config.py # Configuration management (.env variables)
│ ├── judge_client.py # Handles LLM API calls for validation
│ ├── prompt_utils.py # Utilities for constructing judge prompts
│ ├── technique_validator.py # Core validation logic for technique IDs
│ └── init.py
│
├── tests/
│ └── usage_example.py # Example usage script
│
├── test_metrics/ # Generated CSV metrics for evaluations
│
├── prompt_engineering.ipynb # Notebook for prompt experimentation
├── .env # Environment variables (API keys, configs)
└── README.md # Documentation for the module

