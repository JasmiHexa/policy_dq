"""
Unit tests for the Markdown reporter.

Tests Markdown output generation, formatting, and file handling.
"""

import tempfile
from pathlib import Path
import pytest
from src.policy_dq.reporters.markdown import MarkdownReporter
from src.policy_dq.models import (
    ValidationReport, ValidationResult, ValidationSeverity
)


class TestMarkdownReporter:
    """Test cases for the MarkdownReporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = MarkdownReporter()
        self.detailed_reporter = MarkdownReporter(include_passed=True, max_failures_per_rule=3)
    
    def test_init_default_parameters(self):
        """Test reporter initialization with default parameters."""
        reporter = MarkdownReporter()
        assert reporter.include_passed is False
        assert reporter.max_failures_per_rule == 10
    
    def test_init_custom_parameters(self):
        """Test reporter initialization with custom parameters."""
        reporter = MarkdownReporter(include_passed=True, max_failures_per_rule=5)
        assert reporter.include_passed is True
        assert reporter.max_failures_per_rule == 5
    
    def test_generate_report_requires_output_path(self):
        """Test that generate_report raises error without output_path."""
        report = ValidationReport(
            total_records=10,
            total_rules=1,
            passed_validations=10,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with pytest.raises(ValueError, match="Markdown reporter requires an output_path"):
            self.reporter.generate_report(report)
    
    def test_generate_report_creates_directory(self):
        """Test that generate_report creates output directory if needed."""
        report = ValidationReport(
            total_records=10,
            total_rules=1,
            passed_validations=10,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            assert output_path.exists()
            assert output_path.parent.exists()
    
    def test_generate_report_all_passed(self):
        """Test Markdown generation for report with all validations passed."""
        report = ValidationReport(
            total_records=100,
            total_rules=5,
            passed_validations=500,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            # Read the generated Markdown
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify header
            assert "# Data Validation Report" in content
            assert "**Generated:**" in content
            assert "**Report Version:** 1.0" in content
            
            # Verify summary
            assert "## Summary" in content
            assert "✅ **PASSED**" in content
            assert "| Total Records | 100 |" in content
            assert "| Success Rate | 100.0% |" in content
            
            # Verify severity breakdown
            assert "## Severity Breakdown" in content
            assert "No validation issues found." in content
            
            # Should not have failures section
            assert "## Detailed Failures" not in content
    
    def test_generate_report_with_failures(self):
        """Test Markdown generation for report with validation failures."""
        failed_results = [
            ValidationResult(
                rule_name="email_format",
                field="email",
                row_index=0,
                severity=ValidationSeverity.ERROR,
                message="Invalid email format",
                passed=False
            ),
            ValidationResult(
                rule_name="age_range",
                field="age",
                row_index=1,
                severity=ValidationSeverity.WARNING,
                message="Age outside recommended range",
                passed=False
            )
        ]
        
        report = ValidationReport(
            total_records=100,
            total_rules=3,
            passed_validations=298,
            failed_validations=2,
            results=failed_results,
            summary_by_severity={
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 1
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify summary shows failure status
            assert "❌ **FAILED**" in content
            assert "| Success Rate | 99.3% |" in content
            
            # Verify severity breakdown
            assert "| ❌ Error | 1 |" in content
            assert "| ⚠️ Warning | 1 |" in content
            
            # Verify statistics section
            assert "## Statistics" in content
            assert "### Top Failed Rules" in content
            assert "### Top Failed Fields" in content
            assert "`email_format`" in content
            assert "`age_range`" in content
            
            # Verify detailed failures
            assert "## Detailed Failures" in content
            assert "### ❌ Errors (1 issues)" in content
            assert "### ⚠️ Warnings (1 issues)" in content
            assert "Invalid email format" in content
            assert "Age outside recommended range" in content
    
    def test_generate_report_critical_issues(self):
        """Test Markdown generation with critical validation issues."""
        critical_result = ValidationResult(
            rule_name="data_integrity",
            field="id",
            row_index=None,
            severity=ValidationSeverity.CRITICAL,
            message="Duplicate primary keys detected",
            passed=False
        )
        
        report = ValidationReport(
            total_records=100,
            total_rules=1,
            passed_validations=99,
            failed_validations=1,
            results=[critical_result],
            summary_by_severity={ValidationSeverity.CRITICAL: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify critical status
            assert "🚨 **CRITICAL ISSUES**" in content
            assert "| 🚨 Critical | 1 |" in content
            assert "### 🚨 Critical Issues (1 issues)" in content
            assert "Duplicate primary keys detected" in content
            assert "| Dataset |" in content  # None row_index should show as "Dataset"
    
    def test_generate_report_warnings_only(self):
        """Test Markdown generation with only warnings."""
        warning_result = ValidationResult(
            rule_name="data_quality",
            field="score",
            row_index=5,
            severity=ValidationSeverity.WARNING,
            message="Score below recommended threshold",
            passed=False
        )
        
        report = ValidationReport(
            total_records=100,
            total_rules=1,
            passed_validations=99,
            failed_validations=1,
            results=[warning_result],
            summary_by_severity={ValidationSeverity.WARNING: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verify warning status
            assert "⚠️ **WARNINGS**" in content
            assert "| ⚠️ Warning | 1 |" in content
    
    def test_include_passed_validations(self):
        """Test including passed validations in the report."""
        passed_result = ValidationResult(
            rule_name="email_format",
            field="email",
            row_index=0,
            severity=ValidationSeverity.INFO,
            message="Valid email format",
            passed=True
        )
        
        failed_result = ValidationResult(
            rule_name="age_range",
            field="age",
            row_index=1,
            severity=ValidationSeverity.ERROR,
            message="Invalid age",
            passed=False
        )
        
        report = ValidationReport(
            total_records=2,
            total_rules=2,
            passed_validations=1,
            failed_validations=1,
            results=[passed_result, failed_result],
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.detailed_reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should include passed validations section
            assert "## Passed Validations" in content
            assert "`email_format`" in content
    
    def test_max_failures_per_rule_limit(self):
        """Test limiting the number of failures shown per rule."""
        # Create more failures than the limit
        failed_results = []
        for i in range(5):
            failed_results.append(ValidationResult(
                rule_name="email_format",
                field="email",
                row_index=i,
                severity=ValidationSeverity.ERROR,
                message=f"Invalid email format in row {i}",
                passed=False
            ))
        
        report = ValidationReport(
            total_records=10,
            total_rules=1,
            passed_validations=5,
            failed_validations=5,
            results=failed_results,
            summary_by_severity={ValidationSeverity.ERROR: 5}
        )
        
        # Use reporter with limit of 3
        limited_reporter = MarkdownReporter(max_failures_per_rule=3)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            limited_reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Should show only 3 failures plus a note about remaining
            assert "Invalid email format in row 0" in content
            assert "Invalid email format in row 1" in content
            assert "Invalid email format in row 2" in content
            assert "... and 2 more similar failures" in content
    
    def test_pipe_character_escaping(self):
        """Test proper escaping of pipe characters in table content."""
        result = ValidationResult(
            rule_name="pipe|test",
            field="field|with|pipes",
            row_index=0,
            severity=ValidationSeverity.ERROR,
            message="Message with | pipe characters",
            passed=False
        )
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=[result],
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pipe characters should be escaped in table content
            assert "pipe\\|test" in content
            assert "field\\|with\\|pipes" in content
            assert "Message with \\| pipe characters" in content
    
    def test_empty_report(self):
        """Test handling of empty validation report."""
        report = ValidationReport(
            total_records=0,
            total_rules=0,
            passed_validations=0,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "| Total Records | 0 |" in content
            assert "✅ **PASSED**" in content
            assert "No validation issues found." in content
            assert "No failures to analyze." in content
    
    def test_unicode_handling(self):
        """Test proper handling of Unicode characters in messages."""
        result = ValidationResult(
            rule_name="unicode_test",
            field="description",
            row_index=0,
            severity=ValidationSeverity.ERROR,
            message="Invalid character: 'é' in français",
            passed=False
        )
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=[result],
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            # Read with UTF-8 encoding
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert "français" in content
            assert "é" in content
    
    def test_large_numbers_formatting(self):
        """Test proper formatting of large numbers with commas."""
        report = ValidationReport(
            total_records=1000000,
            total_rules=50,
            passed_validations=999950,
            failed_validations=50,
            results=[],
            summary_by_severity={ValidationSeverity.ERROR: 50}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.md"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Numbers should be formatted with commas
            assert "| Total Records | 1,000,000 |" in content
            assert "| Passed Validations | 999,950 |" in content
            assert "| Failed Validations | 50 |" in content