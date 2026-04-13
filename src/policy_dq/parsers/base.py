"""
Base parser interface for data validation system.

This module defines the abstract base class that all data parsers must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DataParser(ABC):
    """
    Abstract base class for data parsers.
    
    All concrete parser implementations must inherit from this class
    and implement the required methods.
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse data file and return list of records.
        
        Args:
            file_path: Path to the data file to parse
            
        Returns:
            List of dictionaries, where each dictionary represents a record
            with field names as keys and field values as values
            
        Raises:
            DataParsingError: If the file cannot be parsed
            FileNotFoundError: If the file does not exist
        """
        pass
    
    @abstractmethod
    def validate_format(self, file_path: str) -> bool:
        """
        Validate if file format is supported by this parser.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if the file format is supported, False otherwise
        """
        pass


class DataParsingError(Exception):
    """Exception raised when data parsing fails."""
    
    def __init__(self, message: str, file_path: str = None, line_number: int = None):
        """
        Initialize parsing error.
        
        Args:
            message: Error description
            file_path: Path to the file that caused the error
            line_number: Line number where the error occurred (if applicable)
        """
        self.file_path = file_path
        self.line_number = line_number
        
        error_msg = message
        if file_path:
            error_msg = f"Error parsing file '{file_path}': {message}"
        if line_number:
            error_msg += f" (line {line_number})"
            
        super().__init__(error_msg)