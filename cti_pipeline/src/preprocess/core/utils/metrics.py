"""
Metrics and Monitoring for CTI Preprocessing Pipeline

This module provides comprehensive metrics collection, performance monitoring,
and analytics for the preprocessing pipeline.
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

@dataclass
class StepMetrics:
    """Metrics for individual processing steps"""
    name: str
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    average_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=100))
    
    # Data processing metrics
    total_input_size: int = 0
    total_output_size: int = 0
    total_size_reduction: int = 0
    
    # Error tracking
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    consecutive_errors: int = 0
    
    def add_execution(
        self,
        duration: float,
        success: bool = True,
        input_size: int = 0,
        output_size: int = 0,
        error_message: Optional[str] = None
    ):
        """Record an execution of this step"""
        self.execution_count += 1
        self.total_duration += duration
        self.average_duration = self.total_duration / self.execution_count
        
        # Update min/max durations
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        
        # Track recent durations for trend analysis
        self.recent_durations.append(duration)
        
        # Track success/error counts
        if success:
            self.success_count += 1
            self.consecutive_errors = 0
        else:
            self.error_count += 1
            self.consecutive_errors += 1
            self.last_error = error_message
            self.last_error_time = datetime.now()
        
        # Track data sizes
        self.total_input_size += input_size
        self.total_output_size += output_size
        if output_size < input_size:
            self.total_size_reduction += (input_size - output_size)
    
    def get_success_rate(self) -> float:
        """Get success rate as percentage"""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100
    
    def get_recent_average_duration(self, window: int = 10) -> float:
        """Get average duration for recent executions"""
        if not self.recent_durations:
            return 0.0
        
        recent = list(self.recent_durations)[-window:]
        return statistics.mean(recent) if recent else 0.0
    
    def get_throughput(self) -> float:
        """Get processing throughput (executions per second)"""
        if self.total_duration == 0:
            return 0.0
        return self.execution_count / self.total_duration
    
    def get_average_size_reduction(self) -> float:
        """Get average size reduction percentage"""
        if self.total_input_size == 0:
            return 0.0
        return (self.total_size_reduction / self.total_input_size) * 100
    
    def is_healthy(self) -> bool:
        """Check if step is performing well"""
        # Consider unhealthy if recent error rate is high
        if self.consecutive_errors > 3:
            return False
        
        # Check if recent performance is degrading
        if len(self.recent_durations) >= 10:
            recent_avg = self.get_recent_average_duration(10)
            overall_avg = self.average_duration
            if recent_avg > overall_avg * 2:  # Recent performance 2x slower
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'name': self.name,
            'execution_count': self.execution_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.get_success_rate(),
            'total_duration': self.total_duration,
            'average_duration': self.average_duration,
            'min_duration': self.min_duration if self.min_duration != float('inf') else 0,
            'max_duration': self.max_duration,
            'recent_average_duration': self.get_recent_average_duration(),
            'throughput': self.get_throughput(),
            'total_input_size': self.total_input_size,
            'total_output_size': self.total_output_size,
            'average_size_reduction': self.get_average_size_reduction(),
            'consecutive_errors': self.consecutive_errors,
            'last_error': self.last_error,
            'last_error_time': self.last_error_time.isoformat() if self.last_error_time else None,
            'is_healthy': self.is_healthy()
        }


@dataclass
class PipelineMetrics:
    """Pipeline-wide metrics and analytics"""
    pipeline_name: str = "CTI_Pipeline"
    start_time: datetime = field(default_factory=datetime.now)
    
    # Overall pipeline metrics
    total_documents_processed: int = 0
    total_files_processed: int = 0
    total_processing_time: float = 0.0
    
    # Step-specific metrics
    step_metrics: Dict[str, StepMetrics] = field(default_factory=dict)
    
    # Document type tracking
    document_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Performance tracking
    processing_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    hourly_throughput: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Error tracking
    total_errors: int = 0
    errors_by_step: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    def add_step_execution(
        self,
        step_name: str,
        duration: float,
        success: bool = True,
        input_size: int = 0,
        output_size: int = 0,
        error_message: Optional[str] = None
    ):
        """Record execution of a pipeline step"""
        # Initialize step metrics if not exists
        if step_name not in self.step_metrics:
            self.step_metrics[step_name] = StepMetrics(step_name)
        
        # Add execution to step metrics
        self.step_metrics[step_name].add_execution(
            duration, success, input_size, output_size, error_message
        )
        
        # Track pipeline-wide errors
        if not success:
            self.total_errors += 1
            self.errors_by_step[step_name] += 1
    
    def add_document_processed(
        self,
        processing_time: float,
        document_type: str = "unknown",
        file_processed: bool = False
    ):
        """Record that a document was processed"""
        self.total_documents_processed += 1
        self.total_processing_time += processing_time
        
        if file_processed:
            self.total_files_processed += 1
        
        # Track document types
        self.document_types[document_type] += 1
        
        # Track processing times
        self.processing_times.append(processing_time)
        
        # Track hourly throughput
        current_hour = datetime.now().strftime('%Y-%m-%d_%H')
        self.hourly_throughput[current_hour] += 1
    
    def get_uptime(self) -> timedelta:
        """Get pipeline uptime"""
        return datetime.now() - self.start_time
    
    def get_average_processing_time(self) -> float:
        """Get average processing time per document"""
        if self.total_documents_processed == 0:
            return 0.0
        return self.total_processing_time / self.total_documents_processed
    
    def get_recent_processing_times(self, window: int = 100) -> List[float]:
        """Get recent processing times"""
        return list(self.processing_times)[-window:]
    
    def get_throughput(self) -> float:
        """Get overall throughput (documents per second)"""
        uptime_seconds = self.get_uptime().total_seconds()
        if uptime_seconds == 0:
            return 0.0
        return self.total_documents_processed / uptime_seconds
    
    def get_current_hour_throughput(self) -> int:
        """Get throughput for current hour"""
        current_hour = datetime.now().strftime('%Y-%m-%d_%H')
        return self.hourly_throughput[current_hour]
    
    def get_error_rate(self) -> float:
        """Get overall error rate percentage"""
        total_executions = sum(metrics.execution_count for metrics in self.step_metrics.values())
        if total_executions == 0:
            return 0.0
        return (self.total_errors / total_executions) * 100
    
    def get_step_performance_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get performance summary for all steps"""
        return {name: metrics.to_dict() for name, metrics in self.step_metrics.items()}
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status of the pipeline"""
        unhealthy_steps = [
            name for name, metrics in self.step_metrics.items()
            if not metrics.is_healthy()
        ]
        
        # Calculate health score (0-100)
        health_score = 100
        if self.get_error_rate() > 10:  # More than 10% error rate
            health_score -= 30
        if len(unhealthy_steps) > 0:
            health_score -= 20 * len(unhealthy_steps)
        
        recent_times = self.get_recent_processing_times(50)
        if recent_times:
            avg_recent = statistics.mean(recent_times)
            avg_overall = self.get_average_processing_time()
            if avg_recent > avg_overall * 1.5:  # Recent performance degraded
                health_score -= 20
        
        health_score = max(0, health_score)
        
        status = "healthy"
        if health_score < 50:
            status = "critical"
        elif health_score < 70:
            status = "degraded"
        elif health_score < 90:
            status = "warning"
        
        return {
            'status': status,
            'health_score': health_score,
            'unhealthy_steps': unhealthy_steps,
            'error_rate': self.get_error_rate(),
            'throughput': self.get_throughput(),
            'uptime_hours': self.get_uptime().total_seconds() / 3600
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            'pipeline_name': self.pipeline_name,
            'start_time': self.start_time.isoformat(),
            'uptime': str(self.get_uptime()),
            'total_documents_processed': self.total_documents_processed,
            'total_files_processed': self.total_files_processed,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': self.get_average_processing_time(),
            'throughput': self.get_throughput(),
            'current_hour_throughput': self.get_current_hour_throughput(),
            'error_rate': self.get_error_rate(),
            'total_errors': self.total_errors,
            'document_types': dict(self.document_types),
            'step_metrics': self.get_step_performance_summary(),
            'health_status': self.get_health_status(),
            'errors_by_step': dict(self.errors_by_step)
        }
    
    def reset(self):
        """Reset all metrics"""
        self.start_time = datetime.now()
        self.total_documents_processed = 0
        self.total_files_processed = 0
        self.total_processing_time = 0.0
        self.step_metrics.clear()
        self.document_types.clear()
        self.processing_times.clear()
        self.hourly_throughput.clear()
        self.total_errors = 0
        self.errors_by_step.clear()
    
    def export_to_file(self, file_path: str):
        """Export metrics to JSON file"""
        import json
        from pathlib import Path
        
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_summary(), f, indent=2, ensure_ascii=False, default=str)
        
        print(f"[Metrics] Metrics exported to: {file_path}")


class MetricsCollector:
    """Utility class for collecting and aggregating metrics"""
    
    def __init__(self, metrics: PipelineMetrics):
        self.metrics = metrics
    
    def time_step(self, step_name: str):
        """Context manager for timing step execution"""
        return StepTimer(self.metrics, step_name)
    
    def record_file_processing(self, file_path: str, processing_time: float):
        """Record file processing metrics"""
        from pathlib import Path
        file_ext = Path(file_path).suffix.lower()
        self.metrics.add_document_processed(
            processing_time=processing_time,
            document_type=file_ext,
            file_processed=True
        )


class StepTimer:
    """Context manager for timing step execution"""
    
    def __init__(self, metrics: PipelineMetrics, step_name: str):
        self.metrics = metrics
        self.step_name = step_name
        self.start_time = None
        self.success = True
        self.error_message = None
        self.input_size = 0
        self.output_size = 0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.success = False
            self.error_message = str(exc_val)
        
        self.metrics.add_step_execution(
            step_name=self.step_name,
            duration=duration,
            success=self.success,
            input_size=self.input_size,
            output_size=self.output_size,
            error_message=self.error_message
        )
    
    def set_input_size(self, size: int):
        """Set input data size"""
        self.input_size = size
        return self
    
    def set_output_size(self, size: int):
        """Set output data size"""
        self.output_size = size
        return self
