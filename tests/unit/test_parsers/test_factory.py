"""
Integration tests for parser factory implementation.

Tests cover parser selection, error handling, format validation,
and integration with existing parsers.
"""

import pytest
import tempfile
import os

from src.policy_dq.parsers.factory import (
    ParserFactory, 
    UnsupportedFormatError,
    create_parser,
    parse_file,
    get_supported_extensions,
    is_supported
)
from src.policy_dq.parsers.base import DataParser, DataParsingError
from src.policy_dq.parsers.csv_parser import CSVParser
from src.policy_dq.parsers.json_parser import JSONParser


class TestParserFactory:
    """Test suite for ParserFactory class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ParserFactory()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_file(self, content: str, suffix: str, encoding: str = 'utf-8') -> str:
        """Create a temporary file with given content and suffix."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def create_temp_binary_file(self, content: bytes, suffix: str) -> str:
        """Create a temporary file with binary content."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name

    # Test basic factory functionality
    
    def test_get_supported_extensions(self):
        """Test getting list of supported extensions."""
        extensions = self.factory.get_supported_extensions()
        assert '.csv' in extensions
        assert '.json' in extensions
        assert len(extensions) >= 2
    
    def test_is_supported_csv(self):
        """Test format support detection for CSV files."""
        assert self.factory.is_supported('test.csv')
        assert self.factory.is_supported('TEST.CSV')
        assert self.factory.is_supported('/path/to/file.csv')
    
    def test_is_supported_json(self):
        """Test format support detection for JSON files."""
        assert self.factory.is_supported('test.json')
        assert self.factory.is_supported('TEST.JSON')
        assert self.factory.is_supported('/path/to/file.json')
    
    def test_is_supported_unsupported_format(self):
        """Test format support detection for unsupported formats."""
        assert not self.factory.is_supported('test.xml')
        assert not self.factory.is_supported('test.txt')
        assert not self.factory.is_supported('test.yaml')
        assert not self.factory.is_supported('')
        assert not self.factory.is_supported(None)
    
    # Test parser creation
    
    def test_create_parser_csv(self):
        """Test creating CSV parser for CSV files."""
        csv_content = "name,age\nJohn,25\nJane,30"
        file_path = self.create_temp_file(csv_content, '.csv')
        
        parser = self.factory.create_parser(file_path)
        assert isinstance(parser, CSVParser)
    
    def test_create_parser_json(self):
        """Test creating JSON parser for JSON files."""
        json_content = '[{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]'
        file_path = self.create_temp_file(json_content, '.json')
        
        parser = self.factory.create_parser(file_path)
        assert isinstance(parser, JSONParser)
    
    def test_create_parser_with_kwargs(self):
        """Test creating parser with additional arguments."""
        csv_content = "name;age\nJohn;25\nJane;30"
        file_path = self.create_temp_file(csv_content, '.csv')
        
        parser = self.factory.create_parser(file_path, delimiter=';')
        assert isinstance(parser, CSVParser)
        assert parser.delimiter == ';'
    
    def test_create_parser_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            self.factory.create_parser('nonexistent.csv')
    
    def test_create_parser_empty_path(self):
        """Test error handling for empty file path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            self.factory.create_parser('')
    
    def test_create_parser_unsupported_format(self):
        """Test error handling for unsupported file formats."""
        xml_content = '<?xml version="1.0"?><root></root>'
        file_path = self.create_temp_file(xml_content, '.xml')
        
        with pytest.raises(UnsupportedFormatError) as exc_info:
            self.factory.create_parser(file_path)
        
        error = exc_info.value
        assert file_path in str(error)
        assert '.csv' in str(error)
        assert '.json' in str(error)
    
    def test_create_parser_invalid_format_content(self):
        """Test error handling when file extension doesn't match content."""
        # Create a file with .csv extension but empty content (which should fail validation)
        file_path = self.create_temp_file('', '.csv')
        
        with pytest.raises(DataParsingError, match="File format validation failed"):
            self.factory.create_parser(file_path)
    
    # Test file parsing integration
    
    def test_parse_file_csv(self):
        """Test parsing CSV file through factory."""
        csv_content = "name,age,city\nJohn,25,NYC\nJane,30,LA"
        file_path = self.create_temp_file(csv_content, '.csv')
        
        data = self.factory.parse_file(file_path)
        
        assert len(data) == 2
        assert data[0] == {'name': 'John', 'age': '25', 'city': 'NYC'}
        assert data[1] == {'name': 'Jane', 'age': '30', 'city': 'LA'}
    
    def test_parse_file_json_array(self):
        """Test parsing JSON array file through factory."""
        json_content = '[{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]'
        file_path = self.create_temp_file(json_content, '.json')
        
        data = self.factory.parse_file(file_path)
        
        assert len(data) == 2
        assert data[0] == {'name': 'John', 'age': 25}
        assert data[1] == {'name': 'Jane', 'age': 30}
    
    def test_parse_file_json_object(self):
        """Test parsing single JSON object file through factory."""
        json_content = '{"name": "John", "age": 25, "city": "NYC"}'
        file_path = self.create_temp_file(json_content, '.json')
        
        data = self.factory.parse_file(file_path)
        
        assert len(data) == 1
        assert data[0] == {'name': 'John', 'age': 25, 'city': 'NYC'}
    
    def test_parse_file_with_kwargs(self):
        """Test parsing file with parser-specific arguments."""
        json_content = '{"user": {"name": "John", "details": {"age": 25}}}'
        file_path = self.create_temp_file(json_content, '.json')
        
        # Parse with flattening enabled
        data = self.factory.parse_file(file_path, flatten_nested=True)
        
        assert len(data) == 1
        assert 'user.name' in data[0]
        assert 'user.details.age' in data[0]
    
    # Test parser registration
    
    def test_register_parser(self):
        """Test registering a new parser type."""
        class MockParser(DataParser):
            def parse(self, file_path: str):
                return [{'mock': 'data'}]
            
            def validate_format(self, file_path: str) -> bool:
                return True
        
        self.factory.register_parser('.mock', MockParser)
        
        assert '.mock' in self.factory.get_supported_extensions()
        assert self.factory.is_supported('test.mock')
    
    def test_register_parser_invalid_extension(self):
        """Test error handling for invalid extension format."""
        class MockParser(DataParser):
            def parse(self, file_path: str):
                return []
            def validate_format(self, file_path: str) -> bool:
                return True
        
        with pytest.raises(ValueError, match="Extension must start with"):
            self.factory.register_parser('mock', MockParser)
    
    def test_register_parser_invalid_class(self):
        """Test error handling for invalid parser class."""
        class NotAParser:
            pass
        
        with pytest.raises(ValueError, match="must implement DataParser interface"):
            self.factory.register_parser('.mock', NotAParser)
    
    # Test error scenarios
    
    def test_malformed_csv_parsing(self):
        """Test error handling for malformed CSV files."""
        malformed_csv = "name,age\nJohn,25,extra_field\nJane"  # Inconsistent columns
        file_path = self.create_temp_file(malformed_csv, '.csv')
        
        # Should still create parser but parsing might fail
        parser = self.factory.create_parser(file_path)
        assert isinstance(parser, CSVParser)
        
        # Parsing should handle the malformed content gracefully
        data = self.factory.parse_file(file_path)
        assert len(data) >= 1  # Should parse at least the valid rows
    
    def test_malformed_json_parsing(self):
        """Test error handling for malformed JSON files."""
        malformed_json = '{"name": "John", "age": 25'  # Missing closing brace
        file_path = self.create_temp_file(malformed_json, '.json')
        
        # Should fail at parser creation due to format validation
        with pytest.raises(DataParsingError):
            self.factory.create_parser(file_path)
    
    def test_empty_file_handling(self):
        """Test handling of empty files."""
        # Empty CSV
        empty_csv_path = self.create_temp_file('', '.csv')
        with pytest.raises(DataParsingError):
            self.factory.create_parser(empty_csv_path)
        
        # Empty JSON
        empty_json_path = self.create_temp_file('', '.json')
        with pytest.raises(DataParsingError):
            self.factory.create_parser(empty_json_path)


