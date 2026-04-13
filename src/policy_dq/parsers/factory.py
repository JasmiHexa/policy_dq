"""
Parser factory for automatic parser selection based on file format.

This module provides a factory class that automatically selects the appropriate
parser based on file extension and validates format compatibility.
"""

import os
from typing import Dict, Type
from .base import DataParser, DataParsingError
from .csv_parser import CSVParser
from .json_parser import JSONParser


class UnsupportedFormatError(DataParsingError):
    """Exception raised when file format is not supported."""
    
    def __init__(self, file_path: str, supported_formats: list = None):
        """
        Initialize unsupported format error.
        
        Args:
            file_path: Path to the unsupported file
            supported_formats: List of supported file extensions
        """
        self.supported_formats = supported_formats or []
        
        message = f"Unsupported file format for '{file_path}'"
        if self.supported_formats:
            message += f". Supported formats: {', '.join(self.supported_formats)}"
            
        super().__init__(message, file_path=file_path)


class ParserFactory:
    """
    Factory class for creating appropriate data parsers based on file format.
    
    Automatically selects the correct parser implementation based on file extension
    and validates format compatibility before parsing.
    """
    
    def __init__(self):
        """Initialize parser factory with default parser mappings."""
        self._parsers: Dict[str, Type[DataParser]] = {
            '.csv': CSVParser,
            '.json': JSONParser,
        }
    
    def register_parser(self, extension: str, parser_class: Type[DataParser]) -> None:
        """
        Register a new parser for a specific file extension.
        
        Args:
            extension: File extension (e.g., '.xml', '.yaml')
            parser_class: Parser class that implements DataParser interface
            
        Raises:
            ValueError: If extension is invalid or parser_class doesn't implement DataParser
        """
        if not extension.startswith('.'):
            raise ValueError(f"Extension must start with '.': {extension}")
            
        if not issubclass(parser_class, DataParser):
            raise ValueError(f"Parser class must implement DataParser interface: {parser_class}")
            
        self._parsers[extension.lower()] = parser_class
    
    def get_supported_extensions(self) -> list:
        """
        Get list of supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(self._parsers.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """
        Check if file format is supported.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if file format is supported, False otherwise
        """
        if not file_path:
            return False
            
        extension = self._get_file_extension(file_path)
        return extension in self._parsers
    
    def create_parser(self, file_path: str, **kwargs) -> DataParser:
        """
        Create appropriate parser for the given file.
        
        Args:
            file_path: Path to the file to parse
            **kwargs: Additional arguments to pass to parser constructor
            
        Returns:
            Parser instance appropriate for the file format
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFormatError: If file format is not supported
            DataParsingError: If parser validation fails
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        extension = self._get_file_extension(file_path)
        
        if extension not in self._parsers:
            raise UnsupportedFormatError(
                file_path=file_path,
                supported_formats=self.get_supported_extensions()
            )
        
        # Create parser instance
        parser_class = self._parsers[extension]
        parser = parser_class(**kwargs)
        
        # Validate that the parser can handle this specific file
        if not parser.validate_format(file_path):
            raise DataParsingError(
                f"File format validation failed. The file '{file_path}' "
                f"has extension '{extension}' but doesn't appear to be a valid "
                f"{extension.upper()} file.",
                file_path=file_path
            )
        
        return parser
    
    def parse_file(self, file_path: str, **kwargs):
        """
        Parse file using appropriate parser.
        
        Convenience method that creates parser and parses file in one step.
        
        Args:
            file_path: Path to the file to parse
            **kwargs: Additional arguments to pass to parser constructor
            
        Returns:
            Parsed data as returned by the appropriate parser
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnsupportedFormatError: If file format is not supported
            DataParsingError: If parsing fails
        """
        parser = self.create_parser(file_path, **kwargs)
        return parser.parse(file_path)
    
    def _get_file_extension(self, file_path: str) -> str:
        """
        Extract file extension from file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension in lowercase (e.g., '.csv', '.json')
        """
        _, extension = os.path.splitext(file_path)
        return extension.lower()


# Default factory instance for convenience
default_factory = ParserFactory()


def create_parser(file_path: str, **kwargs) -> DataParser:
    """
    Create appropriate parser for the given file using default factory.
    
    Convenience function for common use cases.
    
    Args:
        file_path: Path to the file to parse
        **kwargs: Additional arguments to pass to parser constructor
        
    Returns:
        Parser instance appropriate for the file format
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnsupportedFormatError: If file format is not supported
        DataParsingError: If parser validation fails
    """
    return default_factory.create_parser(file_path, **kwargs)


def parse_file(file_path: str, **kwargs):
    """
    Parse file using appropriate parser from default factory.
    
    Convenience function for common use cases.
    
    Args:
        file_path: Path to the file to parse
        **kwargs: Additional arguments to pass to parser constructor
        
    Returns:
        Parsed data as returned by the appropriate parser
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnsupportedFormatError: If file format is not supported
        DataParsingError: If parsing fails
    """
    return default_factory.parse_file(file_path, **kwargs)


def get_supported_extensions() -> list:
    """
    Get list of supported file extensions from default factory.
    
    Returns:
        List of supported file extensions
    """
    return default_factory.get_supported_extensions()


def is_supported(file_path: str) -> bool:
    """
    Check if file format is supported by default factory.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if file format is supported, False otherwise
    """
    return default_factory.is_supported(file_path)