"""
Enhanced Error Handling for CTI Preprocessing Pipeline

This module provides structured error handling, retry mechanisms,
and error recovery strategies.
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import time

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""
    EXTRACTION = "extraction"
    PROCESSING = "processing"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ProcessingError:
    """Structured error information"""
    step: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory = ErrorCategory.UNKNOWN
    exception: Optional[Exception] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    retry_count: int = 0
    resolved: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging/serialization"""
        return {
            'step': self.step,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'timestamp': self.timestamp.isoformat(),
            'retry_count': self.retry_count,
            'resolved': self.resolved,
            'context': self.context,
            'exception_type': type(self.exception).__name__ if self.exception else None,
            'exception_message': str(self.exception) if self.exception else None
        }
    
    def __str__(self) -> str:
        return f"[{self.severity.value.upper()}] {self.step}: {self.message}"


class RetryStrategy:
    """Configurable retry strategy"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        delay_seconds: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ):
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def should_retry(self, error: ProcessingError) -> bool:
        """Determine if an error should be retried"""
        # Don't retry critical errors or if max attempts reached
        if error.severity == ErrorSeverity.CRITICAL:
            return False
        
        if error.retry_count >= self.max_attempts:
            return False
        
        # Don't retry certain error categories
        if error.category in [ErrorCategory.CONFIGURATION, ErrorCategory.VALIDATION]:
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay before retry"""
        delay = self.delay_seconds * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def wait(self, attempt: int):
        """Wait before retrying"""
        delay = self.get_delay(attempt)
        time.sleep(delay)


class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(
        self,
        retry_strategy: Optional[RetryStrategy] = None
    ):
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.errors: List[ProcessingError] = []
        self.error_handlers: Dict[ErrorCategory, Callable] = {}
        self.recovery_strategies: Dict[str, Callable] = {}
    
    def register_error_handler(self, category: ErrorCategory, handler: Callable):
        """Register a custom error handler for a category"""
        self.error_handlers[category] = handler
        print(f"Registered error handler for category: {category.value}")
    
    def register_recovery_strategy(self, step_name: str, strategy: Callable):
        """Register a recovery strategy for a specific step"""
        self.recovery_strategies[step_name] = strategy
        print(f"Registered recovery strategy for step: {step_name}")
    
    def handle_error(self, error: ProcessingError) -> bool:
        """
        Handle an error and return whether processing should continue
        
        Args:
            error: The error to handle
            
        Returns:
            True if processing should continue, False to stop
        """
        self.errors.append(error)
        
        # Log the error based on severity
        self._log_error(error)
        
        # Try custom error handler first
        if error.category in self.error_handlers:
            try:
                return self.error_handlers[error.category](error)
            except Exception as e:
                print(f"Custom error handler failed: {e}")
        
        # Default handling based on severity
        return self._default_error_handling(error)
    
    def _log_error(self, error: ProcessingError):
        """Log error based on severity"""
        # Don't pass error dict as extra to avoid LogRecord conflicts
        error_msg = f"Error in {error.step}: {error.message}"
        if error.exception:
            error_msg += f" (Exception: {type(error.exception).__name__})"
        
        if error.severity == ErrorSeverity.CRITICAL:
            print(error_msg)
        elif error.severity == ErrorSeverity.HIGH:
            print(error_msg)
        elif error.severity == ErrorSeverity.MEDIUM:
            print(error_msg)
        else:
            print(error_msg)
    
    def _default_error_handling(self, error: ProcessingError) -> bool:
        """Default error handling logic"""
        if error.severity == ErrorSeverity.CRITICAL:
            return False  # Stop processing
        elif error.severity == ErrorSeverity.HIGH:
            # Try recovery strategy if available
            if error.step in self.recovery_strategies:
                try:
                    self.recovery_strategies[error.step](error)
                    error.resolved = True
                    return True
                except Exception as e:
                    print(f"Recovery strategy failed for {error.step}: {e}")
            return True  # Continue but flag as failed
        else:
            return True  # Continue for medium and low severity
    
    def can_retry(self, error: ProcessingError) -> bool:
        """Check if an error can be retried"""
        return self.retry_strategy.should_retry(error)
    
    def wait_for_retry(self, error: ProcessingError):
        """Wait before retrying an operation"""
        self.retry_strategy.wait(error.retry_count)
    
    def get_errors(self) -> List[ProcessingError]:
        """Get all errors"""
        return self.errors.copy()
    
    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ProcessingError]:
        """Get errors by severity level"""
        return [e for e in self.errors if e.severity == severity]
    
    def get_errors_by_category(self, category: ErrorCategory) -> List[ProcessingError]:
        """Get errors by category"""
        return [e for e in self.errors if e.category == category]
    
    def get_errors_by_step(self, step_name: str) -> List[ProcessingError]:
        """Get errors for a specific step"""
        return [e for e in self.errors if e.step == step_name]
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors"""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)
    
    def has_unresolved_errors(self) -> bool:
        """Check if there are unresolved errors"""
        return any(not e.resolved for e in self.errors)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        total_errors = len(self.errors)
        if total_errors == 0:
            return {'total_errors': 0}
        
        by_severity = {}
        by_category = {}
        by_step = {}
        
        for error in self.errors:
            # Count by severity
            severity_key = error.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1
            
            # Count by category
            category_key = error.category.value
            by_category[category_key] = by_category.get(category_key, 0) + 1
            
            # Count by step
            by_step[error.step] = by_step.get(error.step, 0) + 1
        
        return {
            'total_errors': total_errors,
            'critical_errors': by_severity.get('critical', 0),
            'unresolved_errors': len([e for e in self.errors if not e.resolved]),
            'by_severity': by_severity,
            'by_category': by_category,
            'by_step': by_step,
            'first_error_time': min(e.timestamp for e in self.errors).isoformat(),
            'last_error_time': max(e.timestamp for e in self.errors).isoformat()
        }
    
    def clear_errors(self):
        """Clear all errors"""
        self.errors.clear()
        print("Cleared all errors")
    
    def clear_resolved_errors(self):
        """Clear only resolved errors"""
        resolved_count = len([e for e in self.errors if e.resolved])
        self.errors = [e for e in self.errors if not e.resolved]
        print(f"Cleared {resolved_count} resolved errors")


def create_error(
    step: str,
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> ProcessingError:
    """Convenience function to create a ProcessingError"""
    return ProcessingError(
        step=step,
        message=message,
        severity=severity,
        category=category,
        exception=exception,
        context=context
    )


def handle_exceptions(
    step_name: str,
    category: ErrorCategory = ErrorCategory.PROCESSING,
    severity: ErrorSeverity = ErrorSeverity.HIGH
):
    """Decorator for automatic exception handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error = create_error(
                    step=step_name,
                    message=f"Exception in {func.__name__}: {str(e)}",
                    severity=severity,
                    category=category,
                    exception=e,
                    context={'function': func.__name__, 'args': str(args)[:100]}
                )
                
                # If an error handler is available in context, use it
                error_handler = kwargs.get('error_handler')
                if error_handler and isinstance(error_handler, ErrorHandler):
                    should_continue = error_handler.handle_error(error)
                    if not should_continue:
                        raise
                else:
                    # Re-raise if no handler available
                    raise
                
                return None  # or some default value
        return wrapper
    return decorator
