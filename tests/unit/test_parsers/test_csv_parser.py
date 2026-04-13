"""
Unit tests for CSV parser implementation.

Tests cover various CSV formats, edge cases, error handling,
and encoding detection functionality.
"""

import pytest
import tempfile
import os

from src.policy_dq.parsers.csv_parser import CSVParser
from src.policy_dq.parsers.base import DataParsingError


class TestCSVParser:
    """Test suite for CSVParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CSVParser()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_csv(self, content: str, encoding: str = 'utf-8') -> str:
        """Create a temporary CSV file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def create_temp_file(self, content: bytes, suffix: str = '.csv') -> str:
        """Create a temporary file with binary content."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name

    def test_validate_format_valid_csv(self):
        """Test format validation for valid CSV files."""
        csv_content = "name,age,email\nJohn,25,john@example.com\nJane,30,jane@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        assert self.parser.validate_format(file_path) is True
    
    def test_validate_format_non_csv_extension(self):
        """Test format validation rejects non-CSV extensions."""
        content = "name,age,email\nJohn,25,john@example.com"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            
        assert self.parser.validate_format(f.name) is False
    
    def test_validate_format_nonexistent_file(self):
        """Test format validation for nonexistent files."""
        assert self.parser.validate_format("nonexistent.csv") is False
    
    def test_validate_format_empty_file(self):
        """Test format validation for empty files."""
        file_path = self.create_temp_csv("")
        assert self.parser.validate_format(file_path) is False
    
    def test_parse_simple_csv(self):
        """Test parsing a simple CSV file."""
        csv_content = "name,age,email\nJohn,25,john@example.com\nJane,30,jane@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": "25", "email": "john@example.com"},
            {"name": "Jane", "age": "30", "email": "jane@example.com"}
        ]
        
        assert result == expected
    
    def test_parse_csv_with_whitespace(self):
        """Test parsing CSV with extra whitespace."""
        csv_content = " name , age , email \n John , 25 , john@example.com \n Jane , 30 , jane@example.com "
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": "25", "email": "john@example.com"},
            {"name": "Jane", "age": "30", "email": "jane@example.com"}
        ]
        
        assert result == expected
    
    def test_parse_csv_with_semicolon_delimiter(self):
        """Test parsing CSV with semicolon delimiter."""
        csv_content = "name;age;email\nJohn;25;john@example.com\nJane;30;jane@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": "25", "email": "john@example.com"},
            {"name": "Jane", "age": "30", "email": "jane@example.com"}
        ]
        
        assert result == expected
    
    def test_parse_csv_with_custom_delimiter(self):
        """Test parsing CSV with custom delimiter specified in constructor."""
        csv_content = "name|age|email\nJohn|25|john@example.com\nJane|30|jane@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        parser = CSVParser(delimiter='|')
        result = parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": "25", "email": "john@example.com"},
            {"name": "Jane", "age": "30", "email": "jane@example.com"}
        ]
        
        assert result == expected
    
    def test_parse_csv_with_quoted_fields(self):
        """Test parsing CSV with quoted fields containing commas."""
        csv_content = 'name,description,price\n"Product A","High quality, durable",29.99\n"Product B","Compact, lightweight",19.99'
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "Product A", "description": "High quality, durable", "price": "29.99"},
            {"name": "Product B", "description": "Compact, lightweight", "price": "19.99"}
        ]
        
        assert result == expected
    
    def test_parse_csv_empty_fields(self):
        """Test parsing CSV with empty fields."""
        csv_content = "name,age,email\nJohn,,john@example.com\n,30,jane@example.com\nBob,25,"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": "", "email": "john@example.com"},
            {"name": "", "age": "30", "email": "jane@example.com"},
            {"name": "Bob", "age": "25", "email": ""}
        ]
        
        assert result == expected
    
    def test_parse_csv_single_row(self):
        """Test parsing CSV with single data row."""
        csv_content = "name,age,email\nJohn,25,john@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{"name": "John", "age": "25", "email": "john@example.com"}]
        
        assert result == expected
    
    def test_parse_csv_headers_only(self):
        """Test parsing CSV with headers but no data rows."""
        csv_content = "name,age,email"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        assert result == []
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("nonexistent.csv")
    
    def test_parse_empty_file(self):
        """Test parsing empty file raises DataParsingError."""
        file_path = self.create_temp_csv("")
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "does not appear to be a valid CSV format" in str(exc_info.value)
    
    def test_parse_no_headers(self):
        """Test parsing file with no headers raises DataParsingError."""
        # Create a file that looks like CSV but has no proper headers
        csv_content = "\n\n"
        file_path = self.create_temp_csv(csv_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "does not appear to be a valid CSV format" in str(exc_info.value)
    
    def test_parse_duplicate_headers(self):
        """Test parsing CSV with duplicate headers raises DataParsingError."""
        csv_content = "name,age,name\nJohn,25,Johnny\nJane,30,Janey"
        file_path = self.create_temp_csv(csv_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "Duplicate column headers" in str(exc_info.value)
        assert "name" in str(exc_info.value)
    
    def test_encoding_detection_utf8(self):
        """Test encoding detection for UTF-8 files."""
        csv_content = "name,description\nJohn,Café owner\nJane,Naïve user"
        file_path = self.create_temp_csv(csv_content, encoding='utf-8')
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "description": "Café owner"},
            {"name": "Jane", "description": "Naïve user"}
        ]
        
        assert result == expected
    
    def test_encoding_detection_latin1(self):
        """Test encoding detection for Latin-1 files."""
        csv_content = "name,description\nJohn,Café owner\nJane,Naïve user"
        
        # Create file with Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                       delete=False, encoding='latin-1') as f:
            f.write(csv_content)
            self.temp_files.append(f.name)
            file_path = f.name
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "description": "Café owner"},
            {"name": "Jane", "description": "Naïve user"}
        ]
        
        assert result == expected
    
    def test_custom_encoding(self):
        """Test parsing with custom encoding specified in constructor."""
        csv_content = "name,description\nJohn,Café owner"
        
        # Create file with Latin-1 encoding
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                       delete=False, encoding='latin-1') as f:
            f.write(csv_content)
            self.temp_files.append(f.name)
            file_path = f.name
        
        parser = CSVParser(encoding='latin-1')
        result = parser.parse(file_path)
        
        expected = [{"name": "John", "description": "Café owner"}]
        
        assert result == expected
    
    def test_malformed_csv_unbalanced_quotes(self):
        """Test parsing malformed CSV with unbalanced quotes."""
        csv_content = 'name,description\n"John,Missing quote\nJane,"Complete quote"'
        file_path = self.create_temp_csv(csv_content)
        
        # This should either parse successfully (if CSV module handles it)
        # or raise a DataParsingError
        try:
            result = self.parser.parse(file_path)
            # If it parses, verify the structure is reasonable
            assert isinstance(result, list)
        except DataParsingError:
            # This is also acceptable for malformed CSV
            pass
    
    def test_large_csv_file(self):
        """Test parsing a larger CSV file for performance."""
        # Generate a CSV with 1000 rows
        lines = ["name,age,email"]
        for i in range(1000):
            lines.append(f"User{i},{20 + (i % 50)},user{i}@example.com")
        
        csv_content = "\n".join(lines)
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1000
        assert result[0]["name"] == "User0"
        assert result[999]["name"] == "User999"
    
    def test_csv_with_newlines_in_fields(self):
        """Test parsing CSV with newlines within quoted fields."""
        csv_content = 'name,description\n"John","Line 1\nLine 2"\n"Jane","Single line"'
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        # Handle both Unix (\n) and Windows (\r\n) line endings
        expected_description = "Line 1\nLine 2"
        if result and result[0].get("description"):
            # Normalize line endings for comparison
            actual_description = result[0]["description"].replace('\r\n', '\n')
            expected = [
                {"name": "John", "description": expected_description},
                {"name": "Jane", "description": "Single line"}
            ]
            # Normalize the actual result for comparison
            normalized_result = []
            for record in result:
                normalized_record = {}
                for key, value in record.items():
                    if isinstance(value, str):
                        normalized_record[key] = value.replace('\r\n', '\n')
                    else:
                        normalized_record[key] = value
                normalized_result.append(normalized_record)
            
            assert normalized_result == expected
        else:
            # Fallback to original assertion if structure is unexpected
            expected = [
                {"name": "John", "description": expected_description},
                {"name": "Jane", "description": "Single line"}
            ]
            assert result == expected
    
    def test_invalid_encoding_handling(self):
        """Test handling of files with invalid encoding."""
        # Create a file with invalid UTF-8 bytes
        invalid_utf8 = b'name,description\nJohn,Caf\xe9 owner\n'
        file_path = self.create_temp_file(invalid_utf8)
        
        # Should either parse successfully with encoding detection
        # or raise appropriate error
        try:
            result = self.parser.parse(file_path)
            assert isinstance(result, list)
        except DataParsingError as e:
            assert "encoding" in str(e).lower() or "error" in str(e).lower()
    
    def test_csv_with_inconsistent_columns(self):
        """Test parsing CSV with inconsistent number of columns."""
        csv_content = "name,age,email\nJohn,25,john@example.com\nJane,30\nBob,35,bob@example.com,extra"
        file_path = self.create_temp_csv(csv_content)
        
        # Should handle inconsistent columns gracefully
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        # Jane should have empty email field (None gets converted to empty string in some CSV readers)
        assert result[1]["name"] == "Jane"
        assert result[1]["age"] == "30"
        assert result[1]["email"] in ("", None)  # Accept both empty string and None
        # Bob should have the extra field ignored or handled
        assert result[2]["name"] == "Bob"
    
    def test_csv_with_only_headers_and_empty_lines(self):
        """Test parsing CSV with headers and empty lines."""
        csv_content = "name,age,email\n\n\n"
        file_path = self.create_temp_csv(csv_content)
        
        # Should handle empty lines gracefully
        try:
            result = self.parser.parse(file_path)
            assert result == []
        except DataParsingError:
            # Some CSV parsers may reject files with only empty lines after headers
            pass
    
    def test_csv_with_mixed_line_endings(self):
        """Test parsing CSV with mixed line endings."""
        csv_content = "name,age,email\nJohn,25,john@example.com\r\nJane,30,jane@example.com\rBob,35,bob@example.com"
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert result[0]["name"] == "John"
        assert result[1]["name"] == "Jane"
        assert result[2]["name"] == "Bob"


class TestCSVParserEdgeCases:
    """Additional edge case tests for CSV parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CSVParser()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_csv(self, content: str, encoding: str = 'utf-8') -> str:
        """Create a temporary CSV file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def test_csv_with_bom(self):
        """Test parsing CSV file with Byte Order Mark (BOM)."""
        csv_content = "name,age\nJohn,25\nJane,30"
        
        # Create file with BOM
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(csv_content.encode('utf-8'))
            self.temp_files.append(f.name)
            file_path = f.name
        
        result = self.parser.parse(file_path)
        
        # Should handle BOM correctly
        assert len(result) == 2
        assert "name" in result[0]  # Header should not have BOM characters
    
    def test_csv_with_very_long_lines(self):
        """Test parsing CSV with very long field values."""
        long_description = "A" * 10000  # 10KB field
        csv_content = f'name,description\nJohn,"{long_description}"\nJane,"Short desc"'
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 2
        assert result[0]["description"] == long_description
        assert result[1]["description"] == "Short desc"
    
    def test_csv_with_special_characters(self):
        """Test parsing CSV with various special characters."""
        csv_content = 'name,symbols\n"John","!@#$%^&*()"\n"Jane","<>?:{}[]|\\"\n"Bob","åäöñç"'
        file_path = self.create_temp_csv(csv_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 3
        assert result[0]["symbols"] == "!@#$%^&*()"
        assert result[1]["symbols"] == '<>?:{}[]|\\'
        assert result[2]["symbols"] == "åäöñç"