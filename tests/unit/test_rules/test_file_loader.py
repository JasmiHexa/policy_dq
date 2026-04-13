"""
Tests for the file-based rule loader.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.policy_dq.rules.file_loader import FileRuleLoader
from src.policy_dq.rules.base import RuleLoadingError
from src.policy_dq.models import ValidationSeverity, RuleType


class TestFileRuleLoader:
    """Test cases for the FileRuleLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = FileRuleLoader()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear loader cache
        self.loader.clear_cache()
    
    def create_temp_file(self, filename: str, content: str) -> str:
        """Create a temporary file with the given content."""
        file_path = self.temp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return str(file_path)
    
    def test_validate_source_valid_json_file(self):
        """Test validate_source with a valid JSON file."""
        content = '{"version": "1.0", "rule_sets": []}'
        file_path = self.create_temp_file("rules.json", content)
        
        assert self.loader.validate_source(file_path) is True
    
    def test_validate_source_valid_yaml_file(self):
        """Test validate_source with a valid YAML file."""
        content = "version: '1.0'\nrule_sets: []"
        file_path = self.create_temp_file("rules.yaml", content)
        
        assert self.loader.validate_source(file_path) is True
    
    def test_validate_source_nonexistent_file(self):
        """Test validate_source with a non-existent file."""
        assert self.loader.validate_source("nonexistent.json") is False
    
    def test_validate_source_unsupported_extension(self):
        """Test validate_source with an unsupported file extension."""
        file_path = self.create_temp_file("rules.txt", "content")
        
        assert self.loader.validate_source(file_path) is False
    
    def test_validate_source_unreadable_file(self):
        """Test validate_source with an unreadable file."""
        # Create a file with invalid UTF-8 content
        file_path = self.temp_path / "invalid.json"
        file_path.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        assert self.loader.validate_source(str(file_path)) is False
    
    def test_load_rules_valid_json(self):
        """Test loading rules from a valid JSON file."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "email_required",
                            "type": "required_field",
                            "field": "email",
                            "severity": "error"
                        },
                        {
                            "name": "age_range",
                            "type": "numeric_range",
                            "field": "age",
                            "parameters": {"min": 18, "max": 99},
                            "severity": "warning"
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        rules = self.loader.load_rules(file_path)
        
        assert len(rules) == 2
        
        # Check first rule
        assert rules[0].name == "email_required"
        assert rules[0].rule_type == RuleType.REQUIRED_FIELD
        assert rules[0].field == "email"
        assert rules[0].severity == ValidationSeverity.ERROR
        assert rules[0].parameters == {}
        
        # Check second rule
        assert rules[1].name == "age_range"
        assert rules[1].rule_type == RuleType.NUMERIC_RANGE
        assert rules[1].field == "age"
        assert rules[1].severity == ValidationSeverity.WARNING
        assert rules[1].parameters == {"min": 18, "max": 99}
    
    @patch('src.policy_dq.rules.file_loader.yaml')
    def test_load_rules_valid_yaml(self, mock_yaml):
        """Test loading rules from a valid YAML file."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "email_format",
                            "type": "regex_check",
                            "field": "email",
                            "parameters": {"pattern": "^[^@]+@[^@]+\\.[^@]+$"}
                        }
                    ]
                }
            ]
        }
        
        mock_yaml.safe_load.return_value = rule_config
        
        file_path = self.create_temp_file("rules.yaml", "dummy content")
        rules = self.loader.load_rules(file_path)
        
        assert len(rules) == 1
        assert rules[0].name == "email_format"
        assert rules[0].rule_type == RuleType.REGEX_CHECK
        assert rules[0].field == "email"
        assert rules[0].parameters == {"pattern": "^[^@]+@[^@]+\\.[^@]+$"}
    
    def test_load_rules_yaml_without_pyyaml(self):
        """Test loading YAML rules when PyYAML is not available."""
        with patch('src.policy_dq.rules.file_loader.yaml', None):
            file_path = self.create_temp_file("rules.yaml", "version: '1.0'")
            
            with pytest.raises(RuleLoadingError, match="PyYAML is required"):
                self.loader.load_rules(file_path)
    
    def test_load_rules_invalid_json(self):
        """Test loading rules from an invalid JSON file."""
        file_path = self.create_temp_file("invalid.json", "{ invalid json }")
        
        with pytest.raises(RuleLoadingError, match="Failed to parse file"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_missing_version(self):
        """Test loading rules from a file missing the version field."""
        rule_config = {"rule_sets": []}
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="missing required 'version' field"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_missing_rule_sets(self):
        """Test loading rules from a file missing the rule_sets field."""
        rule_config = {"version": "1.0"}
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="missing required 'rule_sets' field"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_invalid_rule_sets_type(self):
        """Test loading rules with rule_sets as non-array."""
        rule_config = {"version": "1.0", "rule_sets": "not an array"}
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="'rule_sets' must be an array"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_invalid_rule_type(self):
        """Test loading rules with an invalid rule type."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "invalid_rule",
                            "type": "invalid_type",
                            "field": "test_field"
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="has invalid type 'invalid_type'"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_invalid_severity(self):
        """Test loading rules with an invalid severity."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "test_rule",
                            "type": "required_field",
                            "field": "test_field",
                            "severity": "invalid_severity"
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="has invalid severity 'invalid_severity'"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_missing_required_fields(self):
        """Test loading rules with missing required fields."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "incomplete_rule",
                            "type": "required_field"
                            # Missing 'field'
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        with pytest.raises(RuleLoadingError, match="missing required 'field' field"):
            self.loader.load_rules(file_path)
    
    def test_load_rules_caching(self):
        """Test that rules are cached after first load."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "test_rule",
                            "type": "required_field",
                            "field": "test_field"
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        # Load rules twice
        rules1 = self.loader.load_rules(file_path)
        rules2 = self.loader.load_rules(file_path)
        
        # Should return the same objects (cached)
        assert rules1 is rules2
    
    def test_clear_cache(self):
        """Test that cache can be cleared."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "test_rule",
                            "type": "required_field",
                            "field": "test_field"
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        
        # Load rules and cache them
        rules1 = self.loader.load_rules(file_path)
        
        # Clear cache
        self.loader.clear_cache()
        
        # Load again - should not be the same object
        rules2 = self.loader.load_rules(file_path)
        
        assert rules1 is not rules2
        assert len(rules1) == len(rules2)
    
    def test_load_rules_multiple_rule_sets(self):
        """Test loading rules from multiple rule sets."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "validation_rules",
                    "rules": [
                        {
                            "name": "email_required",
                            "type": "required_field",
                            "field": "email"
                        }
                    ]
                },
                {
                    "name": "business_rules",
                    "rules": [
                        {
                            "name": "age_check",
                            "type": "numeric_range",
                            "field": "age",
                            "parameters": {"min": 0, "max": 120}
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        rules = self.loader.load_rules(file_path)
        
        assert len(rules) == 2
        assert rules[0].name == "email_required"
        assert rules[1].name == "age_check"
    
    def test_load_rules_default_severity(self):
        """Test that rules get default severity when not specified."""
        rule_config = {
            "version": "1.0",
            "rule_sets": [
                {
                    "name": "test_rules",
                    "rules": [
                        {
                            "name": "test_rule",
                            "type": "required_field",
                            "field": "test_field"
                            # No severity specified
                        }
                    ]
                }
            ]
        }
        
        file_path = self.create_temp_file("rules.json", json.dumps(rule_config))
        rules = self.loader.load_rules(file_path)
        
        assert len(rules) == 1
        assert rules[0].severity == ValidationSeverity.ERROR  # Default severity
    
    def test_load_rules_invalid_source(self):
        """Test loading rules from an invalid source."""
        with pytest.raises(RuleLoadingError, match="Invalid or inaccessible source"):
            self.loader.load_rules("nonexistent.json")