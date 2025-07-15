"""
Configuration Management for CTI Preprocessing Pipeline

This module provides configuration classes and management utilities
for the preprocessing pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from pathlib import Path
import json
from pathlib import Path

# Default configuration path - reference the main config directory
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.json"


class ProcessingLevel(Enum):
    """Different levels of processing intensity"""
    MINIMAL = "minimal"      # Basic cleaning only
    STANDARD = "standard"    # Cleaning + normalization  
    FULL = "full"           # All steps (extraction, cleaning, normalization)


@dataclass
class StepConfig:
    """Configuration for individual processing steps"""
    enabled: bool = True
    priority: int = 100
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 0
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value with default fallback"""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any):
        """Set a parameter value"""
        self.parameters[key] = value


@dataclass
class ExtractionConfig(StepConfig):
    """Configuration for text extraction step"""
    max_file_size: int = 100_000_000  # 100MB
    supported_formats: List[str] = field(default_factory=lambda: ['.pdf', '.txt', '.html', '.json', '.csv'])
    encoding_fallbacks: List[str] = field(default_factory=lambda: ['utf-8', 'latin1'])
    
    def __post_init__(self):
        # TextExtractor doesn't accept constructor parameters - it's self-contained
        self.parameters.update({})


@dataclass  
class CleaningConfig(StepConfig):
    """Configuration for text cleaning step"""
    remove_html: bool = True
    remove_boilerplate: bool = True
    remove_ads: bool = True
    fix_ocr_artifacts: bool = True
    min_line_length: int = 10
    remove_extra_whitespace: bool = True
    
    def __post_init__(self):
        # TextCleaner doesn't accept constructor parameters - it's self-contained
        self.parameters.update({})


@dataclass
class NormalizationConfig(StepConfig):
    """Configuration for text normalization step"""
    normalize_encoding: bool = True
    normalize_unicode: bool = True
    normalize_dates: bool = True
    normalize_punctuation: bool = True
    normalize_case: bool = False
    normalize_iocs: bool = True
    
    def __post_init__(self):
        # TextNormalizer doesn't accept constructor parameters - it's self-contained
        self.parameters.update({})


