import os
from pathlib import Path

# Get the actual project root dynamically
BASE_PROJECT_PATH = str(Path(__file__).parent.parent.parent)

VALIDATION_CONFIG = {
    "model": "gemini-1.5-flash",  # Fixed consistency
    "temperature": 0.1,
    "max_tokens": 800,
    "max_retries": 3,
    "validation_threshold": 0.7,
}

PATH_CONFIG = {
    "judge_results": os.path.join(BASE_PROJECT_PATH, "judge_techniques"),
    "judge_logs": os.path.join(BASE_PROJECT_PATH, "judge_logs"),
    "logs": os.path.join(BASE_PROJECT_PATH, "logs"),
}
