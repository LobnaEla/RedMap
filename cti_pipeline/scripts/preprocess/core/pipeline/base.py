"""
Abstract Base Classes for CTI Preprocessing Pipeline

This module provides the core abstract classes and interfaces for the
preprocessing pipeline system.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


class ProcessingStep(ABC):
    """Abstract base class for processing steps"""
    
    @abstractmethod
    def process(self, data: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process the input data and return processed result
        """
        pass
    
    @abstractmethod
    def validate(self, data: str) -> bool:
        """
        Validate if the input data is suitable for this processing step
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this processing step"""
        pass
    
    @property
    def description(self) -> str:
        """Return a description of what this step does"""
        return f"Processing step: {self.name}"


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    input_data: str
    output_data: str
    applied_steps: List[str]
    errors: List[str]
    step_timings: Dict[str, float]
    context: Dict[str, Any]
    total_processing_time: float
    success: bool = True
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def get_step_timing(self, step_name: str) -> float:
        """Get timing for a specific step"""
        return self.step_timings.get(step_name, 0.0)


class PipelineException(Exception):
    """Base exception for pipeline-related errors"""
    pass


class ProcessingStepException(PipelineException):
    """Exception raised by processing steps"""
    pass


class ValidationException(PipelineException):
    """Exception raised during validation"""
    pass


class ConfigurationException(PipelineException):
    """Exception raised for configuration errors"""
    pass
