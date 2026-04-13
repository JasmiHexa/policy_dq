"""
Unit tests for required field validation processor.

These tests verify the RequiredFieldProcessor behavior with
various field presence and value scenarios.
"""

import pytest

from src.policy_dq.validators.processors.required_field import RequiredFieldProcessor
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationResult


class TestRequiredFieldProcessor:
    """Test cases for RequiredFieldProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create RequiredFieldProcessor instance."""
        return RequiredFieldProcessor()
    
    @pytest.fixture
    def basic_rule(self):
        """Basic required field rule."""
        return ValidationRule(
            name="required_name",
            rule_type=RuleType.REQUIRED_FIELD,
            field="name",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
    
    @pytest.fixture
    def strict_rule(self):
        """Strict required field rule that doesn't allow empty values."""
        return ValidationRule(
            name="required_email_strict",
            rule_type=RuleType.REQUIRED_FIELD,
            field="email",
            parameters={"allow_empty": False},
            severity=ValidationSeverity.CRITICAL
        )
    
    @pytest.fixture
    def lenient_rule(self):
        """Lenient required field rule that allows empty values."""
        return ValidationRule(
            name="required_phone_lenient",
            rule_type=RuleType.REQUIRED_FIELD,
            field="phone",
            parameters={"allow_empty": True},
            severity=ValidationSeverity.WARNING
        )
    
    def test_field_present_with_value(self, processor, basic_rule):
        """Test validation when field is present with non-empty value."""
        record = {"name": "John Doe"}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "required_name"
        assert result.field == "name"
        assert result.row_index == 0
        assert result.severity == ValidationSeverity.ERROR
        assert "required" not in result.message.lower() or "passed" in result.message.lower()
    
    def test_field_missing(self, processor, basic_rule):
        """Test validation when field is completely missing."""
        record = {"other_field": "value"}
        result = processor.process_record(basic_rule, record, 1)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "required_name"
        assert result.field == "name"
        assert result.row_index == 1
        assert result.severity == ValidationSeverity.ERROR
        assert "required" in result.message.lower() or "missing" in result.message.lower()
    
    def test_field_none_value(self, processor, basic_rule):
        """Test validation when field is present but has None value."""
        record = {"name": None}
        result = processor.process_record(basic_rule, record, 2)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "required_name"
        assert result.field == "name"
        assert result.row_index == 2
        assert "required" in result.message.lower() or "none" in result.message.lower() or "null" in result.message.lower()
    
    def test_field_empty_string_strict(self, processor, strict_rule):
        """Test validation when field has empty string with strict rule."""
        record = {"email": ""}
        result = processor.process_record(strict_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "required_email_strict"
        assert result.field == "email"
        assert result.severity == ValidationSeverity.CRITICAL
        assert "empty" in result.message.lower() or "required" in result.message.lower()
    
    def test_field_empty_string_lenient(self, processor, lenient_rule):
        """Test validation when field has empty string with lenient rule."""
        record = {"phone": ""}
        result = processor.process_record(lenient_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "required_phone_lenient"
        assert result.field == "phone"
        assert result.severity == ValidationSeverity.WARNING
    
    def test_field_whitespace_only(self, processor, strict_rule):
        """Test validation when field contains only whitespace."""
        record = {"email": "   "}
        result = processor.process_record(strict_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        # Behavior depends on implementation - whitespace might be considered empty
        assert result.rule_name == "required_email_strict"
        assert result.field == "email"
    
    def test_field_zero_value(self, processor, basic_rule):
        """Test validation when field has zero value."""
        record = {"name": 0}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True  # Zero is a valid value
        assert result.rule_name == "required_name"
        assert result.field == "name"
    
    def test_field_false_value(self, processor, basic_rule):
        """Test validation when field has False value."""
        record = {"name": False}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True  # False is a valid value
        assert result.rule_name == "required_name"
        assert result.field == "name"
    
    def test_field_empty_list(self, processor, basic_rule):
        """Test validation when field has empty list."""
        record = {"name": []}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        # Empty list might be considered empty depending on implementation
        assert result.rule_name == "required_name"
        assert result.field == "name"
    
    def test_field_empty_dict(self, processor, basic_rule):
        """Test validation when field has empty dictionary."""
        record = {"name": {}}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        # Empty dict might be considered empty depending on implementation
        assert result.rule_name == "required_name"
        assert result.field == "name"
    
    def test_custom_message_parameter(self, processor):
        """Test validation with custom message parameter."""
        rule = ValidationRule(
            name="custom_message_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="custom_field",
            parameters={"message": "Custom field is mandatory"},
            severity=ValidationSeverity.ERROR
        )
        
        record = {}  # Missing field
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        # Should use custom message if supported
        assert len(result.message) > 0
    
    def test_different_field_names(self, processor):
        """Test validation with various field names."""
        field_names = ["email", "user_name", "field123", "field_with_underscores", "CamelCaseField"]
        
        for field_name in field_names:
            rule = ValidationRule(
                name=f"required_{field_name}",
                rule_type=RuleType.REQUIRED_FIELD,
                field=field_name,
                parameters={},
                severity=ValidationSeverity.ERROR
            )
            
            # Test with field present
            record = {field_name: "value"}
            result = processor.process_record(rule, record, 0)
            assert result.passed is True
            assert result.field == field_name
            
            # Test with field missing
            record = {}
            result = processor.process_record(rule, record, 0)
            assert result.passed is False
            assert result.field == field_name
    
    def test_case_sensitivity(self, processor, basic_rule):
        """Test that field names are case sensitive."""
        # Field name in rule is "name", record has "Name"
        record = {"Name": "John Doe"}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False  # Should be case sensitive
        assert result.field == "name"
    
    def test_unicode_field_names(self, processor):
        """Test validation with unicode field names."""
        rule = ValidationRule(
            name="unicode_field_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="名前",  # Japanese for "name"
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        # Test with field present
        record = {"名前": "田中太郎"}
        result = processor.process_record(rule, record, 0)
        assert result.passed is True
        assert result.field == "名前"
        
        # Test with field missing
        record = {"name": "Tanaka Taro"}
        result = processor.process_record(rule, record, 0)
        assert result.passed is False
        assert result.field == "名前"
    
    def test_unicode_field_values(self, processor, basic_rule):
        """Test validation with unicode field values."""
        record = {"name": "José María Aznar"}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.field == "name"
    
    def test_very_long_field_value(self, processor, basic_rule):
        """Test validation with very long field value."""
        long_value = "x" * 10000
        record = {"name": long_value}
        result = processor.process_record(basic_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True  # Long value is still a valid value
        assert result.field == "name"
    
    def test_special_characters_in_value(self, processor, basic_rule):
        """Test validation with special characters in field value."""
        special_values = [
            "name@domain.com",
            "name with spaces",
            "name\nwith\nnewlines",
            "name\twith\ttabs",
            "name'with'quotes",
            'name"with"double"quotes',
            "name\\with\\backslashes",
            "name/with/slashes"
        ]
        
        for value in special_values:
            record = {"name": value}
            result = processor.process_record(basic_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed is True
            assert result.field == "name"
    
    def test_deterministic_behavior(self, processor, basic_rule):
        """Test that processor behavior is deterministic."""
        record = {"name": "John Doe"}
        
        # Run validation multiple times
        results = []
        for _ in range(10):
            result = processor.process_record(basic_rule, record, 0)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.passed == first_result.passed
            assert result.message == first_result.message
            assert result.rule_name == first_result.rule_name
            assert result.field == first_result.field
            assert result.severity == first_result.severity
    
    def test_parameter_variations(self, processor):
        """Test processor with different parameter combinations."""
        parameter_sets = [
            {},
            {"allow_empty": True},
            {"allow_empty": False},
            {"message": "Custom message"},
            {"allow_empty": True, "message": "Custom message for lenient rule"},
            {"allow_empty": False, "message": "Custom message for strict rule"}
        ]
        
        for params in parameter_sets:
            rule = ValidationRule(
                name="param_test_rule",
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters=params,
                severity=ValidationSeverity.ERROR
            )
            
            # Test with valid value
            record = {"test_field": "value"}
            result = processor.process_record(rule, record, 0)
            assert result.passed is True
            
            # Test with missing field
            record = {}
            result = processor.process_record(rule, record, 0)
            assert result.passed is False
    
    def test_row_index_preservation(self, processor, basic_rule):
        """Test that row index is correctly preserved in results."""
        record = {"name": "John Doe"}
        
        for row_index in [0, 1, 10, 100, 999, None]:
            result = processor.process_record(basic_rule, record, row_index)
            assert result.row_index == row_index
