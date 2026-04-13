"""
Tests for the numeric range validation processor.
"""

import pytest

from src.policy_dq.validators.processors.numeric_range import NumericRangeProcessor
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity


class TestNumericRangeProcessor:
    """Test cases for the NumericRangeProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = NumericRangeProcessor()
    
    def create_rule(self, field_name: str, **parameters) -> ValidationRule:
        """Helper to create a numeric range validation rule."""
        return ValidationRule(
            name=f"{field_name}_range_check",
            rule_type=RuleType.NUMERIC_RANGE,
            field=field_name,
            parameters=parameters,
            severity=ValidationSeverity.ERROR
        )
    
    def test_can_process_numeric_range_rule(self):
        """Test that processor can handle numeric range rules."""
        rule = self.create_rule("age", min=18, max=99)
        assert self.processor.can_process(rule) is True
    
    def test_can_process_other_rule_types(self):
        """Test that processor rejects other rule types."""
        other_rule = ValidationRule(
            name="required_field",
            rule_type=RuleType.REQUIRED_FIELD,
            field="age",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        assert self.processor.can_process(other_rule) is False
    
    def test_process_record_field_missing(self):
        """Test validation fails when field is missing."""
        rule = self.create_rule("age", min=18, max=99)
        record = {"name": "John Doe"}  # age field missing
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "is missing for numeric range validation" in result.message
    
    def test_process_record_field_none(self):
        """Test validation passes when field is None (skipped)."""
        rule = self.create_rule("age", min=18, max=99)
        record = {"age": None}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is True
        assert "is None, skipping numeric range validation" in result.message
    
    def test_min_max_range_valid(self):
        """Test validation with both min and max bounds - valid values."""
        rule = self.create_rule("age", min=18, max=99)
        
        valid_ages = [18, 25, 50, 99, "30", "65", 18.0, 99.0]
        
        for age in valid_ages:
            record = {"age": age}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for valid age: {age}"
            assert "is within range [18, 99]" in result.message
    
    def test_min_max_range_invalid(self):
        """Test validation with both min and max bounds - invalid values."""
        rule = self.create_rule("age", min=18, max=99)
        
        invalid_ages = [17, 100, 0, -5, "17", "100"]
        
        for age in invalid_ages:
            record = {"age": age}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for invalid age: {age}"
            assert "numeric range validation failed" in result.message
    
    def test_min_only_range_valid(self):
        """Test validation with only minimum bound - valid values."""
        rule = self.create_rule("score", min=0)
        
        valid_scores = [0, 1, 100, 1000, "50", 0.0, 99.99]
        
        for score in valid_scores:
            record = {"score": score}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for valid score: {score}"
            assert "is within range >= 0" in result.message
    
    def test_min_only_range_invalid(self):
        """Test validation with only minimum bound - invalid values."""
        rule = self.create_rule("score", min=0)
        
        invalid_scores = [-1, -10, "-5", -0.1]
        
        for score in invalid_scores:
            record = {"score": score}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for invalid score: {score}"
            assert "is less than minimum 0" in result.message
    
    def test_max_only_range_valid(self):
        """Test validation with only maximum bound - valid values."""
        rule = self.create_rule("temperature", max=100)
        
        valid_temps = [100, 50, 0, -10, "75", 99.99]
        
        for temp in valid_temps:
            record = {"temperature": temp}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for valid temperature: {temp}"
            assert "is within range <= 100" in result.message
    
    def test_max_only_range_invalid(self):
        """Test validation with only maximum bound - invalid values."""
        rule = self.create_rule("temperature", max=100)
        
        invalid_temps = [101, 200, "150", 100.1]
        
        for temp in invalid_temps:
            record = {"temperature": temp}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for invalid temperature: {temp}"
            assert "is greater than maximum 100" in result.message
    
    def test_exclusive_bounds(self):
        """Test validation with exclusive bounds."""
        rule = self.create_rule("percentage", min=0, max=100, min_inclusive=False, max_inclusive=False)
        
        # Valid values (between 0 and 100, exclusive)
        valid_values = [0.1, 50, 99.9, "25.5"]
        for value in valid_values:
            record = {"percentage": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is True, f"Failed for valid value: {value}"
            assert "is within range (0, 100)" in result.message
        
        # Invalid values (at or outside bounds)
        invalid_values = [0, 100, -1, 101]
        for value in invalid_values:
            record = {"percentage": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for invalid value: {value}"
    
    def test_mixed_inclusive_exclusive_bounds(self):
        """Test validation with mixed inclusive/exclusive bounds."""
        # Min inclusive, max exclusive: [0, 100)
        rule = self.create_rule("value", min=0, max=100, min_inclusive=True, max_inclusive=False)
        
        test_cases = [
            (0, True),      # Min inclusive
            (50, True),     # Within range
            (99.9, True),   # Just below max
            (100, False),   # Max exclusive
            (-1, False),    # Below min
        ]
        
        for value, should_pass in test_cases:
            record = {"value": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed == should_pass, f"Failed for value: {value}"
    
    def test_non_numeric_values(self):
        """Test validation with non-numeric values."""
        rule = self.create_rule("age", min=18, max=99)
        
        non_numeric_values = ["not_a_number", "abc", "", "18.5.5", True, False, [], {}]
        
        for value in non_numeric_values:
            record = {"age": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed is False, f"Should fail for non-numeric value: {value}"
            assert "cannot be converted to number" in result.message
    
    def test_string_numeric_conversion(self):
        """Test conversion of string values to numbers."""
        rule = self.create_rule("price", min=0, max=1000)
        
        string_values = [
            ("25", True),
            ("999.99", True),
            ("0", True),
            ("1000", True),
            ("-1", False),
            ("1001", False),
            ("  50  ", True),  # With whitespace
        ]
        
        for value, should_pass in string_values:
            record = {"price": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed == should_pass, f"Failed for string value: {value}"
    
    def test_missing_range_parameters(self):
        """Test validation with missing min and max parameters."""
        rule = self.create_rule("value")  # No min or max
        record = {"value": 50}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "must specify at least 'min' or 'max' parameter" in result.message
    
    def test_invalid_range_parameters(self):
        """Test validation with invalid min/max parameter values."""
        # Invalid min parameter
        rule = self.create_rule("value", min="not_a_number", max=100)
        record = {"value": 50}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "Invalid 'min' parameter value" in result.message
        
        # Invalid max parameter
        rule = self.create_rule("value", min=0, max="not_a_number")
        record = {"value": 50}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "Invalid 'max' parameter value" in result.message
    
    def test_float_precision(self):
        """Test validation with floating point precision."""
        rule = self.create_rule("value", min=0.1, max=0.9)
        
        test_cases = [
            (0.1, True),
            (0.5, True),
            (0.9, True),
            (0.09999, False),
            (0.90001, False),
        ]
        
        for value, should_pass in test_cases:
            record = {"value": value}
            result = self.processor.process_record(rule, record, 0)
            assert result.passed == should_pass, f"Failed for float value: {value}"
    
    def test_process_dataset_multiple_records(self):
        """Test processing multiple records in a dataset."""
        rule = self.create_rule("age", min=18, max=99)
        records = [
            {"age": 25},        # Valid
            {"age": 17},        # Invalid - too low
            {"age": "30"},      # Valid - string conversion
            {"age": 100},       # Invalid - too high
            {"age": None},      # Valid - None skipped
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 5
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[2].passed is True
        assert results[3].passed is False
        assert results[4].passed is True  # None is skipped
    
    def test_convert_to_numeric_method(self):
        """Test the _convert_to_numeric helper method."""
        # Valid conversions
        assert self.processor._convert_to_numeric(42) == 42
        assert self.processor._convert_to_numeric(42.5) == 42.5
        assert self.processor._convert_to_numeric("42") == 42
        assert self.processor._convert_to_numeric("42.5") == 42.5
        assert self.processor._convert_to_numeric("  25  ") == 25
        
        # Invalid conversions
        with pytest.raises(ValueError):
            self.processor._convert_to_numeric("not_a_number")
        
        with pytest.raises(ValueError):
            self.processor._convert_to_numeric(True)
        
        with pytest.raises(ValueError):
            self.processor._convert_to_numeric([])
    
    def test_get_range_description_method(self):
        """Test the _get_range_description helper method."""
        # Both min and max
        desc = self.processor._get_range_description(10, 20, True, True)
        assert desc == "[10, 20]"
        
        desc = self.processor._get_range_description(10, 20, False, False)
        assert desc == "(10, 20)"
        
        desc = self.processor._get_range_description(10, 20, True, False)
        assert desc == "[10, 20)"
        
        # Min only
        desc = self.processor._get_range_description(10, None, True, True)
        assert desc == ">= 10"
        
        desc = self.processor._get_range_description(10, None, False, True)
        assert desc == "> 10"
        
        # Max only
        desc = self.processor._get_range_description(None, 20, True, True)
        assert desc == "<= 20"
        
        desc = self.processor._get_range_description(None, 20, True, False)
        assert desc == "< 20"
        
        # Neither
        desc = self.processor._get_range_description(None, None, True, True)
        assert desc == "no range specified"