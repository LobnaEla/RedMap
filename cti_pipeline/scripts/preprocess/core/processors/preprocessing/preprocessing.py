"""
Enhanced CTI Preprocessing Pipeline with Clean Architecture

This module provides the main CTI preprocessing coordinator with improved
architecture, error handling, metrics, and configuration management.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import time

from ...pipeline import Pipeline
from ...pipeline import ComponentFactory
from ...pipeline.config import PipelineConfig, ConfigManager, ProcessingLevel
from ...utils.error_handling import ProcessingError, ErrorSeverity, ErrorCategory
from ...utils.metrics import PipelineMetrics, MetricsCollector
from ..extraction.extraction import TextExtractor, ExtractionResult

@dataclass
class PreprocessingResult:
    """Enhanced result of preprocessing operation with architecture improvements"""
    original_text: str
    processed_text: str
    statistics: Dict[str, Any]
    steps_applied: List[str]
    errors: List[ProcessingError]  # Changed from List[str] to List[ProcessingError]
    extraction_result: Optional[ExtractionResult] = None
    pipeline_metrics: Optional[Dict[str, Any]] = None
    processing_time: float = 0.0
    success: bool = True
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    @property
    def has_critical_errors(self) -> bool:
        """Check if there are critical errors"""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by severity"""
        summary = {}
        for error in self.errors:
            severity = error.severity.value
            summary[severity] = summary.get(severity, 0) + 1
        return summary


