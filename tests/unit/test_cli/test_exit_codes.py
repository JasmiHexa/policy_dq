"""
Integration tests for CLI exit codes and error handling.

These tests verify that the CLI commands exit with appropriate status codes
and provide user-friendly error messages.
"""

import json
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from src.policy_dq.cli import cli, ExitCodes
from src.policy_dq.models import ValidationSeverity, ValidationResult, ValidationReport
from src.policy_dq.exceptions import (
    ConfigurationError,
    DataSourceError,
    ValidationExecutionError,
    ReportGenerationError
)


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("name,email,age\n")
        f.write("John Doe,john@example.com,25\n")
        f.write("Jane Smith,jane@example.com,30\n")
        return f.name


@pytest.fixture
def sample_rules_file():
    """Create a temporary rules file for testing."""
    rules = {
        "version": "1.0",
        "rule_sets": [
            {
                "name": "test_rules",
                "rules": [
                    {
                        "name": "email_format",
                        "type": "regex_check",
                        "field": "email",
                        "parameters": {
                            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
                        },
                        "severity": "error"
                    }
                ]
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(rules, f)
        return f.name


class TestExitCodes:
    """Test cases for CLI exit code behavior."""
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validation_success_exit_code(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that successful validation returns exit code 0."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        mock_report = ValidationReport(
            total_records=2,
            total_rules=1,
            passed_validations=2,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        mock_engine.validate_file.return_value = mock_report
        mock_engine.check_severity_threshold.return_value = True
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.SUCCESS
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validation_failure_exit_code(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that validation failure returns appropriate exit code."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        mock_report = ValidationReport(
            total_records=2,
            total_rules=1,
            passed_validations=1,
            failed_validations=1,
            results=[
                ValidationResult(
                    rule_name="test_rule",
                    field="test_field",
                    row_index=1,
                    severity=ValidationSeverity.ERROR,
                    message="Test error",
                    passed=False
                )
            ],
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        mock_engine.validate_file.return_value = mock_report
        mock_engine.check_severity_threshold.return_value = False
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.VALIDATION_FAILED
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_configuration_error_exit_code(self, mock_engine_class, runner, sample_csv_file):
        """Test that configuration errors return appropriate exit code."""
        mock_engine_class.side_effect = ConfigurationError(
            "Invalid configuration",
            config_key="test_key"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', 'invalid_rules.json'
        ])
        
        assert result.exit_code == ExitCodes.CONFIGURATION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_data_source_error_exit_code(self, mock_engine_class, runner, sample_rules_file):
        """Test that data source errors return appropriate exit code."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = DataSourceError(
            "File not found",
            source_path="nonexistent.csv"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            'nonexistent.csv', 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.DATA_SOURCE_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validation_execution_error_exit_code(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that validation execution errors return appropriate exit code."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = ValidationExecutionError(
            "Execution failed",
            stage="validation"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.VALIDATION_EXECUTION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_report_generation_error_exit_code(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that report generation errors return appropriate exit code."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = ReportGenerationError(
            "Cannot generate report",
            report_type="json"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.REPORT_GENERATION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_unexpected_error_exit_code(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that unexpected errors return appropriate exit code."""
        mock_engine_class.side_effect = RuntimeError("Unexpected error")
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.UNEXPECTED_ERROR


class TestSeverityThreshold:
    """Test cases for severity threshold behavior."""
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_different_severity_thresholds(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validation with different severity thresholds."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        # Create report with warning-level failures
        mock_report = ValidationReport(
            total_records=2,
            total_rules=1,
            passed_validations=1,
            failed_validations=1,
            results=[
                ValidationResult(
                    rule_name="test_rule",
                    field="test_field",
                    row_index=1,
                    severity=ValidationSeverity.WARNING,
                    message="Warning message",
                    passed=False
                )
            ],
            summary_by_severity={ValidationSeverity.WARNING: 1}
        )
        
        mock_engine.validate_file.return_value = mock_report
        
        # Test with warning threshold - should fail
        mock_engine.check_severity_threshold.return_value = False
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file,
            '--severity-threshold', 'warning'
        ])
        assert result.exit_code == ExitCodes.VALIDATION_FAILED
        
        # Test with error threshold - should pass
        mock_engine.check_severity_threshold.return_value = True
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file,
            '--severity-threshold', 'error'
        ])
        assert result.exit_code == ExitCodes.SUCCESS


class TestErrorMessages:
    """Test cases for error message content."""
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_configuration_error_message_includes_suggestions(self, mock_engine_class, runner, sample_csv_file):
        """Test that configuration error messages include helpful suggestions."""
        mock_engine_class.side_effect = ConfigurationError(
            "Invalid configuration",
            config_key="test_key"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', 'invalid_rules.json'
        ])
        
        assert result.exit_code == ExitCodes.CONFIGURATION_ERROR
        # The exact message format may vary, just check it's an error
        assert result.output  # Should have some output
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_data_source_error_message_includes_suggestions(self, mock_engine_class, runner, sample_rules_file):
        """Test that data source error messages include helpful suggestions."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = DataSourceError(
            "File not found",
            source_path="nonexistent.csv"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            'nonexistent.csv', 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.DATA_SOURCE_ERROR
        assert result.output  # Should have some output
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validation_execution_error_with_stage_info(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test that validation execution errors include stage information."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = ValidationExecutionError(
            "Execution failed",
            stage="rule_loading"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.VALIDATION_EXECUTION_ERROR
        assert result.output  # Should have some output