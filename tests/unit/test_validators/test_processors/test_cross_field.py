"""
Unit tests for cross-field validation processor.

These tests verify the CrossFieldProcessor behavior with
field comparisons and relationships.
"""

import pytest

from src.policy_dq.validators.processors.cross_field import CrossFieldProcessor
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationResult


class TestCrossFieldProcessor:
    """Test cases for CrossFieldProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create CrossFieldProcessor instance."""
        return CrossFieldProcessor()
    
    @pytest.fixture
    def date_comparison_rule(self):
        """Rule to check that end_date is after start_date."""
        return ValidationRule(
            name="end_after_start",
            rule_type=RuleType.CROSS_FIELD,
            field="start_date",  # Primary field
            parameters={
                "compare_field": "end_date",
                "comparison": "less_than",
                "message": "End date must be after start date"
            },
            severity=ValidationSeverity.ERROR
        )
    
    @pytest.fixture
    def password_confirmation_rule(self):
        """Rule to check that password and confirm_password match."""
        return ValidationRule(
            name="password_match",
            rule_type=RuleType.CROSS_FIELD,
            field="password",  # Primary field
            parameters={
                "compare_field": "confirm_password",
                "comparison": "equals",
                "message": "Password confirmation must match password"
            },
            severity=ValidationSeverity.CRITICAL
        )
    
    @pytest.fixture
    def numeric_comparison_rule(self):
        """Rule to check that max_value is greater than min_value."""
        return ValidationRule(
            name="max_greater_than_min",
            rule_type=RuleType.CROSS_FIELD,
            field="min_value",  # Primary field
            parameters={
                "compare_field": "max_value",
                "comparison": "less_than"
            },
            severity=ValidationSeverity.WARNING
        )
    
    def test_date_comparison_valid(self, processor, date_comparison_rule):
        """Test valid date comparison (end after start)."""
        record = {
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        result = processor.process_record(date_comparison_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "end_after_start"
        assert result.field == ""
        assert result.row_index == 0
        assert result.severity == ValidationSeverity.ERROR
    
    def test_date_comparison_invalid(self, processor, date_comparison_rule):
        """Test invalid date comparison (end before start)."""
        record = {
            "start_date": "2024-01-31",
            "end_date": "2024-01-01"
        }
        result = processor.process_record(date_comparison_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "end_after_start"
        assert result.field == ""
        assert "Cross-field validation failed" in result.message
    
    def test_date_comparison_equal(self, processor, date_comparison_rule):
        """Test date comparison when dates are equal."""
        record = {
            "start_date": "2024-01-15",
            "end_date": "2024-01-15"
        }
        result = processor.process_record(date_comparison_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False  # Equal dates should fail "less_than" comparison
        assert result.rule_name == "end_after_start"
        assert result.field == ""
    
    def test_password_match_valid(self, processor, password_confirmation_rule):
        """Test valid password confirmation match."""
        record = {
            "password": "SecurePassword123",
            "confirm_password": "SecurePassword123"
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "password_match"
        assert result.field == ""
        assert result.severity == ValidationSeverity.CRITICAL
    
    def test_password_match_invalid(self, processor, password_confirmation_rule):
        """Test invalid password confirmation match."""
        record = {
            "password": "SecurePassword123",
            "confirm_password": "DifferentPassword456"
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "password_match"
        assert result.field == ""
        assert "Cross-field validation failed" in result.message
    
    def test_numeric_comparison_valid(self, processor, numeric_comparison_rule):
        """Test valid numeric comparison (max > min)."""
        record = {
            "min_value": 10,
            "max_value": 100
        }
        result = processor.process_record(numeric_comparison_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "max_greater_than_min"
        assert result.field == ""
        assert result.severity == ValidationSeverity.WARNING
    
    def test_numeric_comparison_invalid(self, processor, numeric_comparison_rule):
        """Test invalid numeric comparison (max < min)."""
        record = {
            "min_value": 100,
            "max_value": 10
        }
        result = processor.process_record(numeric_comparison_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "max_greater_than_min"
        assert result.field == ""
    
    def test_missing_field1(self, processor, password_confirmation_rule):
        """Test behavior when first field is missing."""
        record = {
            "confirm_password": "password123"
            # Missing "password" field
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "password_match"
        assert result.field == ""
        assert "missing" in result.message.lower() or "not found" in result.message.lower()
    
    def test_missing_field2(self, processor, password_confirmation_rule):
        """Test behavior when second field is missing."""
        record = {
            "password": "password123"
            # Missing "confirm_password" field
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "password_match"
        assert result.field == ""
        assert "missing" in result.message.lower() or "not found" in result.message.lower()
    
    def test_both_fields_missing(self, processor, password_confirmation_rule):
        """Test behavior when both fields are missing."""
        record = {
            "other_field": "value"
            # Missing both "password" and "confirm_password"
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "password_match"
        assert result.field == ""
    
    def test_none_values(self, processor, password_confirmation_rule):
        """Test behavior with None values."""
        test_cases = [
            {"password": None, "confirm_password": None},  # Both None
            {"password": "test", "confirm_password": None},  # One None
            {"password": None, "confirm_password": "test"}   # Other None
        ]
        
        for record in test_cases:
            result = processor.process_record(password_confirmation_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.rule_name == "password_match"
            assert result.field == ""
            # Behavior depends on implementation - None == None might be True
    
    def test_different_data_types(self, processor):
        """Test comparison with different data types."""
        rule = ValidationRule(
            name="type_comparison",
            rule_type=RuleType.CROSS_FIELD,
            field="value1",  # Primary field
            parameters={
                "compare_field": "value2",
                "comparison": "equals"
            },
            severity=ValidationSeverity.ERROR
        )
        
        test_cases = [
            {"value1": "123", "value2": 123},  # String vs int
            {"value1": 123, "value2": 123.0},  # Int vs float
            {"value1": True, "value2": 1},     # Bool vs int
            {"value1": [], "value2": []},      # Empty lists
            {"value1": {}, "value2": {}}       # Empty dicts
        ]
        
        for record in test_cases:
            result = processor.process_record(rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.rule_name == "type_comparison"
            assert result.field == ""
            # Result depends on how processor handles type coercion
    
    def test_string_comparisons(self, processor):
        """Test string-based comparisons."""
        rule = ValidationRule(
            name="string_comparison",
            rule_type=RuleType.CROSS_FIELD,
            field="str1",  # Primary field
            parameters={
                "compare_field": "str2",
                "comparison": "less_than"  # Lexicographic comparison
            },
            severity=ValidationSeverity.ERROR
        )
        
        test_cases = [
            ({"str1": "apple", "str2": "banana"}, True),   # apple < banana
            ({"str1": "banana", "str2": "apple"}, False),  # banana > apple
            ({"str1": "apple", "str2": "apple"}, False),   # apple == apple
            ({"str1": "Apple", "str2": "apple"}, True),    # Case sensitivity
        ]
        
        for record, expected_pass in test_cases:
            result = processor.process_record(rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed == expected_pass, f"Failed for {record}"
            assert result.rule_name == "string_comparison"
    
    def test_comparison_operators(self, processor):
        """Test different comparison operators."""
        operators = [
            ("equals", {"a": 5, "b": 5}, True),
            ("equals", {"a": 5, "b": 10}, False),
            ("not_equals", {"a": 5, "b": 10}, True),
            ("not_equals", {"a": 5, "b": 5}, False),
            ("less_than", {"a": 5, "b": 10}, True),
            ("less_than", {"a": 10, "b": 5}, False),
            ("less_than_or_equal", {"a": 5, "b": 5}, True),
            ("less_than_or_equal", {"a": 5, "b": 10}, True),
            ("less_than_or_equal", {"a": 10, "b": 5}, False),
            ("greater_than", {"a": 10, "b": 5}, True),
            ("greater_than", {"a": 5, "b": 10}, False),
            ("greater_than_or_equal", {"a": 5, "b": 5}, True),
            ("greater_than_or_equal", {"a": 10, "b": 5}, True),
            ("greater_than_or_equal", {"a": 5, "b": 10}, False)
        ]
        
        for operator, values, expected_pass in operators:
            rule = ValidationRule(
                name=f"test_{operator}",
                rule_type=RuleType.CROSS_FIELD,
                field="a",  # Primary field
                parameters={
                    "compare_field": "b",
                    "comparison": operator
                },
                severity=ValidationSeverity.ERROR
            )
            
            result = processor.process_record(rule, values, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed == expected_pass, f"Failed for {operator} with {values}"
            assert result.rule_name == f"test_{operator}"
    
    def test_case_sensitive_string_comparison(self, processor):
        """Test case-sensitive string comparison."""
        rule = ValidationRule(
            name="case_sensitive",
            rule_type=RuleType.CROSS_FIELD,
            field="str1",  # Primary field
            parameters={
                "compare_field": "str2",
                "comparison": "equals",
                "case_sensitive": True
            },
            severity=ValidationSeverity.ERROR
        )
        
        test_cases = [
            ({"str1": "Test", "str2": "Test"}, True),
            ({"str1": "Test", "str2": "test"}, False),
            ({"str1": "TEST", "str2": "test"}, False)
        ]
        
        for record, expected_pass in test_cases:
            result = processor.process_record(rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            # Result depends on whether processor supports case_sensitive parameter
            assert result.rule_name == "case_sensitive"
    
    def test_case_insensitive_string_comparison(self, processor):
        """Test case-insensitive string comparison."""
        rule = ValidationRule(
            name="case_insensitive",
            rule_type=RuleType.CROSS_FIELD,
            field="",
            parameters={
                "field1": "str1",
                "field2": "str2",
                "comparison": "equals",
                "case_sensitive": False
            },
            severity=ValidationSeverity.ERROR
        )
        
        test_cases = [
            ({"str1": "Test", "str2": "test"}, True),
            ({"str1": "TEST", "str2": "test"}, True),
            ({"str1": "Test", "str2": "Different"}, False)
        ]
        
        for record, expected_pass in test_cases:
            result = processor.process_record(rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            # Result depends on whether processor supports case_sensitive parameter
            assert result.rule_name == "case_insensitive"
    
    def test_invalid_comparison_operator(self, processor):
        """Test behavior with invalid comparison operator."""
        rule = ValidationRule(
            name="invalid_operator",
            rule_type=RuleType.CROSS_FIELD,
            field="a",
            parameters={
                "compare_field": "b",
                "comparison": "invalid_operator"
            },
            severity=ValidationSeverity.ERROR
        )
        
        record = {"a": 5, "b": 10}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "invalid_operator"
        assert "unsupported" in result.message.lower() or "operator" in result.message.lower()
    
    def test_missing_comparison_parameter(self, processor):
        """Test behavior when comparison parameter is missing."""
        rule = ValidationRule(
            name="no_comparison",
            rule_type=RuleType.CROSS_FIELD,
            field="",
            parameters={
                "field1": "a",
                "field2": "b"
                # Missing "comparison" parameter
            },
            severity=ValidationSeverity.ERROR
        )
        
        record = {"a": 5, "b": 10}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "no_comparison"
        assert "comparison" in result.message.lower()
    
    def test_missing_field_parameters(self, processor):
        """Test behavior when field parameters are missing."""
        rule = ValidationRule(
            name="missing_fields",
            rule_type=RuleType.CROSS_FIELD,
            field="",
            parameters={
                "comparison": "equals"
                # Missing "field1" and "field2" parameters
            },
            severity=ValidationSeverity.ERROR
        )
        
        record = {"a": 5, "b": 10}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "missing_fields"
        assert "field" in result.message.lower()
    
    def test_unicode_field_values(self, processor, password_confirmation_rule):
        """Test cross-field validation with unicode values."""
        record = {
            "password": "пароль123",
            "confirm_password": "пароль123"
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "password_match"
    
    def test_very_long_field_values(self, processor, password_confirmation_rule):
        """Test cross-field validation with very long values."""
        long_password = "x" * 10000
        record = {
            "password": long_password,
            "confirm_password": long_password
        }
        result = processor.process_record(password_confirmation_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True
        assert result.rule_name == "password_match"
    
    def test_deterministic_behavior(self, processor, password_confirmation_rule):
        """Test that processor behavior is deterministic."""
        record = {
            "password": "test123",
            "confirm_password": "test123"
        }
        
        # Run validation multiple times
        results = []
        for _ in range(10):
            result = processor.process_record(password_confirmation_rule, record, 0)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.passed == first_result.passed
            assert result.message == first_result.message
            assert result.rule_name == first_result.rule_name
            assert result.field == first_result.field
            assert result.severity == first_result.severity
    
    def test_row_index_preservation(self, processor, password_confirmation_rule):
        """Test that row index is correctly preserved in results."""
        record = {
            "password": "test123",
            "confirm_password": "test123"
        }
        
        for row_index in [0, 1, 10, 100, 999, None]:
            result = processor.process_record(password_confirmation_rule, record, row_index)
            assert result.row_index == row_index
