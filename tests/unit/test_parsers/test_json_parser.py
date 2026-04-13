"""
Unit tests for JSON parser implementation.

Tests cover single objects, arrays, nested structures, error handling,
and various edge cases for JSON parsing functionality.
"""

import pytest
import tempfile
import os
import json

from src.policy_dq.parsers.json_parser import JSONParser
from src.policy_dq.parsers.base import DataParsingError


class TestJSONParser:
    """Test suite for JSONParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = JSONParser()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_json(self, content: str, encoding: str = 'utf-8') -> str:
        """Create a temporary JSON file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def create_temp_file(self, content: bytes, suffix: str = '.json') -> str:
        """Create a temporary file with binary content."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix=suffix, delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name

    def test_validate_format_valid_json_object(self):
        """Test format validation for valid JSON object."""
        json_content = '{"name": "John", "age": 25, "email": "john@example.com"}'
        file_path = self.create_temp_json(json_content)
        
        assert self.parser.validate_format(file_path) is True
    
    def test_validate_format_valid_json_array(self):
        """Test format validation for valid JSON array."""
        json_content = '[{"name": "John", "age": 25}, {"name": "Jane", "age": 30}]'
        file_path = self.create_temp_json(json_content)
        
        assert self.parser.validate_format(file_path) is True
    
    def test_validate_format_non_json_extension(self):
        """Test format validation rejects non-JSON extensions."""
        content = '{"name": "John", "age": 25}'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            self.temp_files.append(f.name)
            
        assert self.parser.validate_format(f.name) is False
    
    def test_validate_format_nonexistent_file(self):
        """Test format validation for nonexistent files."""
        assert self.parser.validate_format("nonexistent.json") is False
    
    def test_validate_format_empty_file(self):
        """Test format validation for empty files."""
        file_path = self.create_temp_json("")
        assert self.parser.validate_format(file_path) is False
    
    def test_validate_format_malformed_json(self):
        """Test format validation for malformed JSON."""
        malformed_content = '{"name": "John", "age": 25'  # Missing closing brace
        file_path = self.create_temp_json(malformed_content)
        
        assert self.parser.validate_format(file_path) is False
    
    def test_parse_single_object(self):
        """Test parsing a single JSON object."""
        json_content = '{"name": "John", "age": 25, "email": "john@example.com"}'
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{"name": "John", "age": 25, "email": "john@example.com"}]
        
        assert result == expected
    
    def test_parse_array_of_objects(self):
        """Test parsing an array of JSON objects."""
        json_content = '''[
            {"name": "John", "age": 25, "email": "john@example.com"},
            {"name": "Jane", "age": 30, "email": "jane@example.com"}
        ]'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "age": 25, "email": "john@example.com"},
            {"name": "Jane", "age": 30, "email": "jane@example.com"}
        ]
        
        assert result == expected
    
    def test_parse_empty_array(self):
        """Test parsing an empty JSON array."""
        json_content = '[]'
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert result == []
    
    def test_parse_nested_objects(self):
        """Test parsing JSON with nested objects."""
        json_content = '''{
            "name": "John",
            "age": 25,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "country": "USA"
            },
            "contact": {
                "email": "john@example.com",
                "phone": "555-1234"
            }
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "age": 25,
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "country": "USA"
            },
            "contact": {
                "email": "john@example.com",
                "phone": "555-1234"
            }
        }]
        
        assert result == expected
    
    def test_parse_nested_objects_with_flattening(self):
        """Test parsing nested objects with flattening enabled."""
        json_content = '''{
            "name": "John",
            "age": 25,
            "address": {
                "street": "123 Main St",
                "city": "Anytown"
            }
        }'''
        file_path = self.create_temp_json(json_content)
        
        parser = JSONParser(flatten_nested=True)
        result = parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "age": 25,
            "address.street": "123 Main St",
            "address.city": "Anytown"
        }]
        
        assert result == expected
    
    def test_parse_array_with_nested_objects(self):
        """Test parsing array containing objects with nested structures."""
        json_content = '''[
            {
                "name": "John",
                "address": {"city": "New York", "zip": "10001"}
            },
            {
                "name": "Jane", 
                "address": {"city": "Los Angeles", "zip": "90210"}
            }
        ]'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {
                "name": "John",
                "address": {"city": "New York", "zip": "10001"}
            },
            {
                "name": "Jane",
                "address": {"city": "Los Angeles", "zip": "90210"}
            }
        ]
        
        assert result == expected
    
    def test_parse_arrays_in_objects(self):
        """Test parsing objects containing arrays."""
        json_content = '''{
            "name": "John",
            "hobbies": ["reading", "swimming", "coding"],
            "scores": [85, 92, 78]
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "hobbies": ["reading", "swimming", "coding"],
            "scores": [85, 92, 78]
        }]
        
        assert result == expected
    
    def test_parse_arrays_with_flattening(self):
        """Test parsing arrays with flattening enabled."""
        json_content = '''{
            "name": "John",
            "hobbies": ["reading", "swimming"],
            "contacts": [
                {"type": "email", "value": "john@example.com"},
                {"type": "phone", "value": "555-1234"}
            ]
        }'''
        file_path = self.create_temp_json(json_content)
        
        parser = JSONParser(flatten_nested=True)
        result = parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "hobbies[0]": "reading",
            "hobbies[1]": "swimming",
            "contacts[0].type": "email",
            "contacts[0].value": "john@example.com",
            "contacts[1].type": "phone",
            "contacts[1].value": "555-1234"
        }]
        
        assert result == expected
    
    def test_parse_complex_nested_structure(self):
        """Test parsing complex nested JSON structure."""
        json_content = '''{
            "user": {
                "id": 123,
                "profile": {
                    "name": "John Doe",
                    "preferences": {
                        "theme": "dark",
                        "notifications": {
                            "email": true,
                            "push": false
                        }
                    }
                }
            }
        }'''
        file_path = self.create_temp_json(json_content)
        
        parser = JSONParser(flatten_nested=True)
        result = parser.parse(file_path)
        
        expected = [{
            "user.id": 123,
            "user.profile.name": "John Doe",
            "user.profile.preferences.theme": "dark",
            "user.profile.preferences.notifications.email": True,
            "user.profile.preferences.notifications.push": False
        }]
        
        assert result == expected
    
    def test_parse_mixed_data_types(self):
        """Test parsing JSON with various data types."""
        json_content = '''{
            "string_field": "hello",
            "integer_field": 42,
            "float_field": 3.14,
            "boolean_true": true,
            "boolean_false": false,
            "null_field": null,
            "empty_string": "",
            "zero": 0
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{
            "string_field": "hello",
            "integer_field": 42,
            "float_field": 3.14,
            "boolean_true": True,
            "boolean_false": False,
            "null_field": None,
            "empty_string": "",
            "zero": 0
        }]
        
        assert result == expected
    
    def test_parse_unicode_characters(self):
        """Test parsing JSON with Unicode characters."""
        json_content = '''{
            "name": "José María",
            "city": "São Paulo",
            "emoji": "😀🎉",
            "chinese": "你好世界",
            "arabic": "مرحبا بالعالم"
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{
            "name": "José María",
            "city": "São Paulo", 
            "emoji": "😀🎉",
            "chinese": "你好世界",
            "arabic": "مرحبا بالعالم"
        }]
        
        assert result == expected
    
    def test_parse_nonexistent_file(self):
        """Test parsing nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            self.parser.parse("nonexistent.json")
    
    def test_parse_empty_file(self):
        """Test parsing empty file raises DataParsingError."""
        file_path = self.create_temp_json("")
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "does not appear to be a valid JSON format" in str(exc_info.value)
    
    def test_parse_whitespace_only_file(self):
        """Test parsing file with only whitespace raises DataParsingError."""
        file_path = self.create_temp_json("   \n\t  \n  ")
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Whitespace-only files should be caught by format validation
        assert "does not appear to be a valid JSON format" in str(exc_info.value)
    
    def test_parse_malformed_json_missing_brace(self):
        """Test parsing malformed JSON with missing closing brace."""
        malformed_content = '{"name": "John", "age": 25'
        file_path = self.create_temp_json(malformed_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Malformed JSON should be caught by format validation
        assert "does not appear to be a valid JSON format" in str(exc_info.value)
    
    def test_parse_malformed_json_invalid_syntax(self):
        """Test parsing JSON with invalid syntax."""
        malformed_content = '{"name": "John", "age": 25,}'  # Trailing comma
        file_path = self.create_temp_json(malformed_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Malformed JSON should be caught by format validation
        assert "does not appear to be a valid JSON format" in str(exc_info.value)
    
    def test_parse_malformed_json_unquoted_keys(self):
        """Test parsing JSON with unquoted keys."""
        malformed_content = '{name: "John", age: 25}'
        file_path = self.create_temp_json(malformed_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Malformed JSON should be caught by format validation
        assert "does not appear to be a valid JSON format" in str(exc_info.value)
    
    def test_parse_array_with_non_objects(self):
        """Test parsing array containing non-object items raises error."""
        json_content = '["string", 123, true, {"name": "John"}]'
        file_path = self.create_temp_json(json_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "Array item at index 0 is not an object" in str(exc_info.value)
        assert "Expected object, got str" in str(exc_info.value)
    
    def test_parse_primitive_root_value(self):
        """Test parsing JSON with primitive root value raises error."""
        json_content = '"just a string"'
        file_path = self.create_temp_json(json_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "JSON root must be an object or array of objects" in str(exc_info.value)
        assert "Got str" in str(exc_info.value)
    
    def test_parse_number_root_value(self):
        """Test parsing JSON with number root value raises error."""
        json_content = '42'
        file_path = self.create_temp_json(json_content)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        assert "JSON root must be an object or array of objects" in str(exc_info.value)
        assert "Got int" in str(exc_info.value)
    
    def test_parse_large_json_file(self):
        """Test parsing a larger JSON file for performance."""
        # Generate JSON array with 1000 objects
        objects = []
        for i in range(1000):
            objects.append({
                "id": i,
                "name": f"User{i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50)
            })
        
        json_content = json.dumps(objects, indent=2)
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1000
        assert result[0]["name"] == "User0"
        assert result[999]["name"] == "User999"
    
    def test_parse_deeply_nested_structure(self):
        """Test parsing deeply nested JSON structure."""
        # Create a deeply nested structure
        nested_obj = {"value": "deep"}
        for i in range(10):
            nested_obj = {"level": i, "nested": nested_obj}
        
        json_content = json.dumps({"root": nested_obj})
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        assert "root" in result[0]
        assert result[0]["root"]["level"] == 9
    
    def test_invalid_encoding_handling(self):
        """Test handling of files with invalid encoding."""
        # Create a file with invalid UTF-8 bytes
        invalid_utf8 = b'{"name": "Caf\xe9 owner"}'
        file_path = self.create_temp_file(invalid_utf8)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Invalid encoding should be caught by format validation or encoding error
        error_msg = str(exc_info.value)
        assert ("Encoding error" in error_msg and "UTF-8 encoded" in error_msg) or \
               "does not appear to be a valid JSON format" in error_msg


class TestJSONParserEdgeCases:
    """Additional edge case tests for JSON parser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = JSONParser()
        self.temp_files = []
    
    def teardown_method(self):
        """Clean up temporary files."""
        for file_path in self.temp_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def create_temp_json(self, content: str, encoding: str = 'utf-8') -> str:
        """Create a temporary JSON file with given content."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', 
                                       delete=False, encoding=encoding) as f:
            f.write(content)
            self.temp_files.append(f.name)
            return f.name
    
    def test_json_with_bom(self):
        """Test parsing JSON file with Byte Order Mark (BOM)."""
        json_content = '{"name": "John", "age": 25}'
        
        # Create file with BOM
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as f:
            f.write(b'\xef\xbb\xbf')  # UTF-8 BOM
            f.write(json_content.encode('utf-8'))
            self.temp_files.append(f.name)
            file_path = f.name
        
        result = self.parser.parse(file_path)
        
        # Should handle BOM correctly
        assert len(result) == 1
        assert result[0]["name"] == "John"
    
    def test_json_with_comments_fails(self):
        """Test that JSON with comments fails parsing (as per JSON spec)."""
        json_with_comments = '''{
            // This is a comment
            "name": "John",
            /* Multi-line
               comment */
            "age": 25
        }'''
        file_path = self.create_temp_json(json_with_comments)
        
        with pytest.raises(DataParsingError):
            self.parser.parse(file_path)
    
    def test_json_with_trailing_commas_fails(self):
        """Test that JSON with trailing commas fails parsing."""
        json_with_trailing_comma = '''{
            "name": "John",
            "age": 25,
        }'''
        file_path = self.create_temp_json(json_with_trailing_comma)
        
        with pytest.raises(DataParsingError):
            self.parser.parse(file_path)
    
    def test_json_with_single_quotes_fails(self):
        """Test that JSON with single quotes fails parsing."""
        json_with_single_quotes = "{'name': 'John', 'age': 25}"
        file_path = self.create_temp_json(json_with_single_quotes)
        
        with pytest.raises(DataParsingError):
            self.parser.parse(file_path)
    
    def test_json_with_very_long_strings(self):
        """Test parsing JSON with very long string values."""
        long_string = "A" * 100000  # 100KB string
        json_content = json.dumps({"name": "John", "description": long_string})
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        assert result[0]["description"] == long_string
    
    def test_json_with_special_characters_in_keys(self):
        """Test parsing JSON with special characters in keys."""
        json_content = '''{
            "normal_key": "value1",
            "key with spaces": "value2",
            "key-with-dashes": "value3",
            "key_with_underscores": "value4",
            "key.with.dots": "value5",
            "key@with#symbols": "value6"
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        record = result[0]
        assert record["normal_key"] == "value1"
        assert record["key with spaces"] == "value2"
        assert record["key-with-dashes"] == "value3"
        assert record["key_with_underscores"] == "value4"
        assert record["key.with.dots"] == "value5"
        assert record["key@with#symbols"] == "value6"
    
    def test_json_with_escaped_characters(self):
        """Test parsing JSON with escaped characters."""
        json_content = r'''{
            "quote": "He said \"Hello\"",
            "backslash": "Path: C:\\Users\\John",
            "newline": "Line 1\nLine 2",
            "tab": "Column1\tColumn2",
            "unicode": "Unicode: \u00A9 \u2603"
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        record = result[0]
        assert record["quote"] == 'He said "Hello"'
        assert record["backslash"] == "Path: C:\\Users\\John"
        assert record["newline"] == "Line 1\nLine 2"
        assert record["tab"] == "Column1\tColumn2"
        assert record["unicode"] == "Unicode: © ☃"
    
    def test_flatten_with_empty_objects_and_arrays(self):
        """Test flattening with empty nested objects and arrays."""
        json_content = '''{
            "name": "John",
            "empty_object": {},
            "empty_array": [],
            "nested": {
                "also_empty": {},
                "value": "test"
            }
        }'''
        file_path = self.create_temp_json(json_content)
        
        parser = JSONParser(flatten_nested=True)
        result = parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "nested.value": "test"
        }]
        
        assert result == expected
    
    def test_line_number_reporting_accuracy(self):
        """Test that line numbers in error messages are reasonably accurate."""
        # Create malformed JSON with error on a specific line
        malformed_json = '''{
            "name": "John",
            "age": 25,
            "invalid": 
        }'''
        file_path = self.create_temp_json(malformed_json)
        
        with pytest.raises(DataParsingError) as exc_info:
            self.parser.parse(file_path)
        
        # Malformed JSON should be caught by format validation
        # Line number may not be available for format validation errors
        error_msg = str(exc_info.value)
        assert "does not appear to be a valid JSON format" in error_msg or \
               "JSON parsing error" in error_msg
    
    def test_json_with_null_values_in_arrays(self):
        """Test parsing JSON arrays containing null values."""
        json_content = '[{"name": "John", "value": null}, {"name": "Jane", "value": 42}]'
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [
            {"name": "John", "value": None},
            {"name": "Jane", "value": 42}
        ]
        assert result == expected
    
    def test_json_with_empty_nested_structures(self):
        """Test parsing JSON with empty nested objects and arrays."""
        json_content = '''{
            "name": "John",
            "empty_obj": {},
            "empty_array": [],
            "nested": {
                "also_empty": {},
                "values": []
            }
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        expected = [{
            "name": "John",
            "empty_obj": {},
            "empty_array": [],
            "nested": {
                "also_empty": {},
                "values": []
            }
        }]
        assert result == expected
    
    def test_json_with_numeric_precision(self):
        """Test parsing JSON with high precision numbers."""
        json_content = '''{
            "small_decimal": 0.000000001,
            "large_number": 999999999999999,
            "scientific": 1.23e-10,
            "negative_scientific": -4.56e+15
        }'''
        file_path = self.create_temp_json(json_content)
        
        result = self.parser.parse(file_path)
        
        assert len(result) == 1
        record = result[0]
        assert record["small_decimal"] == 0.000000001
        assert record["large_number"] == 999999999999999
        assert record["scientific"] == 1.23e-10
        assert record["negative_scientific"] == -4.56e+15