class TestFactoryConvenienceFunctions:
    """Test suite for factory convenience functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_file(self, content: str, suffix: str, encoding: str = 'utf-8') -> str:
        """Create a temporary file with given content and suffix."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def test_create_parser_function(self):
        """Test create_parser convenience function."""
        csv_content = "name,age\nJohn,25"
        file_path = self.create_temp_file(csv_content, '.csv')
        
        parser = create_parser(file_path)
        assert isinstance(parser, CSVParser)
    
    def test_parse_file_function(self):
        """Test parse_file convenience function."""
        json_content = '{"name": "John", "age": 25}'
        file_path = self.create_temp_file(json_content, '.json')
        
        data = parse_file(file_path)
        assert len(data) == 1
        assert data[0] == {'name': 'John', 'age': 25}
    
    def test_get_supported_extensions_function(self):
        """Test get_supported_extensions convenience function."""
        extensions = get_supported_extensions()
        assert '.csv' in extensions
        assert '.json' in extensions
    
    def test_is_supported_function(self):
        """Test is_supported convenience function."""
        assert is_supported('test.csv')
        assert is_supported('test.json')
        assert not is_supported('test.xml')


class TestUnsupportedFormatError:
    """Test suite for UnsupportedFormatError exception."""
    
    def test_error_message_with_supported_formats(self):
        """Test error message includes supported formats."""
        error = UnsupportedFormatError('test.xml', ['.csv', '.json'])
        
        assert 'test.xml' in str(error)
        assert '.csv' in str(error)
        assert '.json' in str(error)
        assert 'Supported formats' in str(error)
    
    def test_error_message_without_supported_formats(self):
        """Test error message without supported formats list."""
        error = UnsupportedFormatError('test.xml')
        
        assert 'test.xml' in str(error)
        assert 'Unsupported file format' in str(error)
    
    def test_error_attributes(self):
        """Test error attributes are set correctly."""
        supported_formats = ['.csv', '.json']
        error = UnsupportedFormatError('test.xml', supported_formats)
        
        assert error.file_path == 'test.xml'
        assert error.supported_formats == supported_formats


