"""
Base classes for rule loading.

This module defines the abstract base class for rule loaders that can
load validation rules from various sources.
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import ValidationRule


class RuleLoader(ABC):
    """
    Abstract base class for loading validation rules from various sources.
    
    Rule loaders are responsible for reading rule configurations from
    different sources (files, databases, APIs, etc.) and converting them
    into ValidationRule objects.
    """
    
    @abstractmethod
    def load_rules(self, source: str) -> List[ValidationRule]:
        """
        Load validation rules from the specified source.
        
        Args:
            source: Source identifier (file path, URL, etc.)
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If rules cannot be loaded or parsed
        """
        pass
    
    @abstractmethod
    def validate_source(self, source: str) -> bool:
        """
        Validate that the source is accessible and properly formatted.
        
        Args:
            source: Source identifier to validate
            
        Returns:
            True if source is valid and accessible, False otherwise
        """
        pass


class RuleLoadingError(Exception):
    """Exception raised when rules cannot be loaded or parsed."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}