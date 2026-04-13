"""
Integration tests for rule loading functionality.
"""

import pytest
from pathlib import Path

from src.policy_dq.rules.file_loader import FileRuleLoader
from src.policy_dq.models import ValidationSeverity, RuleType


class TestRuleLoadingIntegration:
    """Integration tests for rule loading with sample data."""
    
    def test_load_sample_rules_json(self):
        """Test loading the sample rules JSON file."""
        loader = FileRuleLoader()
        sample_file = Path("sample_data/sample_rules.json")
        
        # Skip test if sample file doesn't exist
        if not sample_file.exists():
            pytest.skip("Sample rules file not found")
        
        rules = loader.load_rules(str(sample_file))
        
        # Verify we loaded the expected number of rules
        assert len(rules) == 5
        
        # Verify specific rules
        rule_names = [rule.name for rule in rules]
        expected_names = [
            "email_required",
            "email_format", 
            "age_range",
            "customer_id_unique",
            "date_consistency"
        ]
        
        for expected_name in expected_names:
            assert expected_name in rule_names
        
        # Verify rule details
        email_required = next(rule for rule in rules if rule.name == "email_required")
        assert email_required.rule_type == RuleType.REQUIRED_FIELD
        assert email_required.field == "email"
        assert email_required.severity == ValidationSeverity.ERROR
        
        age_range = next(rule for rule in rules if rule.name == "age_range")
        assert age_range.rule_type == RuleType.NUMERIC_RANGE
        assert age_range.field == "age"
        assert age_range.severity == ValidationSeverity.WARNING
        assert age_range.parameters == {"min": 18, "max": 99}
        
        customer_id_unique = next(rule for rule in rules if rule.name == "customer_id_unique")
        assert customer_id_unique.rule_type == RuleType.UNIQUENESS
        assert customer_id_unique.field == "customer_id"
        assert customer_id_unique.severity == ValidationSeverity.CRITICAL