"""
Unit tests for rule base classes and rule parsing functionality.

These tests verify rule loading, parsing, and validation behavior
with deterministic and readable test cases.
"""

import pytest

from src.policy_dq.rules.base import RuleLoader, RuleLoadingError
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType


class MockRuleLoader(RuleLoader):
    """Mock rule loader for testing base functionality."""
    
    def __init__(self, rules_data=None, should_fail=False):
        self.rules_data = rules_data or []
        self.should_fail = should_fail
    
    def load_rules(self, source: str):
        if self.should_fail:
            raise RuleLoadingError(f"Mock failure for source: {source}")
        return self.rules_data
    
    def validate_source(self, source: str) -> bool:
        return not self.should_fail


class TestRuleLoader:
    """Test cases for RuleLoader base class."""
    
    def test_rule_loader_interface(self):
        """Test that RuleLoader defines the expected interface."""
        # Verify abstract methods exist
        assert hasattr(RuleLoader, 'load_rules')
        assert hasattr(RuleLoader, 'validate_source')
        
        # Verify we cannot instantiate abstract class directly
        with pytest.raises(TypeError):
            RuleLoader()
    
    def test_mock_rule_loader_success(self):
        """Test mock rule loader with successful operation."""
        test_rules = [
            ValidationRule(
                name="test_rule",
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters={},
                severity=ValidationSeverity.ERROR
            )
        ]
        
        loader = MockRuleLoader(rules_data=test_rules)
        
        # Test source validation
        assert loader.validate_source("test_source") is True
        
        # Test rule loading
        rules = loader.load_rules("test_source")
        assert len(rules) == 1
        assert rules[0].name == "test_rule"
        assert rules[0].rule_type == RuleType.REQUIRED_FIELD
    
    def test_mock_rule_loader_failure(self):
        """Test mock rule loader with failure scenarios."""
        loader = MockRuleLoader(should_fail=True)
        
        # Test source validation failure
        assert loader.validate_source("test_source") is False
        
        # Test rule loading failure
        with pytest.raises(RuleLoadingError, match="Mock failure for source: test_source"):
            loader.load_rules("test_source")


class TestRuleLoadingError:
    """Test cases for RuleLoadingError exception."""
    
    def test_rule_loading_error_creation(self):
        """Test creating RuleLoadingError with message."""
        error = RuleLoadingError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)
    
    def test_rule_loading_error_with_details(self):
        """Test RuleLoadingError with additional details."""
        error = RuleLoadingError("Test error", details={"source": "test.json", "line": 42})
        assert str(error) == "Test error"
        assert hasattr(error, 'details')
        assert error.details == {"source": "test.json", "line": 42}
    
    def test_rule_loading_error_inheritance(self):
        """Test that RuleLoadingError properly inherits from Exception."""
        error = RuleLoadingError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, RuleLoadingError)