# @dataclass
# class AnonymizationConfig(StepConfig):
#     """Configuration for anonymization step"""
#     # Basic anonymization settings
#     anonymize_emails: bool = True
#     anonymize_phones: bool = True
#     anonymize_addresses: bool = True
#     anonymize_names: bool = True
#     anonymize_credit_cards: bool = True
#     anonymize_ssn: bool = True
#     
#     # Preservation settings
#     preserve_domain_in_email: bool = True
#     preserve_technical_terms: bool = True
#     preserve_iocs: bool = True
#     preserve_government_domains: bool = True
#     preserve_facility_names: bool = True
#     preserve_classification_levels: bool = True
#     preserve_agency_names: bool = True
#     
#     # Fine-tuning parameters
#     min_name_length: int = 3
#     max_name_length: int = 50
#     
#     def __post_init__(self):
#         # Create parameters compatible with anonymization.AnonymizationConfig
#         self.parameters.update({
#             'anonymize_emails': self.anonymize_emails,
#             'anonymize_phones': self.anonymize_phones,
#             'anonymize_addresses': self.anonymize_addresses,
#             'anonymize_names': self.anonymize_names,
#             'anonymize_credit_cards': self.anonymize_credit_cards,
#             'anonymize_ssn': self.anonymize_ssn,
#             'preserve_domain_in_email': self.preserve_domain_in_email,
#             'preserve_technical_terms': self.preserve_technical_terms,
#             'preserve_iocs': self.preserve_iocs,
#             'preserve_government_domains': self.preserve_government_domains,
#             'preserve_facility_names': self.preserve_facility_names,
#             'preserve_classification_levels': self.preserve_classification_levels,
#             'preserve_agency_names': self.preserve_agency_names,
#             'min_name_length': self.min_name_length,
#             'max_name_length': self.max_name_length,
#         })


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    name: str = "CTI_Preprocessing_Pipeline"
    version: str = "2.0.0"
    level: ProcessingLevel = ProcessingLevel.STANDARD
    
    # Step configurations
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    # anonymization: AnonymizationConfig = field(default_factory=AnonymizationConfig)
    
    # Global settings
    max_file_size: int = 100_000_000
    timeout_seconds: int = 300
    retry_attempts: int = 3
    output_format: str = "text"
    preserve_metadata: bool = True
    
    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    
    def get_enabled_steps(self) -> List[str]:
        """Get list of enabled step names in priority order"""
        steps = []
        step_configs = [
            ('extraction', self.extraction),
            ('cleaning', self.cleaning),
            ('normalization', self.normalization),
            # ('anonymization', self.anonymization)
        ]
        
        # Filter enabled and sort by priority
        enabled_steps = [(name, config) for name, config in step_configs if config.enabled]
        enabled_steps.sort(key=lambda x: x[1].priority)
        
        return [name for name, _ in enabled_steps]
    
    def get_step_config(self, step_name: str) -> Optional[StepConfig]:
        """Get configuration for a specific step"""
        step_configs = {
            'extraction': self.extraction,
            'cleaning': self.cleaning,
            'normalization': self.normalization,
            # 'anonymization': self.anonymization
        }
        return step_configs.get(step_name)
    
    def disable_step(self, step_name: str):
        """Disable a specific step"""
        config = self.get_step_config(step_name)
        if config:
            config.enabled = False
            print(f"[Pipeline Config] Disabled step: {step_name}")
    
    def enable_step(self, step_name: str):
        """Enable a specific step"""
        config = self.get_step_config(step_name)
        if config:
            config.enabled = True
            print(f"[Pipeline Config] Enabled step: {step_name}")
    
    def set_processing_level(self, level: ProcessingLevel):
        """Set the processing level and adjust step configuration accordingly"""
        self.level = level
        
        if level == ProcessingLevel.MINIMAL:
            # Only basic cleaning
            self.extraction.enabled = True
            self.cleaning.enabled = True
            self.normalization.enabled = False
            # self.anonymization.enabled = False
            
        elif level == ProcessingLevel.STANDARD:
            # Extraction, cleaning, and normalization
            self.extraction.enabled = True
            self.cleaning.enabled = True
            self.normalization.enabled = True
            # self.anonymization.enabled = False
            
        elif level == ProcessingLevel.FULL:
            # All steps enabled
            self.extraction.enabled = True
            self.cleaning.enabled = True
            self.normalization.enabled = True
            # self.anonymization.enabled = True
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PipelineConfig':
        """Create configuration from dictionary"""
        # Handle nested configurations
        extraction_config = ExtractionConfig(**config_dict.get('extraction', {}))
        cleaning_config = CleaningConfig(**config_dict.get('cleaning', {}))
        normalization_config = NormalizationConfig(**config_dict.get('normalization', {}))
        # anonymization_config = AnonymizationConfig(**config_dict.get('anonymization', {}))
        
        # Handle processing level
        level_str = config_dict.get('level', 'standard')
        level = ProcessingLevel(level_str) if isinstance(level_str, str) else level_str
        
        # Create main config
        main_config = {k: v for k, v in config_dict.items() 
                      if k not in ['extraction', 'cleaning', 'normalization', 'anonymization']}
        main_config['level'] = level
        
        return cls(
            extraction=extraction_config,
            cleaning=cleaning_config,
            normalization=normalization_config,
            # anonymization=anonymization_config,
            **main_config
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'level': self.level.value,
            'extraction': self.extraction.__dict__,
            'cleaning': self.cleaning.__dict__,
            'normalization': self.normalization.__dict__,
            # 'anonymization': self.anonymization.__dict__,
            'max_file_size': self.max_file_size,
            'timeout_seconds': self.timeout_seconds,
            'retry_attempts': self.retry_attempts,
            'output_format': self.output_format,
            'preserve_metadata': self.preserve_metadata,
            'log_level': self.log_level,
            'log_to_file': self.log_to_file,
            'log_file_path': self.log_file_path
        }


