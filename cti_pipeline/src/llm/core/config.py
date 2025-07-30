import os

# Configuration des chemins
BASE_PROJECT_PATH = "/opt/project/cti_pipeline"
PATH_CONFIG = {
    "chunks": os.path.join(BASE_PROJECT_PATH, "chunks"),
    "llm_results": os.path.join(BASE_PROJECT_PATH, "llm_results"),
    "mitre_mappings": os.path.join(BASE_PROJECT_PATH, "mitre_mappings"),
    "logs": os.path.join(BASE_PROJECT_PATH, "logs"),
}

# Configuration LLM
LLM_CONFIG = {
    "model": "gemini-2.0-flash",
    "max_tokens": 200,
    "temperature": 0.1,
    "max_retries": 3,
    "batch_size": 10,
    "request_delay": 0.5,  # Délai entre les requêtes
    "file_delay": 2,  # Délai entre les fichiers
}
