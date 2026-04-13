"""
Unit tests for the JSON reporter.

Tests JSON output generation, file handling, and data structure validation.
"""

import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch
from src.policy_dq.reporters.json_reporter import JSONReporter
from src.policy_dq.models import (
    ValidationReport, ValidationResult, ValidationSeverity
)


class TestJSONReporter:
    """Test cases for the JSONReporter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reporter = JSONReporter()
        self.compact_reporter = JSONReporter(indent=None, sort_keys=False)
    
    def test_init_default_parameters(self):
        """Test reporter initialization with default parameters."""
        reporter = JSONReporter()
        assert reporter.indent == 2
        assert reporter.sort_keys is True
    
    def test_init_custom_parameters(self):
        """Test reporter initialization with custom parameters."""
        reporter = JSONReporter(indent=4, sort_keys=False)
        assert reporter.indent == 4
        assert reporter.sort_keys is False
    
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
        
        with pytest.raises(ValueError, match="JSON reporter requires an output_path"):
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
            output_path = Path(temp_dir) / "subdir" / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            assert output_path.exists()
            assert output_path.parent.exists()
    
    def test_generate_report_all_passed(self):
        """Test JSON generation for report with all validations passed."""
        report = ValidationReport(
            total_records=100,
            total_rules=5,
            passed_validations=500,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            # Read and parse the generated JSON
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            # Verify structure
            assert "metadata" in json_data
            assert "summary" in json_data
            assert "results" in json_data
            assert "statistics" in json_data
            
            # Verify metadata
            assert json_data["metadata"]["report_version"] == "1.0"
            assert json_data["metadata"]["generator"] == "policy-dq-validator"
            assert "timestamp" in json_data["metadata"]
            
            # Verify summary
            summary = json_data["summary"]
            assert summary["total_records"] == 100
            assert summary["total_rules"] == 5
            assert summary["passed_validations"] == 500
            assert summary["failed_validations"] == 0
            assert summary["success_rate"] == 100.0
            
            # Verify results
            assert json_data["results"] == []
    
    def test_generate_report_with_failures(self):
        """Test JSON generation for report with validation failures."""
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
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            # Read and parse the generated JSON
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            # Verify summary
            summary = json_data["summary"]
            assert summary["failed_validations"] == 2
            assert summary["success_rate"] == 99.33
            assert summary["severity_breakdown"]["error"] == 1
            assert summary["severity_breakdown"]["warning"] == 1
            
            # Verify results
            results = json_data["results"]
            assert len(results) == 2
            
            # Check first result
            result1 = results[0]
            assert result1["rule_name"] == "email_format"
            assert result1["field"] == "email"
            assert result1["row_index"] == 0
            assert result1["severity"] == "error"
            assert result1["message"] == "Invalid email format"
            assert result1["passed"] is False
            
            # Verify statistics
            stats = json_data["statistics"]
            assert "failures_by_rule" in stats
            assert "failures_by_field" in stats
            assert "failures_by_severity" in stats
            assert "most_common_failures" in stats
            
            assert stats["failures_by_rule"]["email_format"] == 1
            assert stats["failures_by_rule"]["age_range"] == 1
            assert stats["failures_by_field"]["email"] == 1
            assert stats["failures_by_field"]["age"] == 1
    
    def test_generate_report_compact_format(self):
        """Test JSON generation with compact formatting."""
        report = ValidationReport(
            total_records=10,
            total_rules=1,
            passed_validations=10,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.compact_reporter.generate_report(report, str(output_path))
            
            # Read the raw JSON content
            with open(output_path, 'r') as f:
                content = f.read()
            
            # Compact format should not have indentation
            assert '\n' not in content or content.count('\n') < 5
            
            # Should still be valid JSON
            json_data = json.loads(content)
            assert "metadata" in json_data
            assert "summary" in json_data
    
    def test_statistics_calculation(self):
        """Test detailed statistics calculation."""
        # Create multiple failures for the same rule and field
        failed_results = [
            ValidationResult("email_format", "email", 0, ValidationSeverity.ERROR, "Invalid format", False),
            ValidationResult("email_format", "email", 1, ValidationSeverity.ERROR, "Invalid format", False),
            ValidationResult("email_format", "email", 2, ValidationSeverity.ERROR, "Missing @ symbol", False),
            ValidationResult("age_range", "age", 3, ValidationSeverity.WARNING, "Too young", False),
            ValidationResult("required_field", "name", 4, ValidationSeverity.ERROR, "Field missing", False)
        ]
        
        report = ValidationReport(
            total_records=100,
            total_rules=3,
            passed_validations=95,
            failed_validations=5,
            results=failed_results,
            summary_by_severity={
                ValidationSeverity.ERROR: 4,
                ValidationSeverity.WARNING: 1
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            stats = json_data["statistics"]
            
            # Check failures by rule
            assert stats["failures_by_rule"]["email_format"] == 3
            assert stats["failures_by_rule"]["age_range"] == 1
            assert stats["failures_by_rule"]["required_field"] == 1
            
            # Check failures by field
            assert stats["failures_by_field"]["email"] == 3
            assert stats["failures_by_field"]["age"] == 1
            assert stats["failures_by_field"]["name"] == 1
            
            # Check most common failures
            common_failures = stats["most_common_failures"]
            assert len(common_failures) > 0
            
            # The most common should be "email_format: Invalid format" with count 2
            most_common = common_failures[0]
            assert most_common["rule_name"] == "email_format"
            assert most_common["message"] == "Invalid format"
            assert most_common["count"] == 2
            assert "email" in most_common["affected_fields"]
    
    def test_none_row_index_handling(self):
        """Test handling of validation results with None row_index."""
        result = ValidationResult(
            rule_name="dataset_rule",
            field="",
            row_index=None,
            severity=ValidationSeverity.CRITICAL,
            message="Dataset-level validation failed",
            passed=False
        )
        
        report = ValidationReport(
            total_records=100,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=[result],
            summary_by_severity={ValidationSeverity.CRITICAL: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            result_data = json_data["results"][0]
            assert result_data["row_index"] is None
            assert result_data["field"] == ""
            assert result_data["severity"] == "critical"
    
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
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            assert json_data["summary"]["total_records"] == 0
            assert json_data["summary"]["success_rate"] == 100.0
            assert json_data["results"] == []
            assert json_data["statistics"]["failures_by_rule"] == {}
    
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
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            # Read with UTF-8 encoding
            with open(output_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            result_data = json_data["results"][0]
            assert "français" in result_data["message"]
            assert "é" in result_data["message"]
    
    def test_large_dataset_statistics(self):
        """Test statistics calculation with large dataset."""
        # Create a large number of results
        results = []
        for i in range(10000):
            results.append(ValidationResult(
                rule_name=f"rule_{i % 100}",
                field=f"field_{i % 50}",
                row_index=i,
                severity=ValidationSeverity.ERROR if i % 2 == 0 else ValidationSeverity.WARNING,
                message=f"Message {i}",
                passed=False
            ))
        
        report = ValidationReport(
            total_records=10000,
            total_rules=100,
            passed_validations=0,
            failed_validations=10000,
            results=results,
            summary_by_severity={
                ValidationSeverity.ERROR: 5000,
                ValidationSeverity.WARNING: 5000
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            # Should handle large datasets without issues
            assert json_data["summary"]["total_records"] == 10000
            assert len(json_data["results"]) == 10000
            assert len(json_data["statistics"]["failures_by_rule"]) == 100
            assert len(json_data["statistics"]["failures_by_field"]) == 50
    
    def test_file_permissions_error(self):
        """Test handling of file permission errors."""
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=1,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        # Try to write to a directory that doesn't exist and can't be created
        # This is platform-specific, so we'll use a mock
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "restricted" / "report.json"
                
                with pytest.raises(PermissionError):
                    self.reporter.generate_report(report, str(output_path))
    
    def test_json_serialization_edge_cases(self):
        """Test JSON serialization with edge case values."""
        results = [
            ValidationResult(
                rule_name="edge_case_test",
                field="special_values",
                row_index=0,
                severity=ValidationSeverity.INFO,
                message="Testing special float values: inf, -inf, nan",
                passed=False
            )
        ]
        
        report = ValidationReport(
            total_records=1,
            total_rules=1,
            passed_validations=0,
            failed_validations=1,
            results=results,
            summary_by_severity={ValidationSeverity.INFO: 1}
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "report.json"
            self.reporter.generate_report(report, str(output_path))
            
            # Should create valid JSON even with edge case messages
            with open(output_path, 'r') as f:
                json_data = json.load(f)
            
            assert json_data["results"][0]["message"] == "Testing special float values: inf, -inf, nan"