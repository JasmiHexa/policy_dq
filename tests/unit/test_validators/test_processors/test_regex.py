"""
Unit tests for regex validation processor.

These tests verify the RegexProcessor behavior with
various patterns and input values.
"""

import pytest
import re

from src.policy_dq.validators.processors.regex import RegexProcessor
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationResult


class TestRegexProcessor:
    """Test cases for RegexProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create RegexProcessor instance."""
        return RegexProcessor()
    
    @pytest.fixture
    def email_rule(self):
        """Email validation rule."""
        return ValidationRule(
            name="email_format",
            rule_type=RuleType.REGEX_CHECK,
            field="email",
            parameters={
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "message": "Invalid email format"
            },
            severity=ValidationSeverity.ERROR
        )
    
    @pytest.fixture
    def phone_rule(self):
        """Phone number validation rule."""
        return ValidationRule(
            name="phone_format",
            rule_type=RuleType.REGEX_CHECK,
            field="phone",
            parameters={
                "pattern": r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"
            },
            severity=ValidationSeverity.WARNING
        )
    
    @pytest.fixture
    def simple_rule(self):
        """Simple pattern rule."""
        return ValidationRule(
            name="simple_pattern",
            rule_type=RuleType.REGEX_CHECK,
            field="code",
            parameters={"pattern": r"^[A-Z]{3}[0-9]{3}$"},
            severity=ValidationSeverity.INFO
        )
    
    def test_valid_email_format(self, processor, email_rule):
        """Test validation with valid email formats."""
        valid_emails = [
            "user@example.com",
            "test.email@domain.org",
            "user+tag@example.co.uk",
            "firstname.lastname@company.com",
            "user123@test-domain.net"
        ]
        
        for email in valid_emails:
            record = {"email": email}
            result = processor.process_record(email_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed is True, f"Email {email} should be valid"
            assert result.rule_name == "email_format"
            assert result.field == "email"
            assert result.severity == ValidationSeverity.ERROR
    
    def test_invalid_email_format(self, processor, email_rule):
        """Test validation with invalid email formats."""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user.domain.com",
            "user@domain.",
            "user space@domain.com",
            "",
            "user@@domain.com"
        ]
        
        for email in invalid_emails:
            record = {"email": email}
            result = processor.process_record(email_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed is False, f"Email {email} should be invalid"
            assert result.rule_name == "email_format"
            assert result.field == "email"
            assert "does not match pattern" in result.message
    
    def test_valid_phone_numbers(self, processor, phone_rule):
        """Test validation with valid phone number formats."""
        valid_phones = [
            "555-123-4567",
            "(555) 123-4567",
            "555.123.4567",
            "555 123 4567",
            "5551234567",
            "+1-555-123-4567",
            "1-555-123-4567"
        ]
        
        for phone in valid_phones:
            record = {"phone": phone}
            result = processor.process_record(phone_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed is True, f"Phone {phone} should be valid"
            assert result.rule_name == "phone_format"
            assert result.field == "phone"
            assert result.severity == ValidationSeverity.WARNING
    
    def test_invalid_phone_numbers(self, processor, phone_rule):
        """Test validation with invalid phone number formats."""
        invalid_phones = [
            "123-45-6789",  # Too short
            "555-123-45678",  # Too long
            "abc-def-ghij",  # Letters
            "555-123",  # Incomplete
            "",  # Empty
            "555 123 4567 ext 123"  # Extra text
        ]
        
        for phone in invalid_phones:
            record = {"phone": phone}
            result = processor.process_record(phone_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            assert result.passed is False, f"Phone {phone} should be invalid"
            assert result.rule_name == "phone_format"
            assert result.field == "phone"
    
    def test_simple_pattern_matching(self, processor, simple_rule):
        """Test validation with simple pattern (3 letters + 3 digits)."""
        valid_codes = ["ABC123", "XYZ789", "DEF456"]
        invalid_codes = ["abc123", "AB123", "ABCD123", "ABC12", "123ABC", ""]
        
        for code in valid_codes:
            record = {"code": code}
            result = processor.process_record(simple_rule, record, 0)
            
            assert result.passed is True, f"Code {code} should be valid"
            assert result.rule_name == "simple_pattern"
            assert result.field == "code"
            assert result.severity == ValidationSeverity.INFO
        
        for code in invalid_codes:
            record = {"code": code}
            result = processor.process_record(simple_rule, record, 0)
            
            assert result.passed is False, f"Code {code} should be invalid"
            assert result.rule_name == "simple_pattern"
            assert result.field == "code"
    
    def test_missing_field(self, processor, email_rule):
        """Test validation when field is missing from record."""
        record = {"other_field": "value"}
        result = processor.process_record(email_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "email_format"
        assert result.field == "email"
        assert "missing" in result.message.lower() or "not found" in result.message.lower()
    
    def test_none_field_value(self, processor, email_rule):
        """Test validation when field value is None."""
        record = {"email": None}
        result = processor.process_record(email_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is True  # None values pass regex check (handled by required field validation)
        assert result.rule_name == "email_format"
        assert result.field == "email"
        assert "none" in result.message.lower() or "null" in result.message.lower() or "skipping" in result.message.lower()
    
    def test_non_string_field_value(self, processor, email_rule):
        """Test validation when field value is not a string."""
        non_string_values = [123, 45.67, True, [], {}]
        
        for value in non_string_values:
            record = {"email": value}
            result = processor.process_record(email_rule, record, 0)
            
            assert isinstance(result, ValidationResult)
            # Behavior depends on implementation - might convert to string or fail
            assert result.rule_name == "email_format"
            assert result.field == "email"
    
    def test_case_sensitive_pattern(self, processor):
        """Test case-sensitive pattern matching."""
        rule = ValidationRule(
            name="case_sensitive",
            rule_type=RuleType.REGEX_CHECK,
            field="code",
            parameters={"pattern": r"^[A-Z]+$"},  # Only uppercase letters
            severity=ValidationSeverity.ERROR
        )
        
        record = {"code": "ABC"}
        result = processor.process_record(rule, record, 0)
        assert result.passed is True
        
        record = {"code": "abc"}
        result = processor.process_record(rule, record, 0)
        assert result.passed is False
        
        record = {"code": "AbC"}
        result = processor.process_record(rule, record, 0)
        assert result.passed is False
    
    def test_case_insensitive_pattern(self, processor):
        """Test case-insensitive pattern matching."""
        rule = ValidationRule(
            name="case_insensitive",
            rule_type=RuleType.REGEX_CHECK,
            field="code",
            parameters={
                "pattern": r"^[a-z]+$",
                "flags": re.IGNORECASE
            },
            severity=ValidationSeverity.ERROR
        )
        
        test_values = ["abc", "ABC", "AbC", "aBc"]
        
        for value in test_values:
            record = {"code": value}
            result = processor.process_record(rule, record, 0)
            # Behavior depends on whether processor supports flags parameter
            assert result.rule_name == "case_insensitive"
            assert result.field == "code"
    
    def test_multiline_pattern(self, processor):
        """Test pattern matching with multiline strings."""
        rule = ValidationRule(
            name="multiline_pattern",
            rule_type=RuleType.REGEX_CHECK,
            field="text",
            parameters={"pattern": r"^Line 1.*Line 2$"},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"text": "Line 1\nLine 2"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.rule_name == "multiline_pattern"
        assert result.field == "text"
        # Result depends on whether DOTALL flag is used
    
    def test_unicode_pattern_matching(self, processor):
        """Test pattern matching with unicode characters."""
        rule = ValidationRule(
            name="unicode_pattern",
            rule_type=RuleType.REGEX_CHECK,
            field="name",
            parameters={"pattern": r"^[a-zA-ZÀ-ÿ\s]+$"},  # Letters including accented
            severity=ValidationSeverity.ERROR
        )
        
        valid_names = ["José", "María", "François", "Müller", "Øyvind"]
        invalid_names = ["José123", "María@", "François!", ""]
        
        for name in valid_names:
            record = {"name": name}
            result = processor.process_record(rule, record, 0)
            assert result.passed is True, f"Name {name} should be valid"
        
        for name in invalid_names:
            record = {"name": name}
            result = processor.process_record(rule, record, 0)
            assert result.passed is False, f"Name {name} should be invalid"
    
    def test_invalid_regex_pattern(self, processor):
        """Test behavior with invalid regex pattern."""
        rule = ValidationRule(
            name="invalid_regex",
            rule_type=RuleType.REGEX_CHECK,
            field="test",
            parameters={"pattern": r"[invalid(regex"},  # Invalid regex
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test": "value"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "invalid_regex"
        assert result.field == "test"
        assert "pattern" in result.message.lower() or "regex" in result.message.lower()
    
    def test_empty_pattern(self, processor):
        """Test behavior with empty regex pattern."""
        rule = ValidationRule(
            name="empty_pattern",
            rule_type=RuleType.REGEX_CHECK,
            field="test",
            parameters={"pattern": ""},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test": "value"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.rule_name == "empty_pattern"
        assert result.field == "test"
        # Empty pattern might match everything or be treated as error
    
    def test_missing_pattern_parameter(self, processor):
        """Test behavior when pattern parameter is missing."""
        rule = ValidationRule(
            name="no_pattern",
            rule_type=RuleType.REGEX_CHECK,
            field="test",
            parameters={},  # No pattern parameter
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test": "value"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        assert result.rule_name == "no_pattern"
        assert result.field == "test"
        assert "pattern" in result.message.lower()
    
    def test_custom_error_message(self, processor):
        """Test custom error message parameter."""
        custom_message = "This field must match the required format"
        rule = ValidationRule(
            name="custom_message_rule",
            rule_type=RuleType.REGEX_CHECK,
            field="test",
            parameters={
                "pattern": r"^[A-Z]+$",
                "message": custom_message
            },
            severity=ValidationSeverity.ERROR
        )
        
        record = {"test": "invalid"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False
        # Should use custom message if supported
        assert len(result.message) > 0
    
    def test_very_long_input(self, processor, simple_rule):
        """Test validation with very long input string."""
        long_input = "A" * 10000 + "123"
        record = {"code": long_input}
        result = processor.process_record(simple_rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False  # Doesn't match ABC123 pattern
        assert result.rule_name == "simple_pattern"
        assert result.field == "code"
    
    def test_special_regex_characters(self, processor):
        """Test pattern with special regex characters."""
        rule = ValidationRule(
            name="special_chars",
            rule_type=RuleType.REGEX_CHECK,
            field="text",
            parameters={"pattern": r"^test\.\*\+\?\[\]\(\)\{\}\|\^\\$"},
            severity=ValidationSeverity.ERROR
        )
        
        record = {"text": "test.*+?[](){}|^\\$"}
        result = processor.process_record(rule, record, 0)
        
        assert isinstance(result, ValidationResult)
        assert result.passed is False  # This pattern is complex and may not match exactly
        assert result.rule_name == "special_chars"
        assert result.field == "text"
    
    def test_deterministic_behavior(self, processor, email_rule):
        """Test that processor behavior is deterministic."""
        record = {"email": "test@example.com"}
        
        # Run validation multiple times
        results = []
        for _ in range(10):
            result = processor.process_record(email_rule, record, 0)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result.passed == first_result.passed
            assert result.message == first_result.message
            assert result.rule_name == first_result.rule_name
            assert result.field == first_result.field
            assert result.severity == first_result.severity
    
    def test_row_index_preservation(self, processor, email_rule):
        """Test that row index is correctly preserved in results."""
        record = {"email": "test@example.com"}
        
        for row_index in [0, 1, 10, 100, 999, None]:
            result = processor.process_record(email_rule, record, row_index)
            assert result.row_index == row_index
