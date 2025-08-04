import os

BASE_PROJECT_PATH = "/opt/project/cti_pipeline"

JUDGE_CONFIG = {
    "model": "gemini-2.0-flash",
    "temperature": 0.1,
    "max_tokens": 500,
    "max_retries": 3,
    "evaluation_criteria": {
        "accuracy": 0.3,  # Poids pour la précision des techniques
        "coverage": 0.25,  # Poids pour la couverture des techniques
        "relevance": 0.25,  # Poids pour la pertinence contextuelle
        "specificity": 0.2,  # Poids pour la spécificité des techniques
    },
}

PATH_CONFIG = {
    "evaluations": os.path.join(BASE_PROJECT_PATH, "llm_judge_evaluations"),
    "comparisons": os.path.join(BASE_PROJECT_PATH, "llm_judge_comparisons"),
    "logs": os.path.join(BASE_PROJECT_PATH, "logs"),
}
