"""
LLM-as-a-Judge: Cross-Validation Framework for MITRE ATT&CK TTP Mapping
"""

from .core.judge_client import JudgeClient
from .core.technique_validator import TechniqueValidator
from .utils.file_utils import save_judge_results, save_final_techniques_only
from .utils.validation_utils import calculate_validation_metrics

__version__ = "1.0.0"
__all__ = [
    "JudgeClient",
    "TechniqueValidator",
    "save_judge_results",
    "save_final_techniques_only",
    "calculate_validation_metrics",
]
