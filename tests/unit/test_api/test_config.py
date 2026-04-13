"""
Unit tests for the ValidationConfig and related configuration classes.

Tests cover configuration creation, validation, serialization, and
error handling for various configuration scenarios.
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

from src.policy_dq.config import (
    ValidationConfig,
    RuleSourceConfig,
    OutputConfig,
    create_default_config,
    create_config_from_env
)
from src.policy_dq.exceptions import ConfigurationError
from src.policy_dq.models import ValidationSeverity


class TestRuleSourceConfig:
    """Test cases for RuleSourceConfig class."""
    
    def test_init_with_valid_source(self):
        """Test RuleSourceConfig initialization with valid source."""
        config = RuleSourceConfig(source="test_rules.yaml")
        
        assert config.source == "test_rules.yaml"
        assert config.source_type == "auto"
        assert config.fallback_sources == []
        assert config.use_cache is True
    
    def test_init_with_empty_source(self):
        """Test RuleSourceConfig initialization with empty source."""
        with pytest.raises(ConfigurationError) as exc_info:
            RuleSourceConfig(source="")
        
        assert "Rule source cannot be empty" in str(exc_info.value)
    
    def test_init_with_fallback_sources(self):
        """Test RuleSourceConfig with fallback sources."""
        fallback_sources = [
            {"source": "backup_rules.yaml", "type": "file"}
        ]
        config = RuleSourceConfig(
            source="primary_rules.yaml",
            fallback_sources=fallback_sources
        )
        
        assert config.fallback_sources == fallback_sources


class TestOutputConfig:
    """Test cases for OutputConfig class."""
    
    def test_init_with_defaults(self):
        """Test OutputConfig initialization with default values."""
        config = OutputConfig()
        
        assert config.output_directory is None
        assert config.generate_console_report is True
        assert config.generate_json_report is True
        assert config.generate_markdown_report is True
        assert config.console_colors is True
        assert config.include_passed_results is False
    
    def test_init_with_valid_output_directory(self):
        """Test OutputConfig with valid output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = OutputConfig(output_directory=temp_dir)
            assert config.output_directory == temp_dir
    
    def test_init_creates_output_directory(self):
        """Test OutputConfig creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            new_dir = Path(temp_dir) / "new_output_dir"
            config = OutputConfig(output_directory=str(new_dir))
            
            assert new_dir.exists()
            assert config.output_directory == str(new_dir)
    
    def test_init_with_invalid_output_directory(self):
        """Test OutputConfig with invalid output directory."""
        # Try to create directory in a location that requires permissions
        # On Windows, this might not always fail, so let's use a different approach
        import os
        if os.name == 'nt':  # Windows
            # Use a path with invalid characters
            invalid_path = "C:\\invalid<>path"
        else:
            # Unix-like systems
            invalid_path = "/invalid/path/that/cannot/be/created"
        
        with pytest.raises(ConfigurationError) as exc_info:
            OutputConfig(output_directory=invalid_path)
        
        assert "Cannot create output directory" in str(exc_info.value)
        assert exc_info.value.config_key == "output_directory"


class TestValidationConfig:
    """Test cases for ValidationConfig class."""
    
    def test_init_with_minimal_config(self):
        """Test ValidationConfig initialization with minimal configuration."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        config = ValidationConfig(rule_source=rule_source)
        
        assert config.rule_source == rule_source
        assert isinstance(config.output, OutputConfig)
        assert config.fail_fast is False
        assert config.severity_threshold == ValidationSeverity.ERROR
        assert config.max_errors_per_rule is None
        assert config.batch_size is None
        assert config.parallel_processing is False
        assert config.mcp_config is None
        assert config.log_level == "INFO"
        assert config.log_file is None
    
    def test_init_with_full_config(self):
        """Test ValidationConfig initialization with all options."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        output = OutputConfig(output_directory="/tmp/output")
        
        config = ValidationConfig(
            rule_source=rule_source,
            output=output,
            fail_fast=True,
            severity_threshold=ValidationSeverity.WARNING,
            max_errors_per_rule=10,
            batch_size=100,
            parallel_processing=True,
            mcp_config={"server": "localhost"},
            log_level="DEBUG",
            log_file="/tmp/validation.log"
        )
        
        assert config.rule_source == rule_source
        assert config.output == output
        assert config.fail_fast is True
        assert config.severity_threshold == ValidationSeverity.WARNING
        assert config.max_errors_per_rule == 10
        assert config.batch_size == 100
        assert config.parallel_processing is True
        assert config.mcp_config == {"server": "localhost"}
        assert config.log_level == "DEBUG"
        assert config.log_file == "/tmp/validation.log"
    
    def test_from_dict_simple(self):
        """Test ValidationConfig.from_dict with simple configuration."""
        config_dict = {
            "rule_source": "test_rules.yaml",
            "fail_fast": True,
            "severity_threshold": "warning"
        }
        
        config = ValidationConfig.from_dict(config_dict)
        
        assert config.rule_source.source == "test_rules.yaml"
        assert config.fail_fast is True
        assert config.severity_threshold == ValidationSeverity.WARNING
    
    def test_from_dict_complex(self):
        """Test ValidationConfig.from_dict with complex configuration."""
        config_dict = {
            "rule_source": {
                "source": "test_rules.yaml",
                "source_type": "file",
                "use_cache": False
            },
            "output": {
                "generate_console_report": False,
                "generate_json_report": True
            },
            "severity_threshold": "error",
            "max_errors_per_rule": 5
        }
        
        config = ValidationConfig.from_dict(config_dict)
        
        assert config.rule_source.source == "test_rules.yaml"
        assert config.rule_source.source_type == "file"
        assert config.rule_source.use_cache is False
        assert config.output.generate_console_report is False
        assert config.output.generate_json_report is True
        assert config.severity_threshold == ValidationSeverity.ERROR
        assert config.max_errors_per_rule == 5
    
    def test_from_dict_invalid_severity(self):
        """Test ValidationConfig.from_dict with invalid severity threshold."""
        config_dict = {
            "rule_source": "test_rules.yaml",
            "severity_threshold": "invalid_severity"
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            ValidationConfig.from_dict(config_dict)
        
        assert "Invalid severity threshold" in str(exc_info.value)
        assert exc_info.value.config_key == "severity_threshold"
    
    def test_from_file_json(self):
        """Test ValidationConfig.from_file with JSON file."""
        config_data = {
            "rule_source": "test_rules.yaml",
            "fail_fast": True,
            "output": {
                "generate_console_report": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            config = ValidationConfig.from_file(config_file)
            
            assert config.rule_source.source == "test_rules.yaml"
            assert config.fail_fast is True
            assert config.output.generate_console_report is False
        finally:
            Path(config_file).unlink()
    
    def test_from_file_yaml(self):
        """Test ValidationConfig.from_file with YAML file."""
        config_data = {
            "rule_source": "test_rules.yaml",
            "severity_threshold": "warning"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config = ValidationConfig.from_file(config_file)
            
            assert config.rule_source.source == "test_rules.yaml"
            assert config.severity_threshold == ValidationSeverity.WARNING
        finally:
            Path(config_file).unlink()
    
    def test_from_file_not_found(self):
        """Test ValidationConfig.from_file with non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            ValidationConfig.from_file("nonexistent.json")
        
        assert "Configuration file not found" in str(exc_info.value)
        assert exc_info.value.config_key == "config_file"
    
    def test_from_file_unsupported_format(self):
        """Test ValidationConfig.from_file with unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text")
            config_file = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ValidationConfig.from_file(config_file)
            
            assert "Unsupported configuration file format" in str(exc_info.value)
        finally:
            Path(config_file).unlink()
    
    def test_to_dict(self):
        """Test ValidationConfig.to_dict method."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        output = OutputConfig(generate_console_report=False)
        config = ValidationConfig(
            rule_source=rule_source,
            output=output,
            fail_fast=True,
            severity_threshold=ValidationSeverity.WARNING
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["rule_source"]["source"] == "test_rules.yaml"
        assert config_dict["output"]["generate_console_report"] is False
        assert config_dict["fail_fast"] is True
        assert config_dict["severity_threshold"] == "warning"
    
    def test_validate_success(self):
        """Test ValidationConfig.validate with valid configuration."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        config = ValidationConfig(rule_source=rule_source)
        
        # Should not raise any exception
        config.validate()
    
    def test_validate_empty_rule_source(self):
        """Test ValidationConfig.validate with empty rule source."""
        rule_source = RuleSourceConfig.__new__(RuleSourceConfig)
        rule_source.source = ""  # Bypass __post_init__ validation
        config = ValidationConfig(rule_source=rule_source)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Rule source must be specified" in str(exc_info.value)
    
    def test_validate_invalid_batch_size(self):
        """Test ValidationConfig.validate with invalid batch size."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        config = ValidationConfig(rule_source=rule_source, batch_size=0)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Batch size must be positive" in str(exc_info.value)
        assert exc_info.value.config_key == "batch_size"
    
    def test_validate_invalid_max_errors(self):
        """Test ValidationConfig.validate with invalid max errors per rule."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        config = ValidationConfig(rule_source=rule_source, max_errors_per_rule=-1)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Max errors per rule must be positive" in str(exc_info.value)
        assert exc_info.value.config_key == "max_errors_per_rule"
    
    def test_validate_invalid_log_level(self):
        """Test ValidationConfig.validate with invalid log level."""
        rule_source = RuleSourceConfig(source="test_rules.yaml")
        config = ValidationConfig(rule_source=rule_source, log_level="INVALID")
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "Invalid log level" in str(exc_info.value)
        assert exc_info.value.config_key == "log_level"


class TestConfigurationUtilities:
    """Test cases for configuration utility functions."""
    
    def test_create_default_config(self):
        """Test create_default_config function."""
        config = create_default_config("test_rules.yaml", "/tmp/output")
        
        assert config.rule_source.source == "test_rules.yaml"
        assert config.output.output_directory == "/tmp/output"
        assert config.fail_fast is False
        assert config.severity_threshold == ValidationSeverity.ERROR
    
    def test_create_default_config_no_output_dir(self):
        """Test create_default_config without output directory."""
        config = create_default_config("test_rules.yaml")
        
        assert config.rule_source.source == "test_rules.yaml"
        assert config.output.output_directory is None
    
    def test_create_config_from_env(self, monkeypatch):
        """Test create_config_from_env function."""
        # Set environment variables
        monkeypatch.setenv("POLICY_DQ_RULE_SOURCE", "env_rules.yaml")
        monkeypatch.setenv("POLICY_DQ_OUTPUT_DIR", "/tmp/env_output")
        monkeypatch.setenv("POLICY_DQ_SEVERITY_THRESHOLD", "warning")
        monkeypatch.setenv("POLICY_DQ_FAIL_FAST", "true")
        monkeypatch.setenv("POLICY_DQ_LOG_LEVEL", "DEBUG")
        
        config = create_config_from_env()
        
        assert config.rule_source.source == "env_rules.yaml"
        assert config.output.output_directory == "/tmp/env_output"
        assert config.severity_threshold == ValidationSeverity.WARNING
        assert config.fail_fast is True
        assert config.log_level == "DEBUG"
    
    def test_create_config_from_env_missing_required(self, monkeypatch):
        """Test create_config_from_env with missing required environment variable."""
        # Don't set POLICY_DQ_RULE_SOURCE
        monkeypatch.delenv("POLICY_DQ_RULE_SOURCE", raising=False)
        
        with pytest.raises(ConfigurationError) as exc_info:
            create_config_from_env()
        
        assert "POLICY_DQ_RULE_SOURCE environment variable is required" in str(exc_info.value)
        assert exc_info.value.config_key == "POLICY_DQ_RULE_SOURCE"
    
    def test_create_config_from_env_defaults(self, monkeypatch):
        """Test create_config_from_env with default values."""
        monkeypatch.setenv("POLICY_DQ_RULE_SOURCE", "env_rules.yaml")
        # Don't set other optional variables
        monkeypatch.delenv("POLICY_DQ_OUTPUT_DIR", raising=False)
        monkeypatch.delenv("POLICY_DQ_SEVERITY_THRESHOLD", raising=False)
        monkeypatch.delenv("POLICY_DQ_FAIL_FAST", raising=False)
        monkeypatch.delenv("POLICY_DQ_LOG_LEVEL", raising=False)
        
        config = create_config_from_env()
        
        assert config.rule_source.source == "env_rules.yaml"
        assert config.output.output_directory is None
        assert config.fail_fast is False
        assert config.log_level == "INFO"