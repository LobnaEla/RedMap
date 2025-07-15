"""
CTI Preprocessing Pipeline - Clean Architecture

This package provides a clean, extensible architecture for CTI document preprocessing
with comprehensive error handling, metrics collection, and configuration management.

Main Components:
- TextExtractor: Extract text from various file formats (PDF, HTML, JSON, CSV, TXT)
- Pipeline: Flexible step-by-step processing framework
- CTIPreprocessor: Main preprocessing coordinator with clean architecture
- ComponentFactory: Create and configure pipeline components
- ErrorHandler: Structured error handling and recovery
- PipelineMetrics: Comprehensive metrics and monitoring

Usage Examples:

    # Quick usage for files
    from cti_preprocessing.core import preprocess_cti_file
    processed_text = preprocess_cti_file("threat_report.pdf", anonymize=True)
    
    # Detailed usage with configuration
    from cti_preprocessing.core import CTIPreprocessor, create_cti_config
    config = create_cti_config(anonymize=True)
    preprocessor = CTIPreprocessor(config=config)
    result = preprocessor.process_file("document.pdf")
    
    # Factory-based creation
    from cti_preprocessing.core import PipelineFactory
    pipeline = PipelineFactory.create_cti_pipeline(anonymize=True)
    
    # Custom pipeline
    from cti_preprocessing.core import ComponentFactory, PipelineConfig
    config = PipelineConfig()
    pipeline = ComponentFactory.create_pipeline(config)
"""

from typing import Dict, Any
from pathlib import Path

# Core architecture components
from .pipeline import Pipeline, ProcessingStep, PipelineResult
from .pipeline import ComponentFactory, PipelineFactory
from .pipeline.config import (
    PipelineConfig, ConfigManager, ProcessingLevel,
    StepConfig, ExtractionConfig, CleaningConfig, 
    NormalizationConfig,
    #   AnonymizationConfig,
    create_minimal_config, create_standard_config, 
    create_full_config, create_cti_config
)
from .utils.error_handling import (
    ErrorHandler, ProcessingError, ErrorSeverity, ErrorCategory,
    RetryStrategy, create_error, handle_exceptions
)
from .utils.metrics import PipelineMetrics, MetricsCollector, StepMetrics, StepTimer

# Main preprocessing components
from .processors.preprocessing import CTIPreprocessor, PreprocessingResult
from .processors.extraction import TextExtractor, ExtractionResult, extract_text_from_file, extract_with_result

# Individual processing components (for advanced usage)
from .processors.cleaning import TextCleaner, clean_text
from .processors.cleaning import TextNormalizer, normalize_text
# from .processors.anonymization import TextAnonymizer, anonymize_text, anonymize_cti_text

# Convenience functions for quick usage
from .processors.preprocessing import (
    preprocess_text, preprocess_cti_text,
    preprocess_file, preprocess_cti_file, 
    process_file_with_result,
    create_minimal_preprocessor, create_standard_preprocessor,
    create_full_preprocessor, create_cti_preprocessor
)

# Backward compatibility aliases
extract_text_from_file = extract_text_from_file
preprocess_text = preprocess_text
preprocess_file = preprocess_file

__version__ = "2.0.0"

__all__ = [
    # Core architecture
    'Pipeline', 'ProcessingStep', 'PipelineResult',
    'ComponentFactory', 'PipelineFactory',
    
    # Configuration
    'PipelineConfig', 'ConfigManager', 'ProcessingLevel',
    'StepConfig', 'ExtractionConfig', 'CleaningConfig', 
    'NormalizationConfig', 
    # 'AnonymizationConfig',
    'create_minimal_config', 'create_standard_config', 
    'create_full_config', 'create_cti_config',
    
    # Error handling
    'ErrorHandler', 'ProcessingError', 'ErrorSeverity', 'ErrorCategory',
    'RetryStrategy', 'create_error', 'handle_exceptions',
    
    # Metrics and monitoring
    'PipelineMetrics', 'MetricsCollector', 'StepMetrics', 'StepTimer',
    
    # Main preprocessing
    'CTIPreprocessor', 'PreprocessingResult',
    
    # Extraction
    'TextExtractor', 'ExtractionResult', 'extract_text_from_file', 'extract_with_result',
    
    # Individual components
    'TextCleaner', 'TextNormalizer', # 'TextAnonymizer',
    
    # Convenience functions
    'clean_text', 'normalize_text', # 'anonymize_text', 'anonymize_cti_text',
    'preprocess_text', 'preprocess_cti_text',
    'preprocess_file', 'preprocess_cti_file', 'process_file_with_result',
    
    # Factory functions
    'create_minimal_preprocessor', 'create_standard_preprocessor',
    'create_full_preprocessor', 'create_cti_preprocessor'
]


# Module-level convenience functions for even easier usage
def quick_preprocess(text_or_file: str, anonymize: bool = False) -> str:
    """
    Ultra-quick preprocessing - automatically detects if input is text or file path
    
    Args:
        text_or_file: Either text content or path to a file
        anonymize: Whether to apply anonymization
        
    Returns:
        Processed text
    """
    from pathlib import Path
    
    # Check if input is a file path
    if len(text_or_file) < 500 and Path(text_or_file).exists():
        return preprocess_cti_file(text_or_file, anonymize=anonymize)
    else:
        return preprocess_cti_text(text_or_file, anonymize=anonymize)


def create_pipeline_from_file(config_file: str) -> CTIPreprocessor:
    """
    Create a preprocessor from a configuration file
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        Configured CTIPreprocessor
    """
    return CTIPreprocessor(config_path=config_file)


def benchmark_pipeline(test_data: str, iterations: int = 10) -> Dict[str, Any]:
    """
    Benchmark pipeline performance
    
    Args:
        test_data: Test text or file path
        iterations: Number of iterations to run
        
    Returns:
        Performance benchmarks
    """
    import time
    import statistics
    
    preprocessor = create_cti_preprocessor()
    times = []
    
    for _ in range(iterations):
        start = time.time()
        if Path(test_data).exists():
            preprocessor.process_file(test_data)
        else:
            preprocessor.process(test_data)
        times.append(time.time() - start)
    
    return {
        'iterations': iterations,
        'average_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
        'total_time': sum(times)
    }


# Add convenience functions to __all__
__all__.extend(['quick_preprocess', 'create_pipeline_from_file', 'benchmark_pipeline'])