class CTIPreprocessor:
    """
    Enhanced CTI preprocessing pipeline with clean architecture
    
    This class provides the main interface for CTI document preprocessing
    with improved error handling, metrics collection, and configuration management.
    """
    
    def __init__(
        self, 
        config: Optional[PipelineConfig] = None,
        config_path: Optional[str] = None
    ):
        # Configuration management
        self.config_manager = ConfigManager(config_path)
        self.config = config or self.config_manager.config
        
        # Core architecture components
        self.factory = ComponentFactory()
        self.pipeline: Optional[Pipeline] = None
        self.metrics = PipelineMetrics(self.config.name)
        self.metrics_collector = MetricsCollector(self.metrics)
        
        # Initialize extractor for file processing
        self.extractor = TextExtractor()
        
        # Build pipeline
        self._build_pipeline()
        
        print(f"[Preprocessing] Initialized CTI Preprocessor: {self.config.name}")
    
    def _build_pipeline(self):
        """Build the processing pipeline from configuration"""
        try:
            self.pipeline = self.factory.create_pipeline(self.config)
            print(f"[Preprocessing] Built pipeline with {len(self.pipeline)} steps: {self.pipeline.get_step_names()}")
        except Exception as e:
            error = ProcessingError(
                step="pipeline_initialization",
                message=f"Failed to build pipeline: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.CONFIGURATION,
                exception=e
            )
            print("[Preprocessing] ",error)
            raise
    
    def rebuild_pipeline(self, new_config: Optional[PipelineConfig] = None):
        """Rebuild pipeline with new configuration"""
        if new_config:
            self.config = new_config
        self._build_pipeline()
        print("[Preprocessing] Pipeline rebuilt with new configuration")
    
    def process(self, text: str) -> PreprocessingResult:
        """
        Process text through the preprocessing pipeline
        
        Args:
            text: Input text to process
            
        Returns:
            PreprocessingResult with detailed processing information
        """
        start_time = time.time()
        original_text = text
        
        print(f"[Preprocessing] Starting text processing (length: {len(text)})")
        
        try:
            # Validate input
            if not text or not text.strip():
                error = ProcessingError(
                    step="input_validation",
                    message="Empty or whitespace-only text provided",
                    severity=ErrorSeverity.MEDIUM,
                    category=ErrorCategory.VALIDATION
                )
                print("[Preprocessing] ",error)
                
                return PreprocessingResult(
                    original_text=original_text,
                    processed_text="",
                    statistics=self._calculate_stats(original_text, ""),
                    steps_applied=[],
                    errors=[error],
                    processing_time=0.0,
                    success=False
                )
            
            # Execute pipeline
            if not self.pipeline:
                raise Exception("Pipeline not initialized")
            
            pipeline_result = self.pipeline.process(text)
            processing_time = time.time() - start_time
            
            # Convert pipeline errors to ProcessingError objects
            errors = []
            for error_msg in pipeline_result.errors:
                error = ProcessingError(
                    step="pipeline",
                    message=error_msg,
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.PROCESSING
                )
                errors.append(error)
                print("[Preprocessing] ",error)
            
            # Calculate statistics
            stats = self._calculate_stats(original_text, pipeline_result.output_data)
            
            # Record metrics
            self.metrics.add_document_processed(processing_time)
            
            # Create result
            result = PreprocessingResult(
                original_text=original_text,
                processed_text=pipeline_result.output_data,
                statistics=stats,
                steps_applied=pipeline_result.applied_steps,
                errors=errors,
                pipeline_metrics=self.metrics.get_summary(),
                processing_time=processing_time,
                success=pipeline_result.success and not errors
            )
            
            print(f"[Preprocessing] Text processing completed in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error = ProcessingError(
                step="pipeline_execution",
                message=f"Pipeline execution failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                exception=e
            )
            
            print("[Preprocessing] ",error)
            
            return PreprocessingResult(
                original_text=original_text,
                processed_text=original_text,  # Return original on error
                statistics=self._calculate_stats(original_text, original_text),
                steps_applied=[],
                errors=[error],
                processing_time=processing_time,
                success=False
            )
    
    def process_file(self, file_path: str) -> PreprocessingResult:
        """
        Process a file through the complete extraction and preprocessing pipeline
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            PreprocessingResult with extraction metadata and processed text
        """
        start_time = time.time()
        print(f"[Preprocessing] Processing file: {file_path}")
        
        try:
            # Step 1: Extract text from file
            extraction_result = self.extractor.extract_from_file(file_path)
            
            if not extraction_result.success:
                error = ProcessingError(
                    step="file_extraction",
                    message=f"Text extraction failed: {extraction_result.error_message}",
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.EXTRACTION
                )
                
                return PreprocessingResult(
                    original_text="",
                    processed_text="",
                    statistics=self._calculate_stats("", ""),
                    steps_applied=[],
                    errors=[error],
                    extraction_result=extraction_result,
                    processing_time=time.time() - start_time,
                    success=False
                )
            
            # Step 2: Process the extracted text
            processing_result = self.process(extraction_result.text)
            
            # Add extraction metadata to the result
            processing_result.extraction_result = extraction_result
            
            # Update statistics with extraction info
            if extraction_result.metadata:
                processing_result.statistics.update({
                    'file_path': file_path,
                    'file_format': extraction_result.file_format,
                    'file_size': extraction_result.metadata.get('file_size', 0),
                    'extraction_success': True
                })
            
            # Record file processing metrics
            total_time = time.time() - start_time
            self.metrics_collector.record_file_processing(file_path, total_time)
            processing_result.processing_time = total_time
            
            print(f"[Preprocessing] File processing completed: {file_path}")
            return processing_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error = ProcessingError(
                step="file_processing",
                message=f"File processing failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                exception=e
            )
            
            return PreprocessingResult(
                original_text="",
                processed_text="",
                statistics=self._calculate_stats("", ""),
                steps_applied=[],
                errors=[error],
                processing_time=processing_time,
                success=False
            )
    
    def _calculate_stats(self, original: str, processed: str) -> Dict[str, Any]:
        """Calculate processing statistics"""
        original_length = len(original)
        processed_length = len(processed)
        
        reduction = ((original_length - processed_length) / original_length * 100) if original_length > 0 else 0
        
        return {
            'original_length': original_length,
            'processed_length': processed_length,
            'reduction_percentage': round(reduction, 2),
            'character_reduction': original_length - processed_length
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline metrics"""
        return self.metrics.get_summary()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get pipeline health status"""
        return self.metrics.get_health_status()
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.reset()
        print("[Preprocessing] Metrics reset")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        return self.error_handler.get_error_summary()
    
    def reload_config(self, config_path: Optional[str] = None):
        """Reload configuration and rebuild pipeline"""
        if config_path:
            self.config_manager.config_path = config_path
        
        self.config = self.config_manager.reload_config()
        self._build_pipeline()
        print("[Preprocessing] Configuration reloaded and pipeline rebuilt")


# Convenience functions for backward compatibility and quick usage
def preprocess_text(text: str, level: ProcessingLevel = ProcessingLevel.STANDARD) -> str:
    """Quick text preprocessing function"""
    from ...pipeline.config import PipelineConfig
    config = PipelineConfig(level=level)
    preprocessor = CTIPreprocessor(config=config)
    result = preprocessor.process(text)
    return result.processed_text


def preprocess_cti_text(text: str, anonymize: bool = False) -> str:
    """Preprocess CTI text with optimal settings"""
    from ...pipeline.config import create_cti_config
    config = create_cti_config(anonymize=anonymize)
    preprocessor = CTIPreprocessor(config=config)
    result = preprocessor.process(text)
    return result.processed_text


def preprocess_file(file_path: str, level: ProcessingLevel = ProcessingLevel.STANDARD) -> str:
    """
    Quick file preprocessing function that extracts text and processes it
    
    Args:
        file_path: Path to the file to process
        level: Preprocessing level to apply
        
    Returns:
        Processed text content
    """
    from ...pipeline.config import PipelineConfig
    config = PipelineConfig(level=level)
    preprocessor = CTIPreprocessor(config=config)
    result = preprocessor.process_file(file_path)
    return result.processed_text


def preprocess_cti_file(file_path: str, anonymize: bool = False) -> str:
    """
    Preprocess CTI file with optimal settings
    
    Args:
        file_path: Path to the CTI file to process
        anonymize: Whether to apply anonymization
        
    Returns:
        Processed text content
    """
    from ...pipeline.config import create_cti_config
    config = create_cti_config(anonymize=anonymize)
    preprocessor = CTIPreprocessor(config=config)
    result = preprocessor.process_file(file_path)
    return result.processed_text


def process_file_with_result(file_path: str, level: ProcessingLevel = ProcessingLevel.STANDARD) -> PreprocessingResult:
    """
    Process file and return detailed result with extraction metadata
    
    Args:
        file_path: Path to the file to process
        level: Preprocessing level to apply
        
    Returns:
        Complete PreprocessingResult with extraction metadata
    """
    from ...pipeline.config import PipelineConfig
    config = PipelineConfig(level=level)
    preprocessor = CTIPreprocessor(config=config)
    return preprocessor.process_file(file_path)


# Factory functions for creating preprocessors with common configurations
def create_minimal_preprocessor() -> CTIPreprocessor:
    """Create preprocessor for minimal processing"""
    from ...pipeline.config import create_minimal_config
    config = create_minimal_config()
    return CTIPreprocessor(config=config)


def create_standard_preprocessor() -> CTIPreprocessor:
    """Create preprocessor for standard processing"""
    from ...pipeline.config import create_standard_config
    config = create_standard_config()
    return CTIPreprocessor(config=config)


def create_full_preprocessor() -> CTIPreprocessor:
    """Create preprocessor for full processing with anonymization"""
    from ...pipeline.config import create_full_config
    config = create_full_config()
    return CTIPreprocessor(config=config)


def create_cti_preprocessor(anonymize: bool = False) -> CTIPreprocessor:
    """Create CTI-optimized preprocessor"""
    from ...pipeline.config import create_cti_config
    config = create_cti_config(anonymize=anonymize)
    return CTIPreprocessor(config=config)


# Additional convenience function
def quick_preprocess(file_path: str, anonymize: bool = False) -> str:
    """Ultra-quick function to process a file and return text"""
    preprocessor = create_cti_preprocessor(anonymize=anonymize)
    result = preprocessor.process_file(file_path)
    return result.processed_text
