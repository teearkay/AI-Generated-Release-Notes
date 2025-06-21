"""Enhanced logging utilities for the release notes application."""

import logging
import time
import functools
from typing import Any, Callable, Dict, Optional
import json


class PerformanceLogger:
    """Utility class for performance monitoring and logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers: Dict[str, float] = {}
    
    def start_timer(self, operation: str) -> None:
        """Start timing an operation."""
        self.timers[operation] = time.time()
        self.logger.debug(f"PERF: Started timer for {operation}")
    
    def end_timer(self, operation: str) -> float:
        """End timing an operation and log the duration."""
        if operation not in self.timers:
            self.logger.warning(f"PERF: No timer found for operation: {operation}")
            return 0.0
        
        duration = time.time() - self.timers[operation]
        self.logger.info(f"PERF: {operation} completed in {duration:.3f}s")
        del self.timers[operation]
        return duration
    
    def log_with_timing(self, operation: str):
        """Decorator to automatically time and log function execution."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    self.logger.info(f"PERF: Starting {operation}")
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    self.logger.info(f"PERF: {operation} completed successfully in {duration:.3f}s")
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    self.logger.error(f"PERF: {operation} failed after {duration:.3f}s - {type(e).__name__}: {str(e)}")
                    raise
            return wrapper
        return decorator


class StructuredLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.performance = PerformanceLogger(logger)
    
    def log_function_entry(self, func_name: str, **kwargs) -> None:
        """Log function entry with parameters."""
        params = {k: str(v)[:100] for k, v in kwargs.items()}  # Truncate long values
        self.logger.info(f"ENTRY: {func_name} - Parameters: {params}")
    
    def log_function_exit(self, func_name: str, result_summary: Optional[str] = None) -> None:
        """Log function exit with optional result summary."""
        if result_summary:
            self.logger.info(f"EXIT: {func_name} - Result: {result_summary}")
        else:
            self.logger.info(f"EXIT: {func_name}")
    
    def log_data_quality(self, data_type: str, data: Any, expected_type: type = None) -> None:
        """Log data quality information."""
        try:
            if data is None:
                self.logger.warning(f"QUALITY: {data_type} is None")
                return
            
            actual_type = type(data)
            size_info = ""
            content = ""
            
            if hasattr(data, '__len__'):
                size_info = f", size: {len(data)}"
                content = f", Content: {data}"
            
            self.logger.info(f"QUALITY: {data_type} - type: {actual_type.__name__}{size_info}{content}")
            
            if expected_type and not isinstance(data, expected_type):
                self.logger.warning(f"QUALITY: {data_type} type mismatch - expected: {expected_type.__name__}, got: {actual_type.__name__}")
            
            # Additional quality checks for strings
            if isinstance(data, str):
                if len(data) == 0:
                    self.logger.warning(f"QUALITY: {data_type} is empty string")
                elif len(data) < 10:
                    self.logger.warning(f"QUALITY: {data_type} is very short ({len(data)} chars)")
                elif "error" in data.lower() or "fail" in data.lower():
                    self.logger.warning(f"QUALITY: {data_type} contains error indicators")
                    
        except Exception as e:
            self.logger.error(f"QUALITY: Error analyzing {data_type}: {e}")
    
    def log_api_call(self, service: str, operation: str, **kwargs) -> None:
        """Log external API calls."""
        params = {k: str(v)[:50] for k, v in kwargs.items()}  # Truncate for security
        self.logger.info(f"API: {service}.{operation} - Parameters: {params}")
    
    def log_api_response(self, service: str, operation: str, success: bool, response_size: int = 0, duration: float = 0) -> None:
        """Log API response information."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"API: {service}.{operation} - {status} - Size: {response_size}B, Duration: {duration:.3f}s")
    
    def log_security_event(self, event_type: str, details: str) -> None:
        """Log security-related events."""
        self.logger.warning(f"SECURITY: {event_type} - {details}")
    
    def log_business_metric(self, metric_name: str, value: Any, unit: str = "") -> None:
        """Log business metrics for monitoring."""
        self.logger.info(f"METRIC: {metric_name} = {value} {unit}".strip())


def create_enhanced_logger(name: str) -> StructuredLogger:
    """Create an enhanced logger instance."""
    base_logger = logging.getLogger(name)
    return StructuredLogger(base_logger)


def log_exceptions(logger: logging.Logger):
    """Decorator to automatically log exceptions with context."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"EXCEPTION: {func.__name__} failed - {type(e).__name__}: {str(e)}")
                logger.debug(f"EXCEPTION: Function args: {args}")
                logger.debug(f"EXCEPTION: Function kwargs: {kwargs}")
                raise
        return wrapper
    return decorator


def sanitize_for_logging(data: Any, max_length: int = 200) -> str:
    """Safely convert data to string for logging, avoiding sensitive information."""
    try:
        if data is None:
            return "None"
        
        if isinstance(data, (str, int, float, bool)):
            result = str(data)
        elif isinstance(data, dict):
            # Remove potentially sensitive keys
            safe_dict = {}
            sensitive_keys = {'password', 'secret', 'key', 'token', 'credential'}
            for k, v in data.items():
                if any(sensitive in str(k).lower() for sensitive in sensitive_keys):
                    safe_dict[k] = "[REDACTED]"
                else:
                    safe_dict[k] = str(v)[:50]  # Truncate values
            result = json.dumps(safe_dict)
        elif isinstance(data, list):
            result = f"List[{len(data)} items]"
        else:
            result = f"{type(data).__name__}({str(data)[:50]})"
        
        # Truncate if too long
        if len(result) > max_length:
            result = result[:max_length] + "..."
        
        return result
    except Exception:
        return f"<Error converting {type(data).__name__} to string>"
