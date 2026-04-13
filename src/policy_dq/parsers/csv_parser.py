"""
CSV parser implementation for data validation system.

This module provides CSV parsing functionality with encoding detection,
error handling, and support for various CSV formats.
"""

import csv
import os
from typing import List, Dict, Any
import chardet
from .base import DataParser, DataParsingError


class CSVParser(DataParser):
    """
    CSV parser with encoding detection and error handling.
    
    Supports various CSV formats and provides detailed error reporting
    for parsing issues.
    """
    
    def __init__(self, delimiter: str = None, encoding: str = None):
        """
        Initialize CSV parser.
        
        Args:
            delimiter: CSV delimiter character (auto-detected if None)
            encoding: File encoding (auto-detected if None)
        """
        self.delimiter = delimiter
        self.encoding = encoding
    
    def validate_format(self, file_path: str) -> bool:
        """
        Validate if file is a CSV format.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if file appears to be CSV format, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        # Check file extension
        if not file_path.lower().endswith('.csv'):
            return False
            
        try:
            # Try to read first few lines to validate CSV structure
            encoding = self._detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding, newline='') as file:
                # Read first few lines to check if it's valid CSV
                sample = file.read(1024)
                if not sample.strip():
                    return False
                    
                # Use CSV sniffer to detect format
                sniffer = csv.Sniffer()
                try:
                    sniffer.sniff(sample)
                    return True
                except csv.Error:
                    # If sniffer fails, try basic parsing
                    file.seek(0)
                    reader = csv.reader(file)
                    next(reader)  # Try to read first row
                    return True
                    
        except Exception:
            return False
    
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV file and return list of records.
        
        Args:
            file_path: Path to the CSV file to parse
            
        Returns:
            List of dictionaries representing CSV records
            
        Raises:
            DataParsingError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        if not self.validate_format(file_path):
            raise DataParsingError(
                "File does not appear to be a valid CSV format",
                file_path=file_path
            )
        
        try:
            encoding = self.encoding or self._detect_encoding(file_path)
            delimiter = self.delimiter or self._detect_delimiter(file_path, encoding)
            
            records = []
            
            with open(file_path, 'r', encoding=encoding, newline='') as file:
                reader = csv.DictReader(file, delimiter=delimiter)
                
                # Validate headers
                if not reader.fieldnames:
                    raise DataParsingError(
                        "CSV file has no headers or is empty",
                        file_path=file_path,
                        line_number=1
                    )
                
                # Check for duplicate headers
                headers = reader.fieldnames
                if len(headers) != len(set(headers)):
                    duplicates = [h for h in headers if headers.count(h) > 1]
                    raise DataParsingError(
                        f"Duplicate column headers found: {duplicates}",
                        file_path=file_path,
                        line_number=1
                    )
                
                # Parse records
                for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    try:
                        # Clean up the record - remove None keys and strip whitespace
                        cleaned_row = {}
                        for key, value in row.items():
                            if key is not None:  # Skip None keys from malformed CSV
                                cleaned_key = key.strip() if key else key
                                cleaned_value = value.strip() if isinstance(value, str) else value
                                cleaned_row[cleaned_key] = cleaned_value
                        
                        records.append(cleaned_row)
                        
                    except Exception as e:
                        raise DataParsingError(
                            f"Error parsing record: {str(e)}",
                            file_path=file_path,
                            line_number=line_num
                        )
            
            return records
            
        except DataParsingError:
            raise
        except UnicodeDecodeError as e:
            raise DataParsingError(
                f"Encoding error: {str(e)}. Try specifying a different encoding.",
                file_path=file_path
            )
        except csv.Error as e:
            raise DataParsingError(
                f"CSV parsing error: {str(e)}",
                file_path=file_path
            )
        except Exception as e:
            raise DataParsingError(
                f"Unexpected error during parsing: {str(e)}",
                file_path=file_path
            )
    
    def _detect_encoding(self, file_path: str) -> str:
        """
        Detect file encoding using chardet.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected encoding string
        """
        try:
            with open(file_path, 'rb') as file:
                # Read sample for encoding detection
                sample = file.read(10000)  # Read first 10KB
                result = chardet.detect(sample)
                
                encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                # If confidence is low, fallback to common encodings
                if confidence < 0.7:
                    for fallback_encoding in ['utf-8', 'latin-1', 'cp1252']:
                        try:
                            sample.decode(fallback_encoding)
                            return fallback_encoding
                        except UnicodeDecodeError:
                            continue
                
                return encoding or 'utf-8'
                
        except Exception:
            return 'utf-8'  # Default fallback
    
    def _detect_delimiter(self, file_path: str, encoding: str) -> str:
        """
        Detect CSV delimiter using csv.Sniffer.
        
        Args:
            file_path: Path to the CSV file
            encoding: File encoding
            
        Returns:
            Detected delimiter character
        """
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as file:
                # Read sample for delimiter detection
                sample = file.read(1024)
                
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                return delimiter
                
        except Exception:
            # Fallback to comma if detection fails
            return ','