"""
Tests for the type check validation processor.
"""

from datetime import datetime

from src.policy_dq.validators.processors.type_check import TypeCheckProcessor
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity


class TestTypeCheckProcessor:
    """Test cases for the TypeCheckProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = TypeCheckProcessor()
    
    def create_rule(self, field_name: str, expected_type: str) -> ValidationRule:
        """Helper to create a type check rule."""
        return ValidationRule(
            name=f"{field_name}_type_check",
            rule_type=RuleType.TYPE_CHECK,
            field=field_name,
            parameters={"type": expected_type},
            severity=ValidationSeverity.ERROR
        )
    
    def test_can_process_type_check_rule(self):
        """Test that processor can handle type check rules."""
        rule = self.create_rule("email", "string")
        assert self.processor.can_process(rule) is True
    
    def test_can_process_other_rule_types(self):
        """Test that processor rejects other rule types."""
        other_rule = ValidationRule(
            name="required_field",
            rule_type=RuleType.REQUIRED_FIELD,
            field="email",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        assert self.processor.can_process(other_rule) is False
    
    def test_process_record_field_missing(self):
        """Test validation fails when field is missing."""
        rule = self.create_rule("email", "string")
        record = {"name": "John Doe"}  # email field missing
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "is missing for type check" in result.message
    
    def test_process_record_field_none(self):
        """Test validation passes when field is None (skipped)."""
        rule = self.create_rule("email", "string")
        record = {"email": None}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is True
        assert "is None, skipping type check" in result.message
    
    # String type validation tests
    def test_validate_string_valid(self):
        """Test string validation with valid string values."""
        rule = self.create_rule("name", "string")
        
        test_cases = [
            {"name": "John Doe"},
            {"name": ""},
            {"name": "123"},
            {"name": "special@chars!"},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for value: {record['name']}"
    
    def test_validate_string_invalid(self):
        """Test string validation with invalid values."""
        rule = self.create_rule("name", "string")
        
        test_cases = [
            {"name": 123},
            {"name": 45.67},
            {"name": True},
            {"name": []},
            {"name": {}},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['name']}"
            assert "Expected string" in result.message
    
    # Integer type validation tests
    def test_validate_int_valid(self):
        """Test integer validation with valid integer values."""
        rule = self.create_rule("age", "int")
        
        test_cases = [
            {"age": 25},
            {"age": 0},
            {"age": -10},
            {"age": "42"},
            {"age": "-5"},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for value: {record['age']}"
    
    def test_validate_int_invalid(self):
        """Test integer validation with invalid values."""
        rule = self.create_rule("age", "int")
        
        test_cases = [
            {"age": 25.5},
            {"age": "25.5"},
            {"age": "not_a_number"},
            {"age": True},  # bool is not considered int
            {"age": []},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['age']}"
    
    # Float type validation tests
    def test_validate_float_valid(self):
        """Test float validation with valid float values."""
        rule = self.create_rule("price", "float")
        
        test_cases = [
            {"price": 25.99},
            {"price": 25},      # int is valid for float
            {"price": 0},
            {"price": -10.5},
            {"price": "42.5"},
            {"price": "25"},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for value: {record['price']}"
    
    def test_validate_float_invalid(self):
        """Test float validation with invalid values."""
        rule = self.create_rule("price", "float")
        
        test_cases = [
            {"price": "not_a_number"},
            {"price": True},  # bool is not considered float
            {"price": []},
            {"price": {}},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['price']}"
    
    # Boolean type validation tests
    def test_validate_bool_valid(self):
        """Test boolean validation with valid boolean values."""
        rule = self.create_rule("active", "bool")
        
        test_cases = [
            {"active": True},
            {"active": False},
            {"active": "true"},
            {"active": "false"},
            {"active": "yes"},
            {"active": "no"},
            {"active": "1"},
            {"active": "0"},
            {"active": "on"},
            {"active": "off"},
            {"active": 1},
            {"active": 0},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for value: {record['active']}"
    
    def test_validate_bool_invalid(self):
        """Test boolean validation with invalid values."""
        rule = self.create_rule("active", "bool")
        
        test_cases = [
            {"active": "maybe"},
            {"active": 2},
            {"active": -1},
            {"active": 1.5},
            {"active": []},
            {"active": {}},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['active']}"
    
    # Date type validation tests
    def test_validate_date_valid(self):
        """Test date validation with valid date values."""
        rule = self.create_rule("created_at", "date")
        
        test_cases = [
            {"created_at": datetime(2023, 12, 25)},
            {"created_at": "2023-12-25"},
            {"created_at": "12/25/2023"},
            {"created_at": "25/12/2023"},
            {"created_at": "2023-12-25 14:30:00"},
            {"created_at": "2023-12-25T14:30:00"},
            {"created_at": "2023-12-25T14:30:00Z"},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for value: {record['created_at']}"
    
    def test_validate_date_invalid(self):
        """Test date validation with invalid values."""
        rule = self.create_rule("created_at", "date")
        
        test_cases = [
            {"created_at": "not_a_date"},
            {"created_at": "2023-13-25"},  # Invalid month
            {"created_at": "25-12-2023"},  # Wrong format
            {"created_at": 123456789},
            {"created_at": []},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['created_at']}"
    
    # None type validation tests
    def test_validate_none_valid(self):
        """Test None validation with None value."""
        rule = self.create_rule("optional_field", "none")
        record = {"optional_field": None}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is True
    
    def test_validate_none_invalid(self):
        """Test None validation with non-None values."""
        rule = self.create_rule("optional_field", "none")
        
        test_cases = [
            {"optional_field": ""},
            {"optional_field": 0},
            {"optional_field": False},
            {"optional_field": []},
        ]
        
        for record in test_cases:
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for value: {record['optional_field']}"
    
    def test_unsupported_type(self):
        """Test validation with unsupported type."""
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.TYPE_CHECK,
            field="test_field",
            parameters={"type": "unsupported_type"},
            severity=ValidationSeverity.ERROR
        )
        record = {"test_field": "value"}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "Unsupported type 'unsupported_type'" in result.message
    
    def test_missing_type_parameter(self):
        """Test validation with missing type parameter (defaults to string)."""
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.TYPE_CHECK,
            field="test_field",
            parameters={},  # No type parameter
            severity=ValidationSeverity.ERROR
        )
        record = {"test_field": "string_value"}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is True  # Should default to string type
    
    def test_process_dataset_multiple_records(self):
        """Test processing multiple records in a dataset."""
        rule = self.create_rule("age", "int")
        records = [
            {"age": 25},        # Valid
            {"age": "30"},      # Valid (string that can be converted)
            {"age": 25.5},      # Invalid (float)
            {"age": "abc"},     # Invalid (non-numeric string)
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 4
        assert results[0].passed is True
        assert results[1].passed is True
        assert results[2].passed is False
        assert results[3].passed is False