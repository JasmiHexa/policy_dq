"""
Unit tests for base parser interface.

Tests the abstract base class and exception handling.
"""

import pytest
from src.policy_dq.parsers.base import DataParser, DataParsingError


class TestDataParsingError:
    """Test suite for DataParsingError exception."""
    
    def test_basic_error_message(self):
        """Test basic error message creation."""
        error = DataParsingError("Test error message")
        assert str(error) == "Test error message"
    
    def test_error_with_file_path(self):
        """Test error message with file path."""
        error = DataParsingError("Test error", file_path="/path/to/file.csv")
        expected = "Error parsing file '/path/to/file.csv': Test error"
        assert str(error) == expected
    
    def test_error_with_line_number(self):
        """Test error message with line number."""
        error = DataParsingError("Test error", line_number=42)
        expected = "Test error (line 42)"
        assert str(error) == expected
    
    def test_error_with_file_and_line(self):
        """Test error message with both file path and line number."""
        error = DataParsingError(
            "Test error", 
            file_path="/path/to/file.csv", 
            line_number=42
        )
        expected = "Error parsing file '/path/to/file.csv': Test error (line 42)"
        assert str(error) == expected
    
    def test_error_attributes(self):
        """Test that error attributes are properly set."""
        error = DataParsingError(
            "Test error",
            file_path="/path/to/file.csv",
            line_number=42
        )
        
        assert error.file_path == "/path/to/file.csv"
        assert error.line_number == 42


class TestDataParserInterface:
    """Test suite for DataParser abstract base class."""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that DataParser cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DataParser()
    
    def test_subclass_must_implement_parse(self):
        """Test that subclasses must implement parse method."""
        
        class IncompleteParser(DataParser):
            def validate_format(self, file_path: str) -> bool:
                return True
        
        with pytest.raises(TypeError):
            IncompleteParser()
    
    def test_subclass_must_implement_validate_format(self):
        """Test that subclasses must implement validate_format method."""
        
        class IncompleteParser(DataParser):
            def parse(self, file_path: str):
                return []
        
        with pytest.raises(TypeError):
            IncompleteParser()
    
    def test_complete_subclass_can_be_instantiated(self):
        """Test that complete subclasses can be instantiated."""
        
        class CompleteParser(DataParser):
            def parse(self, file_path: str):
                return []
            
            def validate_format(self, file_path: str) -> bool:
                return True
        
        # Should not raise any exception
        parser = CompleteParser()
        assert isinstance(parser, DataParser)
        assert parser.parse("test.csv") == []
        assert parser.validate_format("test.csv") is True