class TestFactoryIntegrationScenarios:
    """Test suite for complex integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = ParserFactory()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_file(self, content: str, suffix: str, encoding: str = 'utf-8') -> str:
        """Create a temporary file with given content and suffix."""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def test_mixed_file_processing(self):
        """Test processing multiple files of different formats."""
        # Create test files
        csv_content = "name,age\nJohn,25\nJane,30"
        csv_file = self.create_temp_file(csv_content, '.csv')
        
        json_content = '[{"name": "Bob", "age": 35}]'
        json_file = self.create_temp_file(json_content, '.json')
        
        # Process both files
        csv_data = self.factory.parse_file(csv_file)
        json_data = self.factory.parse_file(json_file)
        
        assert len(csv_data) == 2
        assert len(json_data) == 1
        assert csv_data[0]['name'] == 'John'
        assert json_data[0]['name'] == 'Bob'
    
    def test_case_insensitive_extension_handling(self):
        """Test that file extensions are handled case-insensitively."""
        csv_content = "name,age\nJohn,25"
        
        # Test various case combinations
        for extension in ['.CSV', '.Csv', '.cSv']:
            file_path = self.create_temp_file(csv_content, extension)
            
            assert self.factory.is_supported(file_path)
            parser = self.factory.create_parser(file_path)
            assert isinstance(parser, CSVParser)
            
            data = self.factory.parse_file(file_path)
            assert len(data) == 1
    
    def test_complex_file_paths(self):
        """Test handling of complex file paths."""
        csv_content = "name,age\nJohn,25"
        
        # Create file in a subdirectory-like name
        file_path = self.create_temp_file(csv_content, '.csv')
        
        # Test with the actual path
        assert self.factory.is_supported(file_path)
        data = self.factory.parse_file(file_path)
        assert len(data) == 1
    
    def test_parser_reuse(self):
        """Test that factory can be reused for multiple operations."""
        csv_content1 = "name,age\nJohn,25"
        csv_content2 = "name,city\nJane,NYC"
        
        file1 = self.create_temp_file(csv_content1, '.csv')
        file2 = self.create_temp_file(csv_content2, '.csv')
        
        # Use same factory instance for multiple files
        data1 = self.factory.parse_file(file1)
        data2 = self.factory.parse_file(file2)
        
        assert data1[0]['name'] == 'John'
        assert data2[0]['name'] == 'Jane'
        assert data1[0]['age'] == '25'
        assert data2[0]['city'] == 'NYC'