class ConfigManager:
    """Manages configuration loading, saving, and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        # Use default config path if none provided
        self.config_path = config_path or str(DEFAULT_CONFIG_PATH)
        self._config: Optional[PipelineConfig] = None
    
    @property
    def config(self) -> PipelineConfig:
        """Get the current configuration, loading if necessary"""
        if self._config is None:
            self._config = self._load_config()
        return self._config
    
    def _load_config(self) -> PipelineConfig:
        """Load configuration from file or create default"""
        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
                print(f"[Pipeline Config] Loaded configuration from: {self.config_path}")
                return PipelineConfig.from_dict(config_dict)
            except Exception as e:
                print("[Pipeline Config] Using default configuration")
        
        return PipelineConfig()  # Default configuration
    
    def save_config(self, config: Optional[PipelineConfig] = None):
        """Save configuration to file"""
        if not self.config_path:
            raise ValueError("No config path specified")
        
        config_to_save = config or self.config
        config_dict = config_to_save.to_dict()
        
        # Ensure directory exists
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        print(f"[Pipeline Config] Saved configuration to: {self.config_path}")
    
    def reload_config(self) -> PipelineConfig:
        """Reload configuration from file"""
        self._config = None
        return self.config
    
    def create_default_config_file(self, path: str):
        """Create a default configuration file"""
        default_config = PipelineConfig()
        old_path = self.config_path
        self.config_path = path
        
        try:
            self.save_config(default_config)
            print(f"[Pipeline Config] Created default configuration file: {path}")
        finally:
            self.config_path = old_path


# Convenience functions for quick configuration creation
def create_minimal_config() -> PipelineConfig:
    """Create configuration for minimal processing"""
    config = PipelineConfig()
    config.set_processing_level(ProcessingLevel.MINIMAL)
    return config


def create_standard_config() -> PipelineConfig:
    """Create configuration for standard processing"""
    config = PipelineConfig()
    config.set_processing_level(ProcessingLevel.STANDARD)
    return config


# def create_full_config() -> PipelineConfig:
#     """Create configuration for full processing with anonymization"""
#     config = PipelineConfig()
#     config.set_processing_level(ProcessingLevel.FULL)
#     return config

def create_full_config() -> PipelineConfig:
    """Create configuration for full processing (extraction, cleaning, normalization)"""
    config = PipelineConfig()
    config.set_processing_level(ProcessingLevel.FULL)
    return config


# def create_cti_config(anonymize: bool = False) -> PipelineConfig:
#     """Create CTI-specific configuration"""
#     config = PipelineConfig()
#     config.set_processing_level(ProcessingLevel.FULL if anonymize else ProcessingLevel.STANDARD)
#     
#     # CTI-specific settings
#     config.normalization.normalize_iocs = True
#     config.anonymization.preserve_iocs = True
#     config.anonymization.preserve_technical_terms = True
#     config.anonymization.preserve_government_domains = True
#     
#     return config

def create_cti_config(anonymize: bool = False) -> PipelineConfig:
    """Create CTI-specific configuration"""
    config = PipelineConfig()
    # Since anonymization is disabled, use STANDARD level regardless of anonymize parameter
    config.set_processing_level(ProcessingLevel.STANDARD)
    
    # CTI-specific settings
    config.normalization.normalize_iocs = True
    # Note: anonymization settings are commented out since anonymization is disabled
    # config.anonymization.preserve_iocs = True
    # config.anonymization.preserve_technical_terms = True
    # config.anonymization.preserve_government_domains = True
    
    return config