class TestRuleParsing:
    """Test cases for rule parsing functionality."""
    
    @pytest.fixture
    def valid_rule_data(self):
        """Valid rule data for testing."""
        return {
            "name": "email_validation",
            "type": "regex_check",
            "field": "email",
            "parameters": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "message": "Invalid email format"
            },
            "severity": "error"
        }
    
    @pytest.fixture
    def minimal_rule_data(self):
        """Minimal valid rule data."""
        return {
            "name": "required_name",
            "type": "required_field",
            "field": "name"
        }
    
    def test_parse_valid_rule_data(self, valid_rule_data):
        """Test parsing complete valid rule data."""
        rule = ValidationRule(
            name=valid_rule_data["name"],
            rule_type=RuleType(valid_rule_data["type"]),
            field=valid_rule_data["field"],
            parameters=valid_rule_data["parameters"],
            severity=ValidationSeverity(valid_rule_data["severity"])
        )
        
        assert rule.name == "email_validation"
        assert rule.rule_type == RuleType.REGEX_CHECK
        assert rule.field == "email"
        assert rule.parameters["pattern"] == r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert rule.severity == ValidationSeverity.ERROR
    
    def test_parse_minimal_rule_data(self, minimal_rule_data):
        """Test parsing minimal rule data with defaults."""
        rule = ValidationRule(
            name=minimal_rule_data["name"],
            rule_type=RuleType(minimal_rule_data["type"]),
            field=minimal_rule_data["field"],
            parameters={},  # Default empty parameters
            severity=ValidationSeverity.ERROR  # Default severity
        )
        
        assert rule.name == "required_name"
        assert rule.rule_type == RuleType.REQUIRED_FIELD
        assert rule.field == "name"
        assert rule.parameters == {}
        assert rule.severity == ValidationSeverity.ERROR
    
    def test_parse_rule_with_all_severities(self):
        """Test parsing rules with different severity levels."""
        severities = [
            ("info", ValidationSeverity.INFO),
            ("warning", ValidationSeverity.WARNING),
            ("error", ValidationSeverity.ERROR),
            ("critical", ValidationSeverity.CRITICAL)
        ]
        
        for severity_str, expected_severity in severities:
            rule = ValidationRule(
                name=f"test_rule_{severity_str}",
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters={},
                severity=ValidationSeverity(severity_str)
            )
            
            assert rule.severity == expected_severity
    
    def test_parse_rule_with_all_types(self):
        """Test parsing rules with different rule types."""
        rule_types = [
            ("required_field", RuleType.REQUIRED_FIELD),
            ("regex_check", RuleType.REGEX_CHECK),
            ("numeric_range", RuleType.NUMERIC_RANGE),
            ("type_check", RuleType.TYPE_CHECK),
            ("uniqueness", RuleType.UNIQUENESS),
            ("cross_field", RuleType.CROSS_FIELD)
        ]
        
        for type_str, expected_type in rule_types:
            rule = ValidationRule(
                name=f"test_rule_{type_str}",
                rule_type=RuleType(type_str),
                field="test_field",
                parameters={},
                severity=ValidationSeverity.ERROR
            )
            
            assert rule.rule_type == expected_type
    
    def test_parse_invalid_rule_type(self):
        """Test parsing rule with invalid rule type."""
        with pytest.raises(ValueError):
            ValidationRule(
                name="invalid_rule",
                rule_type=RuleType("invalid_type"),
                field="test_field",
                parameters={},
                severity=ValidationSeverity.ERROR
            )
    
    def test_parse_invalid_severity(self):
        """Test parsing rule with invalid severity."""
        with pytest.raises(ValueError):
            ValidationRule(
                name="invalid_rule",
                rule_type=RuleType.REQUIRED_FIELD,
                field="test_field",
                parameters={},
                severity=ValidationSeverity("invalid_severity")
            )
    
    def test_rule_equality(self):
        """Test rule equality comparison."""
        rule1 = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={"param1": "value1"},
            severity=ValidationSeverity.ERROR
        )
        
        rule2 = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={"param1": "value1"},
            severity=ValidationSeverity.ERROR
        )
        
        rule3 = ValidationRule(
            name="different_rule",
            rule_type=RuleType.REQUIRED_FIELD,
            field="test_field",
            parameters={"param1": "value1"},
            severity=ValidationSeverity.ERROR
        )
        
        assert rule1 == rule2
        assert rule1 != rule3
    
    def test_rule_string_representation(self):
        """Test rule string representation."""
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REGEX_CHECK,
            field="email",
            parameters={"pattern": "test_pattern"},
            severity=ValidationSeverity.WARNING
        )
        
        rule_str = str(rule)
        assert "test_rule" in rule_str
        assert "regex_check" in rule_str
        assert "email" in rule_str
        assert "warning" in rule_str
    
    def test_rule_deterministic_ordering(self):
        """Test that rules have deterministic ordering for consistent results."""
        rules = [
            ValidationRule("rule_c", RuleType.REQUIRED_FIELD, "field_c", {}, ValidationSeverity.ERROR),
            ValidationRule("rule_a", RuleType.REQUIRED_FIELD, "field_a", {}, ValidationSeverity.ERROR),
            ValidationRule("rule_b", RuleType.REQUIRED_FIELD, "field_b", {}, ValidationSeverity.ERROR),
        ]
        
        # Sort by name for deterministic ordering
        sorted_rules = sorted(rules, key=lambda r: r.name)
        
        assert sorted_rules[0].name == "rule_a"
        assert sorted_rules[1].name == "rule_b"
        assert sorted_rules[2].name == "rule_c"
        
        # Multiple sorts should produce same result
        sorted_again = sorted(rules, key=lambda r: r.name)
        assert [r.name for r in sorted_rules] == [r.name for r in sorted_again]
    
    def test_rule_parameters_immutability(self):
        """Test that rule parameters maintain integrity."""
        original_params = {"pattern": "test", "message": "error"}
        rule = ValidationRule(
            name="test_rule",
            rule_type=RuleType.REGEX_CHECK,
            field="test_field",
            parameters=original_params.copy(),
            severity=ValidationSeverity.ERROR
        )
        
        # Modifying original params should not affect rule
        original_params["pattern"] = "modified"
        assert rule.parameters["pattern"] == "test"
        
        # Rule parameters should be accessible
        assert rule.parameters["message"] == "error"
    
    def test_rule_field_validation(self):
        """Test rule field name validation."""
        # Valid field names
        valid_fields = ["email", "user_name", "field123", "field_with_underscores"]
        
        for field in valid_fields:
            rule = ValidationRule(
                name="test_rule",
                rule_type=RuleType.REQUIRED_FIELD,
                field=field,
                parameters={},
                severity=ValidationSeverity.ERROR
            )
            assert rule.field == field
        
        # Empty field should be allowed (for cross-field validations)
        rule = ValidationRule(
            name="cross_field_rule",
            rule_type=RuleType.CROSS_FIELD,
            field="",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        assert rule.field == ""