"""
Pipeline Pattern Implementation for CTI Preprocessing

This module provides the core pipeline architecture with abstract processing steps
and a flexible pipeline orchestrator.
"""

from typing import List, Dict, Any, Optional
import time

from .base import ProcessingStep, PipelineResult, PipelineException


class Pipeline:
    """
    Main pipeline orchestrator that executes processing steps in sequence
    """
    
    def __init__(self, name: str = "CTI_Pipeline"):
        self.name = name
        self.steps: List[ProcessingStep] = []
        self.context: Dict[str, Any] = {}
    
    def add_step(self, step: ProcessingStep) -> 'Pipeline':
        """
        Add a processing step to the pipeline
        
        Args:
            step: ProcessingStep instance to add
            
        Returns:
            Self for method chaining
        """
        self.steps.append(step)
        return self
    
    def remove_step(self, step_name: str) -> bool:
        """
        Remove a processing step by name
        
        Args:
            step_name: Name of the step to remove
            
        Returns:
            True if step was found and removed, False otherwise
        """
        for i, step in enumerate(self.steps):
            if step.name == step_name:
                removed_step = self.steps.pop(i)
                return True
        return False
    
    def get_step_names(self) -> List[str]:
        """Get list of all step names in order"""
        return [step.name for step in self.steps]
    
    def clear_context(self):
        """Clear the pipeline context"""
        self.context.clear()
    
    def set_context(self, key: str, value: Any):
        """Set a value in the pipeline context"""
        self.context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a value from the pipeline context"""
        return self.context.get(key, default)
    
    def process(self, input_data: str) -> PipelineResult:
        """
        Execute the pipeline on input data
        
        Args:
            input_data: Data to process through the pipeline
            
        Returns:
            PipelineResult with processing information
        """
        start_time = time.time()
        current_data = input_data
        applied_steps = []
        errors = []
        step_timings = {}
        
        # Reset context for this run
        self.context.clear()
        self.context['pipeline_name'] = self.name
        self.context['start_time'] = start_time
        
        for step in self.steps:
            step_start_time = time.time()
            
            try:
                # Validate input data for this step
                if not step.validate(current_data):
                    error_msg = f"Validation failed for step '{step.name}'"
                    errors.append(error_msg)
                    continue
                
                # Process the data
                processed_data = step.process(current_data, self.context)
                
                # Update current data for next step
                current_data = processed_data
                applied_steps.append(step.name)
                
                # Record timing
                step_duration = time.time() - step_start_time
                step_timings[step.name] = step_duration
                
            except Exception as e:
                error_msg = f"Error in step '{step.name}': {str(e)}"
                errors.append(error_msg)
                
                # Record timing even for failed steps
                step_duration = time.time() - step_start_time
                step_timings[step.name] = step_duration
                
                # Continue with next step using the last successful data
                continue
        
        total_time = time.time() - start_time
        success = len(errors) == 0
        
        return PipelineResult(
            input_data=input_data,
            output_data=current_data,
            applied_steps=applied_steps,
            errors=errors,
            step_timings=step_timings,
            context=self.context.copy(),
            total_processing_time=total_time,
            success=success
        )
    
    def __len__(self) -> int:
        """Return number of steps in pipeline"""
        return len(self.steps)
    
    def __str__(self) -> str:
        """String representation of pipeline"""
        return f"Pipeline('{self.name}', {len(self.steps)} steps: {self.get_step_names()})"
    
    def __repr__(self) -> str:
        """Detailed representation of pipeline"""
        return self.__str__()
