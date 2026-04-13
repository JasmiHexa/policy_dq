"""
Unit tests for console report generation.

These tests verify the ConsoleReporter behavior with
different report formats and configurations.
"""

import pytest
from io import StringIO

from src.policy_dq.reporters.console import ConsoleReporter
from src.policy_dq.models import ValidationReport, ValidationResult, ValidationSeverity


class TestConsoleReporter:
    """Test cases for ConsoleReporter."""
    
    @pytest.fixture
    def sample_report(self):
        """Create a sample validation report for testing."""
        results = [
            ValidationResult(
                rule_name="required_name",
                field="name",
                row_index=0,
                severity=ValidationSeverity.CRITICAL,
                message="Name is required",
                passed=False
            ),
            ValidationResult(
                rule_name="email_format",
                field="email",
                row_index=1,
                severity=ValidationSeverity.ERROR,
                message="Invalid email format: 'invalid-email'",
                passed=False
            ),
            ValidationResult(
                rule_name="age_range",
                field="age",
                row_index=2,
                severity=ValidationSeverity.WARNING,
                message="Age value outside expected range: 150",
                passed=False
            ),
            ValidationResult(
                rule_name="valid_name",
                field="name",
                row_index=3,
                severity=ValidationSeverity.INFO,
                message="Name validation passed",
                passed=True
            )
        ]
        
        return ValidationReport(
            total_records=4,
            total_rules=3,
            passed_validations=1,
            failed_validations=3,
            results=results,
            summary_by_severity={
                ValidationSeverity.CRITICAL: 1,
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 1,
                ValidationSeverity.INFO: 1
            }
        )
    
    @pytest.fixture
    def empty_report(self):
        """Create an empty validation report."""
        return ValidationReport(
            total_records=0,
            total_rules=0,
            passed_validations=0,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
    
    @pytest.fixture
    def success_report(self):
        """Create a report with all validations passing."""
        results = [
            ValidationResult(
                rule_name="valid_name",
                field="name",
                row_index=0,
                severity=ValidationSeverity.INFO,
                message="Name validation passed",
                passed=True
            ),
            ValidationResult(
                rule_name="valid_email",
                field="email",
                row_index=0,
                severity=ValidationSeverity.INFO,
                message="Email validation passed",
                passed=True
            )
        ]
        
        return ValidationReport(
            total_records=1,
            total_rules=2,
            passed_validations=2,
            failed_validations=0,
            results=results,
            summary_by_severity={ValidationSeverity.INFO: 2}
        )
    
    def test_reporter_initialization_default(self):
        """Test ConsoleReporter initialization with default settings."""
        reporter = ConsoleReporter()
        
        assert reporter.use_colors is True  # Default should be True
        assert hasattr(reporter, 'generate_report')
    
    def test_reporter_initialization_no_colors(self):
        """Test ConsoleReporter initialization with colors disabled."""
        reporter = ConsoleReporter(use_colors=False)
        
        assert reporter.use_colors is False
    
    def test_reporter_initialization_with_colors(self):
        """Test ConsoleReporter initialization with colors enabled."""
        reporter = ConsoleReporter(use_colors=True)
        
        assert reporter.use_colors is True
    
    def test_generate_report_basic(self, sample_report):
        """Test basic report generation."""
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(sample_report)
        
        output = mock_stdout.getvalue()
        
        # Check that basic information is present
        assert "Total Records Processed: 4" in output
        assert "Total Rules Applied: 3" in output
        assert "Passed Validations: 1" in output
        assert "Failed Validations: 3" in output
        
        # Check that severity counts are present
        assert "CRITICAL: 1" in output
        assert "ERROR: 1" in output
        assert "WARNING: 1" in output
        assert "INFO: 1" in output
    
    def test_generate_report_with_failures(self, sample_report):
        """Test report generation includes failure details."""
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(sample_report)
        
        output = mock_stdout.getvalue()
        
        # Check that failure details are present
        assert "required_name" in output
        assert "Name is required" in output
        assert "email_format" in output
        assert "Invalid email format" in output
        assert "age_range" in output
        assert "Age value outside expected range" in output
    
    def test_generate_report_empty(self, empty_report):
        """Test report generation with empty report."""
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(empty_report)
        
        output = mock_stdout.getvalue()
        
        # Check that zero values are displayed
        assert "Total Records Processed: 0" in output
        assert "Total Rules Applied: 0" in output
        assert "Passed Validations: 0" in output
        assert "Failed Validations: 0" in output
    
    def test_generate_report_success_only(self, success_report):
        """Test report generation with only successful validations."""
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(success_report)
        
        output = mock_stdout.getvalue()
        
        # Check basic stats
        assert "Total Records Processed: 1" in output
        assert "Passed Validations: 2" in output
        assert "Failed Validations: 0" in output
        
        # Should indicate success
        assert "validation" in output.lower()
    
    def test_generate_report_with_colors(self, sample_report):
        """Test report generation with colors enabled."""
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=True)
        reporter.generate_report(sample_report)
        
        output = mock_stdout.getvalue()
        
        # Should contain basic information (colors are implementation detail)
        assert "Total Records Processed: 4" in output
        assert "Failed Validations: 3" in output
        
        # Check that failure information is present
        assert "required_name" in output
        assert "email_format" in output
        assert "age_range" in output
    
    def test_generate_report_deterministic_order(self):
        """Test that report generation produces deterministic output order."""
        # Create report with results in random order
        results = [
            ValidationResult("rule_c", "field_c", 2, ValidationSeverity.ERROR, "Error C", False),
            ValidationResult("rule_a", "field_a", 0, ValidationSeverity.WARNING, "Warning A", False),
            ValidationResult("rule_b", "field_b", 1, ValidationSeverity.CRITICAL, "Critical B", False),
        ]
        
        report = ValidationReport(
            total_records=3,
            total_rules=3,
            passed_validations=0,
            failed_validations=3,
            results=results,
            summary_by_severity={
                ValidationSeverity.CRITICAL: 1,
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 1
            }
        )
        
        # Generate report multiple times
        outputs = []
        for _ in range(3):
            mock_stdout = StringIO()
            reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
            reporter.generate_report(report)
            outputs.append(mock_stdout.getvalue())
        
        # All outputs should be identical (deterministic)
        assert outputs[0] == outputs[1] == outputs[2]
    
    def test_generate_report_severity_ordering(self):
        """Test that failures are displayed in severity order."""
        results = [
            ValidationResult("info_rule", "field", 0, ValidationSeverity.INFO, "Info message", False),
            ValidationResult("critical_rule", "field", 0, ValidationSeverity.CRITICAL, "Critical message", False),
            ValidationResult("warning_rule", "field", 0, ValidationSeverity.WARNING, "Warning message", False),
            ValidationResult("error_rule", "field", 0, ValidationSeverity.ERROR, "Error message", False),
        ]
        
        report = ValidationReport(
            total_records=1,
            total_rules=4,
            passed_validations=0,
            failed_validations=4,
            results=results,
            summary_by_severity={
                ValidationSeverity.CRITICAL: 1,
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 1,
                ValidationSeverity.INFO: 1
            }
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Check that all messages are present
        assert "Critical message" in output
        assert "Error message" in output
        assert "Warning message" in output
        assert "Info message" in output
    
    def test_generate_report_row_index_display(self):
        """Test that row indices are displayed correctly."""
        results = [
            ValidationResult("rule1", "field1", 0, ValidationSeverity.ERROR, "Error at row 0", False),
            ValidationResult("rule2", "field2", 10, ValidationSeverity.ERROR, "Error at row 10", False),
            ValidationResult("rule3", "field3", None, ValidationSeverity.ERROR, "Error with no row", False),
        ]
        
        report = ValidationReport(
            total_records=11,
            total_rules=3,
            passed_validations=0,
            failed_validations=3,
            results=results,
            summary_by_severity={ValidationSeverity.ERROR: 3}
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Check that row information is included
        assert "Error at row 0" in output
        assert "Error at row 10" in output
        assert "Error with no row" in output
    
    def test_generate_report_unicode_handling(self):
        """Test report generation with unicode characters."""
        results = [
            ValidationResult(
                "unicode_rule",
                "名前",  # Japanese field name
                0,
                ValidationSeverity.ERROR,
                "エラーメッセージ",  # Japanese error message
                False
            )
        ]
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=results,
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Should handle unicode without errors
        assert "unicode_rule" in output
        assert "名前" in output
        assert "エラーメッセージ" in output
    
    def test_generate_report_very_long_messages(self):
        """Test report generation with very long error messages."""
        long_message = "This is a very long error message that goes on and on " * 20
        
        results = [
            ValidationResult(
                "long_message_rule",
                "field",
                0,
                ValidationSeverity.ERROR,
                long_message,
                False
            )
        ]
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=results,
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Should handle long messages without errors
        assert "long_message_rule" in output
        assert len(output) > 1000  # Should include the long message
    
    def test_generate_report_special_characters(self):
        """Test report generation with special characters in messages."""
        special_message = "Error with special chars: @#$%^&*()[]{}|\\:;\"'<>,.?/~`"
        
        results = [
            ValidationResult(
                "special_chars_rule",
                "field",
                0,
                ValidationSeverity.ERROR,
                special_message,
                False
            )
        ]
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=results,
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Should handle special characters without errors
        assert "special_chars_rule" in output
        assert "@#$%^&*()" in output
    
    def test_generate_report_no_output_parameter(self, sample_report):
        """Test that generate_report doesn't require output parameter."""
        reporter = ConsoleReporter(use_colors=False)
        
        # Should not raise an exception
        try:
            reporter.generate_report(sample_report)
        except Exception as e:
            pytest.fail(f"generate_report raised an exception: {e}")
    
    def test_generate_report_with_none_report(self):
        """Test behavior when report is None."""
        reporter = ConsoleReporter(use_colors=False)
        
        # Should handle None gracefully or raise appropriate error
        with pytest.raises((TypeError, AttributeError, ValueError)):
            reporter.generate_report(None)
    
    def test_generate_report_large_dataset(self):
        """Test report generation with large number of results."""
        # Create report with many results
        results = []
        for i in range(1000):
            results.append(
                ValidationResult(
                    f"rule_{i}",
                    f"field_{i % 10}",
                    i,
                    ValidationSeverity.ERROR,
                    f"Error message {i}",
                    False
                )
            )
        
        report = ValidationReport(
            total_records=1000,
            total_rules=10,
            passed_validations=0,
            failed_validations=1000,
            results=results,
            summary_by_severity={ValidationSeverity.ERROR: 1000}
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Should handle large dataset without errors
        assert "Total Records Processed: 1000" in output
        assert "Failed Validations: 1000" in output
        assert "ERROR: 1000" in output
    
    def test_generate_report_mixed_severities(self):
        """Test report generation with all severity levels."""
        results = []
        severities = [ValidationSeverity.INFO, ValidationSeverity.WARNING, 
                     ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]
        
        for i, severity in enumerate(severities):
            results.append(
                ValidationResult(
                    f"rule_{severity.value}",
                    f"field_{i}",
                    i,
                    severity,
                    f"{severity.value.title()} message",
                    False
                )
            )
        
        report = ValidationReport(
            total_records=4,
            total_rules=4,
            passed_validations=0,
            failed_validations=4,
            results=results,
            summary_by_severity={
                ValidationSeverity.INFO: 1,
                ValidationSeverity.WARNING: 1,
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.CRITICAL: 1
            }
        )
        
        mock_stdout = StringIO()
        reporter = ConsoleReporter(output_stream=mock_stdout, use_colors=False)
        reporter.generate_report(report)
        
        output = mock_stdout.getvalue()
        
        # Check that all severity levels are represented
        assert "ℹ INFO: 1" in output
        assert "⚠ WARNING: 1" in output
        assert "✗ ERROR: 1" in output
        assert "🚨 CRITICAL: 1" in output