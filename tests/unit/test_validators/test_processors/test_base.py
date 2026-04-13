"""
Unit tests for base validation processor functionality.

These tests verify the RuleProcessor base class and
common processor behavior.
"""

import pytest

from src.policy_dq.validators.processors.base import RuleProcessor
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationResult


class MockRuleProcessor(RuleProcessor):
    """Mock rule processor for testing base functionality."""
    
    def __init__(self, should_pass=True, custom_message=None):
        self.should_pass = should_pass
        self.custom_message = custom_message
    
    def can_process(self, rule):
        return True
    
    def process_record(self, rule, record, record_index, all_records=None):
        message = self.custom_message or ("Validation passed" if self.should_pass else "Validation failed")
        return ValidationResult(
            rule_name=rule.name,
            field=rule.field,
            row_index=record_index,
            severity=rule.severity,
            message=message,
            passed=self.should_pass
        )


class TestRuleProcessor:
    """Test cases for RuleProcessor base class."""
    
    def test_processor_interface(self):
        """Test that RuleProcessor defines the expected interface."""
        # Verify abstract methods exist
        assert hasattr(RuleProcessor, 'can_process')
        assert hasattr(RuleProcessor, 'process_record')
        
        # Verify we cannot instantiate abstract class directly
        with pytest.raises(TypeError):
            RuleProcessor()
    
    def test_mock_processor_success(self):
        """Test mock processor with successful validation."""
        processor = MockRuleProcessor(should_pass=True)
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test_field": "test_value"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.rule_name == "test_rule"
        assert result.field == "test_field"
        assert result.row_index == 0
        assert result.severity == ValidationSeverity.ERROR
        assert result.passed is True
        assert "passed" in result.message.lower()
    
    def test_mock_processor_failure(self):
        """Test mock processor with validation failure."""
        processor = MockRuleProcessor(should_pass=False, custom_message="Custom failure message")
        
        rule = ValidationRule(
            name="failing_rule",
            rule_type=RuleType.REGEX_CHECK,
            field="email",
            parameters={},
            severity=ValidationSeverity.WARNING
        )
        
        record = {"email": "invalid-email"}
        result = processor.process_record(rule, record, 1)
        
        assert isinstance(result, ValidationResult)
        assert result.rule_name == "failing_rule"
        assert result.field == "email"
        assert result.row_index == 1
        assert result.severity == ValidationSeverity.WARNING
        assert result.passed is False
        assert result.message == "Custom failure message"
    
    def test_processor_result_consistency(self):
        """Test that processor results are consistent across calls."""
        processor = MockRuleProcessor(should_pass=True)
        
        rule = ValidationRule(
            name="consistent_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="name",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"name": "John Doe"}
        
        # Run multiple times
        result1 = processor.process_record(rule, record, 0)
        result2 = processor.process_record(rule, record, 0)
        result3 = processor.process_record(rule, record, 0)
        
        # Results should be identical
        assert result1.passed == result2.passed == result3.passed
        assert result1.message == result2.message == result3.message
        assert result1.rule_name == result2.rule_name == result3.rule_name
    
    def test_processor_with_different_severities(self):
        """Test processor behavior with different severity levels."""
        processor = MockRuleProcessor(should_pass=False)
        
        severities = [
            ValidationSeverity.INFO,
            ValidationSeverity.WARNING,
            ValidationSeverity.ERROR,
            ValidationSeverity.CRITICAL
        ]
        
        for severity in severities:
            rule = ValidationRule(
                name=f"rule_{severity.value}",
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters={},
                severity=severity
            )
            
            record = {"test_field": "value"}
            result = processor.process_record(rule, record, 0)
            
            assert result.severity == severity
            assert result.passed is False
    
    def test_processor_with_different_row_indices(self):
        """Test processor behavior with different row indices."""
        processor = MockRuleProcessor(should_pass=True)
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test_field": "value"}
        
        for row_index in [0, 1, 10, 100, 999]:
            result = processor.process_record(rule, record, row_index)
            assert result.row_index == row_index
    
    def test_processor_with_none_row_index(self):
        """Test processor behavior with None row index."""
        processor = MockRuleProcessor(should_pass=True)
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test_field": "value"}
        result = processor.process_record(rule, record, None)
        
        assert result.row_index is None
    
    def test_processor_with_empty_record(self):
        """Test processor behavior with empty record."""
        processor = MockRuleProcessor(should_pass=False)
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="missing_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.field == "missing_field"
        assert result.passed is False
    
    def test_processor_with_none_values(self):
        """Test processor behavior with None values in record."""
        processor = MockRuleProcessor(should_pass=False)
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="null_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"null_field": None}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.field == "null_field"
        assert result.passed is False
    
    def test_processor_message_requirements(self):
        """Test that processor messages meet requirements."""
        processor = MockRuleProcessor(should_pass=False, custom_message="Detailed error message")
        
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test_field": ""}
        result = processor.process_record(rule, record, 0)
        
        # Message should be non-empty string
        assert isinstance(result.message, str)
        assert len(result.message) > 0
        
        # Message should be descriptive
        assert len(result.message) > 5  # More than just "Error"
    
    def test_processor_field_name_preservation(self):
        """Test that processor preserves field names correctly."""
        processor = MockRuleProcessor(should_pass=True)
        
        field_names = ["email", "user_name", "field_123", "field_with_underscores", ""]
        
        for field_name in field_names:
            rule = ValidationRule(
                name="test_rule",
                rule_type=RuleType.REQUIRED_FIELD,
                field=field_name,
                parameters={},
                severity=ValidationSeverity.ERROR
            )
            
            record = {field_name: "value"} if field_name else {}
            result = processor.process_record(rule, record, 0)
            
            assert result.field == field_name
    
    def test_processor_rule_name_preservation(self):
        """Test that processor preserves rule names correctly."""
        processor = MockRuleProcessor(should_pass=True)
        
        rule_names = ["simple_rule", "rule_with_underscores", "rule123", "very_long_rule_name_with_many_parts"]
        
        for rule_name in rule_names:
            rule = ValidationRule(
                name=rule_name,
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters={},
                severity=ValidationSeverity.ERROR
            )
            
            record = {"test_field": "value"}
            result = processor.process_record(rule, record, 0)
            
            assert result.rule_name == rule_name
    
    def test_processor_deterministic_behavior(self):
        """Test that processor behavior is deterministic."""
        processor = MockRuleProcessor(should_pass=True, custom_message="Deterministic message")
        
        rule = ValidationRule(
            name="deterministic_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test_field": "consistent_value"}
        
        # Run validation multiple times
        results = []
        for _ in range(10):
            result = processor.process_record(rule, record, 0)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.passed == first_result.passed
            assert result.message == first_result.message
            assert result.rule_name == first_result.rule_name
            assert result.field == first_result.field
            assert result.severity == first_result.severity
            assert result.row_index == first_result.row_index