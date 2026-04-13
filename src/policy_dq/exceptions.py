"""
Custom exceptions for the validation API.

This module defines API-specific exceptions that provide clear error handling
and separation from internal implementation errors.
"""


class ValidationAPIError(Exception):
    """Base exception for all validation API errors."""
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize API error.
        
        Args:
            message: Human-readable error message
            details: Additional error details for debugging
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(ValidationAPIError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        """
        Initialize configuration error.
        
        Args:
            message: Human-readable error message
            config_key: Configuration key that caused the error
            details: Additional error details
        """
        super().__init__(message, details)
        self.config_key = config_key


class ValidationExecutionError(ValidationAPIError):
    """Exception raised during validation execution."""
    
    def __init__(self, message: str, stage: str = None, details: dict = None):
        """
        Initialize validation execution error.
        
        Args:
            message: Human-readable error message
            stage: Validation stage where error occurred
            details: Additional error details
        """
        super().__init__(message, details)
        self.stage = stage


class RuleConfigurationError(ConfigurationError):
    """Exception raised for rule configuration errors."""
    pass


class DataSourceError(ValidationAPIError):
    """Exception raised for data source access errors."""
    
    def __init__(self, message: str, source_path: str = None, details: dict = None):
        """
        Initialize data source error.
        
        Args:
            message: Human-readable error message
            source_path: Path to the problematic data source
            details: Additional error details
        """
        super().__init__(message, details)
        self.source_path = source_path


class ReportGenerationError(ValidationAPIError):
    """Exception raised during report generation."""
    
    def __init__(self, message: str, report_type: str = None, details: dict = None):
        """
        Initialize report generation error.
        
        Args:
            message: Human-readable error message
            report_type: Type of report that failed to generate
            details: Additional error details
        """
        super().__init__(message, details)
        self.report_type = report_type