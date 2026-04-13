"""
JSON parser implementation for data validation system.

This module provides JSON parsing functionality with support for both
single objects and arrays, nested structures, and detailed error reporting.
"""

import json
import os
from typing import List, Dict, Any, Union
from .base import DataParser, DataParsingError


class JSONParser(DataParser):
    """
    JSON parser with support for single objects, arrays, and nested structures.
    
    Provides detailed error reporting including line numbers for parsing issues.
    """
    
    def __init__(self, flatten_nested: bool = False):
        """
        Initialize JSON parser.
        
        Args:
            flatten_nested: If True, flatten nested objects using dot notation
                          (e.g., {"user": {"name": "John"}} becomes {"user.name": "John"})
        """
        self.flatten_nested = flatten_nested
    
    def validate_format(self, file_path: str) -> bool:
        """
        Validate if file is a JSON format.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file appears to be JSON format, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        # Check file extension
        if not file_path.lower().endswith('.json'):
            return False
            
        try:
            # Try to read the file with UTF-8 encoding (with BOM handling)
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                content = file.read().strip()
                if not content:
                    return False
                    
                # Attempt to parse JSON - this validates the format
                json.loads(content)
                return True
                
        except (json.JSONDecodeError, UnicodeDecodeError, Exception):
            return False
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse JSON file and return list of records.
        
        Supports both single JSON objects and arrays of objects.
        For single objects, returns a list with one element.
        
        Args:
            file_path: Path to the JSON file to parse
            
        Returns:
            List of dictionaries representing JSON records
            
        Raises:
            DataParsingError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if not self.validate_format(file_path):
            raise DataParsingError(
                "File does not appear to be a valid JSON format",
                file_path=file_path
            )
        
        try:
            # Try UTF-8 with BOM handling first
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as file:
                    content = file.read().strip()
            except UnicodeDecodeError:
                # Fallback to regular UTF-8
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read().strip()
                
            if not content:
                raise DataParsingError(
                    "JSON file is empty",
                    file_path=file_path,
                    line_number=1
                )
            
            # Parse JSON content
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                # Extract line number from JSON decode error
                line_number = self._extract_line_number_from_error(content, e)
                raise DataParsingError(
                    f"JSON parsing error: {e.msg}",
                    file_path=file_path,
                    line_number=line_number
                )
            
            # Convert to list of records
            records = self._normalize_to_records(data, file_path)
            
            # Apply flattening if requested
            if self.flatten_nested:
                records = [self._flatten_dict(record) for record in records]
            
            return records
                
        except DataParsingError:
            raise
        except UnicodeDecodeError as e:
            raise DataParsingError(
                f"Encoding error: {str(e)}. File must be UTF-8 encoded.",
                file_path=file_path
            )
        except Exception as e:
            raise DataParsingError(
                f"Unexpected error during parsing: {str(e)}",
                file_path=file_path
            )
    
    def _normalize_to_records(self, data: Union[Dict, List], file_path: str) -> List[Dict[str, Any]]:
        """
        Normalize JSON data to a list of record dictionaries.
        
        Args:
            data: Parsed JSON data (dict or list)
            file_path: Path to the file being parsed (for error reporting)
            
        Returns:
            List of dictionaries representing records
            
        Raises:
            DataParsingError: If data structure is not supported
        """
        if isinstance(data, dict):
            # Single object - return as single-item list
            return [data]
        elif isinstance(data, list):
            # Array of objects
            if not data:
                # Empty array is valid
                return []
            
            records = []
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    raise DataParsingError(
                        f"Array item at index {i} is not an object. "
                        f"Expected object, got {type(item).__name__}: {item}",
                        file_path=file_path,
                        line_number=self._estimate_line_number_for_array_item(i)
                    )
                records.append(item)
            
            return records
        else:
            raise DataParsingError(
                f"JSON root must be an object or array of objects. "
                f"Got {type(data).__name__}: {data}",
                file_path=file_path,
                line_number=1
            )
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten nested dictionary using dot notation.
        
        Args:
            d: Dictionary to flatten
            parent_key: Parent key prefix
            sep: Separator for nested keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                # Recursively flatten nested dictionaries
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Handle arrays - convert to indexed keys
                for i, item in enumerate(v):
                    array_key = f"{new_key}[{i}]"
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, array_key, sep=sep).items())
                    else:
                        items.append((array_key, item))
            else:
                items.append((new_key, v))
        
        return dict(items)
    
    def _extract_line_number_from_error(self, content: str, error: json.JSONDecodeError) -> int:
        """
        Extract line number from JSON decode error.
        
        Args:
            content: Original JSON content
            error: JSONDecodeError with position information
            
        Returns:
            Estimated line number where error occurred
        """
        try:
            # Count newlines up to the error position
            if hasattr(error, 'pos') and error.pos is not None:
                lines_before_error = content[:error.pos].count('\n')
                return lines_before_error + 1
            else:
                # Fallback: try to extract from error message
                if hasattr(error, 'lineno') and error.lineno is not None:
                    return error.lineno
                return 1
        except Exception:
            return 1
    
    def _estimate_line_number_for_array_item(self, index: int) -> int:
        """
        Estimate line number for array item (rough approximation).
        
        Args:
            index: Array item index
            
        Returns:
            Estimated line number
        """
        # This is a rough estimate - in practice, line numbers for array items
        # would require more sophisticated parsing to be accurate
        return index + 2  # Assume array starts on line 2, items follow