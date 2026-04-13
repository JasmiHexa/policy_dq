"""
Integration tests for CLI commands and exit behavior.

These tests verify that the CLI commands work correctly with various
inputs and exit with appropriate status codes.
"""

import json
import os
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


class TestValidateCommand:
    """Test cases for the validate command."""
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_success_with_no_failures(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with successful validation (no failures)."""
        # Mock successful validation with no failures
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
    def test_validate_success_with_failures_below_threshold(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with failures below severity threshold."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        # Create report with warning-level failures (below error threshold)
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
        mock_engine.check_severity_threshold.return_value = True
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file,
            '--severity-threshold', 'error'
        ])
        
        assert result.exit_code == ExitCodes.SUCCESS
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_failure_exceeds_threshold(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with failures exceeding severity threshold."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        # Create report with error-level failures
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
                    message="Error message",
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
            '--rules', sample_rules_file,
            '--severity-threshold', 'error'
        ])
        
        assert result.exit_code == ExitCodes.VALIDATION_FAILED
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_with_verbose_output(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with verbose output."""
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
            '--verbose',
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.SUCCESS
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_configuration_error(self, mock_engine_class, runner, sample_csv_file):
        """Test validate command with configuration error."""
        mock_engine_class.side_effect = ConfigurationError(
            "Invalid configuration parameter",
            config_key="test_key"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', 'nonexistent_rules.json'
        ])
        
        assert result.exit_code == ExitCodes.CONFIGURATION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_data_source_error(self, mock_engine_class, runner, sample_rules_file):
        """Test validate command with data source error."""
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
    def test_validate_execution_error(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with validation execution error."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = ValidationExecutionError(
            "Validation failed during rule loading",
            stage="rule_loading"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.VALIDATION_EXECUTION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_report_generation_error(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with report generation error."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        mock_engine.validate_file.side_effect = ReportGenerationError(
            "Cannot write to output directory",
            report_type="json"
        )
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.REPORT_GENERATION_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_unexpected_error(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with unexpected error."""
        mock_engine_class.side_effect = RuntimeError("Unexpected system error")
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.UNEXPECTED_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_keyboard_interrupt(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with keyboard interrupt."""
        mock_engine_class.side_effect = KeyboardInterrupt()
        
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file
        ])
        
        assert result.exit_code == ExitCodes.UNEXPECTED_ERROR
    
    @patch('src.policy_dq.cli.ValidationEngine')
    def test_validate_different_severity_thresholds(self, mock_engine_class, runner, sample_csv_file, sample_rules_file):
        """Test validate command with different severity thresholds."""
        mock_engine = MagicMock()
        mock_engine_class.return_value = mock_engine
        
        # Create report with critical-level failures
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
                    severity=ValidationSeverity.CRITICAL,
                    message="Critical error",
                    passed=False
                )
            ],
            summary_by_severity={ValidationSeverity.CRITICAL: 1}
        )
        
        mock_engine.validate_file.return_value = mock_report
        
        # Test with critical threshold - should pass
        mock_engine.check_severity_threshold.return_value = True
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file,
            '--severity-threshold', 'critical'
        ])
        assert result.exit_code == ExitCodes.SUCCESS
        
        # Test with error threshold - should fail
        mock_engine.check_severity_threshold.return_value = False
        result = runner.invoke(cli, [
            'validate', 
            sample_csv_file, 
            '--rules', sample_rules_file,
            '--severity-threshold', 'error'
        ])
        assert result.exit_code == ExitCodes.VALIDATION_FAILED


class TestSummarizeCommand:
    """Test cases for the summarize command."""
    
    def test_summarize_success(self, runner):
        """Test summarize command with valid report file."""
        # Create a sample report file
        report_data = {
            "metadata": {
                "timestamp": "2024-01-15T10:30:00Z",
                "input_file": "test_data.csv",
                "rules_source": "test_rules.json",
                "total_records": 3,
                "total_rules": 1
            },
            "summary": {
                "total_records": 3,
                "passed_validations": 2,
                "failed_validations": 1,
                "by_severity": {
                    "error": 1,
                    "warning": 0,
                    "critical": 0,
                    "info": 0
                }
            },
            "results": [
                {
                    "rule_name": "email_format",
                    "field": "email",
                    "row_index": 2,
                    "severity": "error",
                    "message": "Email format invalid: 'invalid-email'",
                    "passed": False
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f)
            report_file = f.name
        
        try:
            result = runner.invoke(cli, [
                'summarize', 
                report_file
            ])
            
            assert result.exit_code == ExitCodes.SUCCESS
        finally:
            os.unlink(report_file)
    
    def test_summarize_file_not_found(self, runner):
        """Test summarize command with non-existent file."""
        result = runner.invoke(cli, [
            'summarize', 
            'nonexistent_report.json'
        ])
        
        assert result.exit_code == ExitCodes.DATA_SOURCE_ERROR


class TestExitCodes:
    """Test cases for exit code behavior."""
    
    def test_exit_codes_are_unique(self):
        """Test that all exit codes are unique."""
        exit_codes = [
            ExitCodes.SUCCESS,
            ExitCodes.VALIDATION_FAILED,
            ExitCodes.CONFIGURATION_ERROR,
            ExitCodes.DATA_SOURCE_ERROR,
            ExitCodes.VALIDATION_EXECUTION_ERROR,
            ExitCodes.REPORT_GENERATION_ERROR,
            ExitCodes.UNEXPECTED_ERROR
        ]
        
        assert len(exit_codes) == len(set(exit_codes)), "Exit codes must be unique"
    
    def test_success_exit_code_is_zero(self):
        """Test that success exit code is 0."""
        assert ExitCodes.SUCCESS == 0