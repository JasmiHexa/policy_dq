"""
Base reporter interface for the validation system.

This module defines the abstract base class that all reporters must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
from ..models import ValidationReport


class Reporter(ABC):
    """Abstract base class for all validation report generators."""
    
    @abstractmethod
    def generate_report(self, report: ValidationReport, output_path: Optional[str] = None) -> None:
        """
        Generate a validation report in the specific format.
        
        Args:
            report: The validation report to format and output
            output_path: Optional path for file-based reporters
        """
        pass