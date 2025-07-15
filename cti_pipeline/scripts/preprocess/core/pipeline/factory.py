"""
Factory Pattern Implementation for CTI Preprocessing Components

This module provides factories for creating pipeline components and steps
with proper dependency injection and configuration management.
"""

from typing import Dict, Type, Any, Optional
from .base import ProcessingStep
from .pipeline import Pipeline

# Try to import configuration and processors with fallbacks
try:
    from .config import PipelineConfig, StepConfig
except ImportError:
    # Fallback for when config module is not available
    PipelineConfig = None
    StepConfig = None

try:
    from ..processors.extraction.extraction import TextExtractor
except ImportError:
    TextExtractor = None

try:
    from ..processors.cleaning.cleaning import TextCleaner
except ImportError:
    TextCleaner = None

try:
    from ..processors.cleaning.normalization import TextNormalizer
except ImportError:
    TextNormalizer = None

# try:
#     from ..processors.anonymization.anonymizer import TextAnonymizer
# except ImportError:
#     TextAnonymizer = None


class ExtractionStep(ProcessingStep):
    """Processing step wrapper for text extraction"""
    
    def __init__(self, extractor: Any):
        self.extractor = extractor
    
    def process(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Extract text from file"""
        if self.extractor is None:
            raise Exception("TextExtractor not available")
            
        result = self.extractor.extract_from_file(file_path)
        
        if context is not None:
            context['extraction_result'] = result
            context['file_format'] = result.file_format
            context['extraction_metadata'] = result.metadata
        
        if not result.success:
            raise Exception(f"Text extraction failed: {result.error_message}")
        
        return result.text
    
    def validate(self, input_data: str) -> bool:
        """Validate that input is a valid file path"""
        try:
            from pathlib import Path
            
            # If input_data looks like extracted text (too long), skip validation
            if len(input_data) > 1000 or '\n' in input_data[:100]:
                return True  # This is already extracted text, validation passed
            
            # Check if it's a valid file path
            path = Path(input_data)
            if not path.exists():
                return False
            
            if self.extractor and hasattr(self.extractor, 'get_supported_formats'):
                supported_formats = self.extractor.get_supported_formats()
                return path.suffix.lower() in supported_formats
            return True
        except Exception:
            # If any error occurs, assume it's already processed text
            return True
    
    @property
    def name(self) -> str:
        return "extraction"
    
    @property
    def description(self) -> str:
        return "Extract text from various file formats (PDF, HTML, JSON, CSV, TXT)"


class CleaningStep(ProcessingStep):
    """Processing step wrapper for text cleaning"""
    
    def __init__(self, cleaner: Any):
        self.cleaner = cleaner
    
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Clean text content"""
        if self.cleaner is None:
            raise Exception("TextCleaner not available")
            
        cleaned_text = self.cleaner.clean(text)
        
        if context is not None:
            context['cleaning_stats'] = {
                'original_length': len(text),
                'cleaned_length': len(cleaned_text),
                'reduction_percentage': ((len(text) - len(cleaned_text)) / len(text) * 100) if len(text) > 0 else 0
            }
        
        return cleaned_text
    
    def validate(self, text: str) -> bool:
        """Validate that input is a non-empty string"""
        return isinstance(text, str) and len(text.strip()) > 0
    
    @property
    def name(self) -> str:
        return "cleaning"
    
    @property
    def description(self) -> str:
        return "Remove HTML, boilerplate text, ads, and clean OCR artifacts"


class NormalizationStep(ProcessingStep):
    """Processing step wrapper for text normalization"""
    
    def __init__(self, normalizer: Any):
        self.normalizer = normalizer
    
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Normalize text content"""
        if self.normalizer is None:
            raise Exception("TextNormalizer not available")
            
        normalized_text = self.normalizer.normalize(text)
        
        if context is not None:
            context['normalization_stats'] = {
                'original_length': len(text),
                'normalized_length': len(normalized_text)
            }
        
        return normalized_text
    
    def validate(self, text: str) -> bool:
        """Validate that input is a non-empty string"""
        return isinstance(text, str) and len(text.strip()) > 0
    
    @property
    def name(self) -> str:
        return "normalization"
    
    @property
    def description(self) -> str:
        return "Standardize encoding, dates, punctuation, and format IoCs"


# class AnonymizationStep(ProcessingStep):
#     """Processing step wrapper for text anonymization"""
    
#     def __init__(self, anonymizer: Any):
#         self.anonymizer = anonymizer
    
#     def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
#         """Anonymize sensitive data in text"""
#         if self.anonymizer is None:
#             raise Exception("TextAnonymizer not available")
            
#         anonymized_text = self.anonymizer.anonymize(text)
        
#         if context is not None:
#             context['anonymization_stats'] = {
#                 'original_length': len(text),
#                 'anonymized_length': len(anonymized_text)
#             }
        
#         return anonymized_text
    
#     def validate(self, text: str) -> bool:
#         """Validate that input is a non-empty string"""
#         return isinstance(text, str) and len(text.strip()) > 0
    
#     @property
#     def name(self) -> str:
#         return "anonymization"
    
#     @property
#     def description(self) -> str:
#         return "Mask sensitive data while preserving technical terms and IoCs"


class ComponentFactory:
    """Factory for creating pipeline components with configuration"""
    
    # Registry of available processing steps
    _step_registry: Dict[str, Type[ProcessingStep]] = {
        'extraction': ExtractionStep,
        'cleaning': CleaningStep,
        'normalization': NormalizationStep,
        # 'anonymization': AnonymizationStep
    }
    
    # Registry of core components
    _component_registry: Dict[str, Type] = {
        'text_extractor': TextExtractor,
        'text_cleaner': TextCleaner,
        'text_normalizer': TextNormalizer,
        # 'text_anonymizer': TextAnonymizer
    }
    
    @classmethod
    def register_step(cls, name: str, step_class: Type[ProcessingStep]):
        """Register a new processing step type"""
        cls._step_registry[name] = step_class
    
    @classmethod
    def register_component(cls, name: str, component_class: Type):
        """Register a new component type"""
        cls._component_registry[name] = component_class
    
    @classmethod
    def create_component(cls, component_name: str, config: Dict[str, Any] = None) -> Any:
        """
        Create a component instance with configuration
        
        Args:
            component_name: Name of the component to create
            config: Configuration dictionary for the component
            
        Returns:
            Configured component instance
        """
        if component_name not in cls._component_registry:
            raise ValueError(f"Unknown component: {component_name}. Available: {list(cls._component_registry.keys())}")
        
        component_class = cls._component_registry[component_name]
        config = config or {}
        return component_class()
        # try:
        #     # Handle special cases for component creation
        #     if component_name == 'text_anonymizer':
        #         from ..processors.anonymization.config import AnonymizationConfig
        #         # Map config parameters to AnonymizationConfig format
        #         anon_config = AnonymizationConfig(**config)
        #         return component_class(anon_config)
        #     else:
        #         # Most components don't take constructor parameters
        #         return component_class()
        # except Exception as e:
        #     raise
    
    @classmethod
    def create_step(cls, step_name: str, step_config: Any) -> ProcessingStep:
        """
        Create a processing step with configuration
        
        Args:
            step_name: Name of the processing step
            step_config: Configuration for the step
            
        Returns:
            Configured processing step instance
        """
        if step_name not in cls._step_registry:
            raise ValueError(f"Unknown step: {step_name}. Available: {list(cls._step_registry.keys())}")
        
        step_class = cls._step_registry[step_name]
        
        # Map step names to component names
        component_mapping = {
            'extraction': 'text_extractor',
            'cleaning': 'text_cleaner',
            'normalization': 'text_normalizer',
            # 'anonymization': 'text_anonymizer'
        }
        
        component_name = component_mapping.get(step_name)
        if not component_name:
            raise ValueError(f"No component mapping for step: {step_name}")
        
        # Create the underlying component
        try:
            component = cls.create_component(component_name, step_config.parameters if hasattr(step_config, 'parameters') else {})
        except Exception as e:
            # Create a default component without parameters for robustness
            component = cls.create_component(component_name, {})
        
        # Create and return the step wrapper
        return step_class(component)
    
    @classmethod
    def create_pipeline(cls, config: Any) -> Pipeline:
        """
        Create a complete pipeline from configuration
        
        Args:
            config: Pipeline configuration
            
        Returns:
            Configured pipeline with all enabled steps
        """
        pipeline_name = config.name if hasattr(config, 'name') else "Default_Pipeline"
        pipeline = Pipeline(pipeline_name)
        
        if not hasattr(config, 'extraction'):
            return pipeline
        
        # Get enabled steps in priority order
        step_configs = [
            ('extraction', config.extraction),
            ('cleaning', config.cleaning),
            ('normalization', config.normalization),
            # ('anonymization', config.anonymization)
        ]
        
        # Filter enabled steps and sort by priority
        enabled_steps = [(name, cfg) for name, cfg in step_configs if hasattr(cfg, 'enabled') and cfg.enabled]
        enabled_steps.sort(key=lambda x: x[1].priority if hasattr(x[1], 'priority') else 0)
        
        # Create and add steps to pipeline
        for step_name, step_config in enabled_steps:
            try:
                step = cls.create_step(step_name, step_config)
                pipeline.add_step(step)
            except Exception as e:
                retry_attempts = step_config.retry_attempts if hasattr(step_config, 'retry_attempts') else 0
                if retry_attempts > 0:
                    print(f"[Factory] Step '{step_name}' will be retried if it fails during processing")
        
        return pipeline
    
    @classmethod
    def get_available_steps(cls) -> list:
        """Get list of available step types"""
        return list(cls._step_registry.keys())
    
    @classmethod
    def get_available_components(cls) -> list:
        """Get list of available component types"""
        return list(cls._component_registry.keys())


class PipelineFactory:
    """High-level factory for creating common pipeline configurations"""
    
    @staticmethod
    def create_minimal_pipeline() -> Pipeline:
        """Create pipeline for minimal processing (extraction + cleaning only)"""
        from .config import create_minimal_config
        config = create_minimal_config()
        return ComponentFactory.create_pipeline(config)
    
    @staticmethod
    def create_standard_pipeline() -> Pipeline:
        """Create pipeline for standard processing (extraction + cleaning + normalization)"""
        from .config import create_standard_config
        config = create_standard_config()
        return ComponentFactory.create_pipeline(config)
    
    @staticmethod
    def create_full_pipeline() -> Pipeline:
        """Create pipeline for full processing (all steps)"""
        from .config import create_full_config
        config = create_full_config()
        return ComponentFactory.create_pipeline(config)
    
    # @staticmethod
    # def create_cti_pipeline(anonymize: bool = False) -> Pipeline:
    #     """Create CTI-optimized pipeline"""
    #     from ..utils.config import create_cti_config
    #     config = create_cti_config(anonymize=anonymize)
    #     return ComponentFactory.create_pipeline(config)

    @staticmethod
    def create_cti_pipeline() -> Pipeline:
        """
        Create CTI-optimized pipeline.
        """
        from .config import create_cti_config
        config = create_cti_config()
        return ComponentFactory.create_pipeline(config)
    
    @staticmethod
    def create_custom_pipeline(
        steps: list, 
        name: str = "Custom_Pipeline",
        **step_configs
    ) -> Pipeline:
        """
        Create a custom pipeline with specified steps
        
        Args:
            steps: List of step names to include
            name: Name for the pipeline
            **step_configs: Keyword arguments for step configurations
            
        Returns:
            Configured custom pipeline
        """
        from .config import PipelineConfig, StepConfig
        
        config = PipelineConfig(name=name)
        
        # Disable all steps first
        config.extraction.enabled = False
        config.cleaning.enabled = False
        config.normalization.enabled = False
        # config.anonymization.enabled = False
        
        # Enable only specified steps
        step_priority = 10
        for step_name in steps:
            step_config = config.get_step_config(step_name)
            if step_config:
                step_config.enabled = True
                step_config.priority = step_priority
                step_priority += 10
                
                # Apply custom configuration if provided
                if step_name in step_configs:
                    step_config.parameters.update(step_configs[step_name])
        
        return ComponentFactory.create_pipeline(config)
