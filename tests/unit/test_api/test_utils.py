"""
Unit tests for API utility functions.

Tests cover analysis functions, filtering utilities, export functions,
and other convenience methods in the utils module.
"""

import pytest
import tempfile
import json
import csv
from pathlib import Path
from unittest.mock import Mock

from src.policy_dq.utils import (
    analyze_validation_results,
    get_validation_summary,
    filter_results,
    group_results_by_field,
    group_results_by_rule,
    get_worst_records,
    export_results_to_csv,
    load_sample_data,
    create_sample_rules,
    validate_rule_configuration,
    merge_validation_reports
)
from src.policy_dq.exceptions import ValidationAPIError, DataSourceError
from src.policy_dq.models import ValidationReport, ValidationResult, ValidationSeverity


class TestAnalyzeValidationResults:
    """Test cases for analyze_validation_results function."""
    
    def test_analyze_empty_report(self):
        """Test analysis of empty validation report."""
        report = ValidationReport(
            total_records=0,
            total_rules=0,
            passed_validations=0,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        analysis = analyze_validation_results(report)
        
        assert analysis['overall']['total_records'] == 0
        assert analysis['overall']['success_rate'] == 0.0
        assert analysis['field_analysis'] == {}
        assert analysis['rule_analysis'] == {}
        assert analysis['top_failing_fields'] == []
        assert analysis['top_failing_rules'] == []
    
    def test_analyze_report_with_results(self):
        """Test analysis of validation report with results."""
        results = [
            ValidationResult(
                rule_name="rule1",
                field="field1",
                row_index=0,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule1",
                field="field2",
                row_index=1,
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule2",
                field="field1",
                row_index=0,
                severity=ValidationSeverity.ERROR,
                message="Error 2",
                passed=True
            )
        ]
        
        report = ValidationReport(
            total_records=2,
            total_rules=2,
            passed_validations=1,
            failed_validations=2,
            results=results,
            summary_by_severity={
                ValidationSeverity.ERROR: 1,
                ValidationSeverity.WARNING: 1
            }
        )
        
        analysis = analyze_validation_results(report)
        
        # Check overall statistics
        assert analysis['overall']['total_records'] == 2
        assert analysis['overall']['total_rules'] == 2
        assert analysis['overall']['passed_validations'] == 1
        assert analysis['overall']['failed_validations'] == 2
        assert analysis['overall']['success_rate'] == pytest.approx(33.33, rel=1e-2)
        
        # Check field analysis
        assert 'field1' in analysis['field_analysis']
        assert 'field2' in analysis['field_analysis']
        assert analysis['field_analysis']['field1']['failed'] == 1
        assert analysis['field_analysis']['field2']['failed'] == 1
        
        # Check rule analysis
        assert 'rule1' in analysis['rule_analysis']
        assert 'rule2' in analysis['rule_analysis']
        assert analysis['rule_analysis']['rule1']['failed'] == 2
        assert analysis['rule_analysis']['rule2']['failed'] == 0
        
        # Check top failing items
        assert len(analysis['top_failing_fields']) > 0
        assert len(analysis['top_failing_rules']) > 0


class TestGetValidationSummary:
    """Test cases for get_validation_summary function."""
    
    def test_summary_with_results(self):
        """Test summary generation with validation results."""
        report = ValidationReport(
            total_records=100,
            total_rules=5,
            passed_validations=80,
            failed_validations=20,
            results=[Mock() for _ in range(100)],  # Mock results
            summary_by_severity={
                ValidationSeverity.ERROR: 15,
                ValidationSeverity.WARNING: 5
            }
        )
        
        summary = get_validation_summary(report)
        
        assert "Records processed: 100" in summary
        assert "Rules applied: 5" in summary
        assert "Total validations: 100" in summary
        assert "Passed: 80" in summary
        assert "Failed: 20" in summary
        assert "Success rate: 80.0%" in summary
        assert "ERROR: 15" in summary
        assert "WARNING: 5" in summary
    
    def test_summary_empty_report(self):
        """Test summary generation with empty report."""
        report = ValidationReport(
            total_records=0,
            total_rules=0,
            passed_validations=0,
            failed_validations=0,
            results=[],
            summary_by_severity={}
        )
        
        summary = get_validation_summary(report)
        
        assert "Records processed: 0" in summary
        assert "Success rate: 0.0%" in summary


class TestFilterResults:
    """Test cases for filter_results function."""
    
    def setup_method(self):
        """Set up test data."""
        self.results = [
            ValidationResult(
                rule_name="rule1",
                field="field1",
                row_index=0,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule2",
                field="field2",
                row_index=1,
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule1",
                field="field1",
                row_index=2,
                severity=ValidationSeverity.ERROR,
                message="Error 2",
                passed=True
            )
        ]
    
    def test_filter_by_field(self):
        """Test filtering results by field name."""
        filtered = filter_results(self.results, field="field1")
        
        assert len(filtered) == 2
        assert all(r.field == "field1" for r in filtered)
    
    def test_filter_by_rule(self):
        """Test filtering results by rule name."""
        filtered = filter_results(self.results, rule="rule1")
        
        assert len(filtered) == 2
        assert all(r.rule_name == "rule1" for r in filtered)
    
    def test_filter_by_severity(self):
        """Test filtering results by severity."""
        filtered = filter_results(self.results, severity=ValidationSeverity.ERROR)
        
        assert len(filtered) == 2
        assert all(r.severity == ValidationSeverity.ERROR for r in filtered)
    
    def test_filter_by_passed(self):
        """Test filtering results by pass/fail status."""
        filtered = filter_results(self.results, passed=False)
        
        assert len(filtered) == 2
        assert all(not r.passed for r in filtered)
    
    def test_filter_by_row_range(self):
        """Test filtering results by row range."""
        filtered = filter_results(self.results, row_range=(0, 1))
        
        assert len(filtered) == 2
        assert all(0 <= r.row_index <= 1 for r in filtered)
    
    def test_filter_multiple_criteria(self):
        """Test filtering with multiple criteria."""
        filtered = filter_results(
            self.results,
            field="field1",
            passed=False
        )
        
        assert len(filtered) == 1
        assert filtered[0].field == "field1"
        assert not filtered[0].passed


class TestGroupingFunctions:
    """Test cases for result grouping functions."""
    
    def setup_method(self):
        """Set up test data."""
        self.results = [
            ValidationResult(
                rule_name="rule1",
                field="field1",
                row_index=0,
                severity=ValidationSeverity.ERROR,
                message="Error 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule2",
                field="field1",
                row_index=1,
                severity=ValidationSeverity.WARNING,
                message="Warning 1",
                passed=False
            ),
            ValidationResult(
                rule_name="rule1",
                field="field2",
                row_index=2,
                severity=ValidationSeverity.ERROR,
                message="Error 2",
                passed=True
            )
        ]
    
    def test_group_results_by_field(self):
        """Test grouping results by field name."""
        grouped = group_results_by_field(self.results)
        
        assert "field1" in grouped
        assert "field2" in grouped
        assert len(grouped["field1"]) == 2
        assert len(grouped["field2"]) == 1
    
    def test_group_results_by_rule(self):
        """Test grouping results by rule name."""
        grouped = group_results_by_rule(self.results)
        
        assert "rule1" in grouped
        assert "rule2" in grouped
        assert len(grouped["rule1"]) == 2
        assert len(grouped["rule2"]) == 1


class TestGetWorstRecords:
    """Test cases for get_worst_records function."""
    
    def test_get_worst_records(self):
        """Test getting records with most failures."""
        results = [
            # Record 0: 2 failures
            ValidationResult("rule1", "field1", 0, ValidationSeverity.ERROR, "Error 1", False),
            ValidationResult("rule2", "field2", 0, ValidationSeverity.ERROR, "Error 2", False),
            # Record 1: 1 failure
            ValidationResult("rule1", "field1", 1, ValidationSeverity.ERROR, "Error 3", False),
            # Record 2: 0 failures (passed)
            ValidationResult("rule1", "field1", 2, ValidationSeverity.ERROR, "Success", True),
        ]
        
        worst_records = get_worst_records(results, limit=2)
        
        assert len(worst_records) == 2
        # Should be sorted by failure count descending
        assert worst_records[0][0] == 0  # Row index 0
        assert worst_records[0][1] == 2  # 2 failures
        assert worst_records[1][0] == 1  # Row index 1
        assert worst_records[1][1] == 1  # 1 failure


class TestExportResultsToCsv:
    """Test cases for export_results_to_csv function."""
    
    def test_export_failed_results_only(self):
        """Test exporting only failed results to CSV."""
        results = [
            ValidationResult("rule1", "field1", 0, ValidationSeverity.ERROR, "Error 1", False),
            ValidationResult("rule2", "field2", 1, ValidationSeverity.WARNING, "Warning 1", False),
            ValidationResult("rule3", "field3", 2, ValidationSeverity.INFO, "Info 1", True),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            export_results_to_csv(results, output_path, include_passed=False)
            
            # Read back the CSV and verify content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2  # Only failed results
            assert rows[0]['rule_name'] == 'rule1'
            assert rows[0]['passed'] == 'False'
            assert rows[1]['rule_name'] == 'rule2'
            assert rows[1]['passed'] == 'False'
            
        finally:
            Path(output_path).unlink()
    
    def test_export_all_results(self):
        """Test exporting all results to CSV."""
        results = [
            ValidationResult("rule1", "field1", 0, ValidationSeverity.ERROR, "Error 1", False),
            ValidationResult("rule2", "field2", 1, ValidationSeverity.INFO, "Info 1", True),
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            export_results_to_csv(results, output_path, include_passed=True)
            
            # Read back the CSV and verify content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2  # All results
            
        finally:
            Path(output_path).unlink()


class TestLoadSampleData:
    """Test cases for load_sample_data function."""
    
    def test_load_json_data(self):
        """Test loading sample data from JSON file."""
        sample_data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_data, f)
            file_path = f.name
        
        try:
            loaded_data = load_sample_data(file_path)
            assert loaded_data == sample_data
        finally:
            Path(file_path).unlink()
    
    def test_load_csv_data(self):
        """Test loading sample data from CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'name'])
            writer.writeheader()
            writer.writerow({'id': '1', 'name': 'Alice'})
            writer.writerow({'id': '2', 'name': 'Bob'})
            file_path = f.name
        
        try:
            loaded_data = load_sample_data(file_path)
            assert len(loaded_data) == 2
            assert loaded_data[0]['id'] == '1'
            assert loaded_data[0]['name'] == 'Alice'
        finally:
            Path(file_path).unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading sample data from non-existent file."""
        with pytest.raises(DataSourceError) as exc_info:
            load_sample_data("nonexistent.json")
        
        assert "Sample data file not found" in str(exc_info.value)
    
    def test_load_unsupported_format(self):
        """Test loading sample data from unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some text")
            file_path = f.name
        
        try:
            with pytest.raises(DataSourceError) as exc_info:
                load_sample_data(file_path)
            
            assert "Unsupported sample data format" in str(exc_info.value)
        finally:
            Path(file_path).unlink()


class TestCreateSampleRules:
    """Test cases for create_sample_rules function."""
    
    def test_create_sample_rules(self):
        """Test creating sample validation rules."""
        rule_types = ['required_field', 'type_check', 'regex_check']
        fields = ['field1', 'field2', 'field3']
        
        rules = create_sample_rules(rule_types, fields)
        
        assert len(rules) == 3
        assert rules[0]['type'] == 'required_field'
        assert rules[0]['field'] == 'field1'
        assert rules[1]['type'] == 'type_check'
        assert rules[1]['field'] == 'field2'
        assert 'parameters' in rules[1]
        assert rules[2]['type'] == 'regex_check'
        assert rules[2]['field'] == 'field3'
        assert 'pattern' in rules[2]['parameters']


class TestValidateRuleConfiguration:
    """Test cases for validate_rule_configuration function."""
    
    def test_validate_valid_rules_list(self):
        """Test validation of valid rules list."""
        rules = [
            {
                "name": "test_rule",
                "type": "required_field",
                "field": "test_field",
                "severity": "error"
            }
        ]
        
        issues = validate_rule_configuration(rules)
        assert len(issues) == 0
    
    def test_validate_valid_rules_dict(self):
        """Test validation of valid rules dictionary."""
        rules_data = {
            "rules": [
                {
                    "name": "test_rule",
                    "type": "required_field",
                    "field": "test_field"
                }
            ]
        }
        
        issues = validate_rule_configuration(rules_data)
        assert len(issues) == 0
    
    def test_validate_missing_required_fields(self):
        """Test validation with missing required fields."""
        rules = [
            {
                "name": "test_rule",
                # Missing 'type' and 'field'
                "severity": "error"
            }
        ]
        
        issues = validate_rule_configuration(rules)
        assert len(issues) >= 2  # Should have issues for missing type and field
        assert any("Missing required field 'type'" in issue for issue in issues)
        assert any("Missing required field 'field'" in issue for issue in issues)
    
    def test_validate_invalid_rule_type(self):
        """Test validation with invalid rule type."""
        rules = [
            {
                "name": "test_rule",
                "type": "invalid_type",
                "field": "test_field"
            }
        ]
        
        issues = validate_rule_configuration(rules)
        assert len(issues) >= 1
        assert any("Invalid rule type" in issue for issue in issues)
    
    def test_validate_invalid_severity(self):
        """Test validation with invalid severity."""
        rules = [
            {
                "name": "test_rule",
                "type": "required_field",
                "field": "test_field",
                "severity": "invalid_severity"
            }
        ]
        
        issues = validate_rule_configuration(rules)
        assert len(issues) >= 1
        assert any("Invalid severity" in issue for issue in issues)


class TestMergeValidationReports:
    """Test cases for merge_validation_reports function."""
    
    def test_merge_reports(self):
        """Test merging multiple validation reports."""
        report1 = ValidationReport(
            total_records=10,
            total_rules=2,
            passed_validations=8,
            failed_validations=2,
            results=[Mock(passed=True), Mock(passed=False)],
            summary_by_severity={ValidationSeverity.ERROR: 1, ValidationSeverity.WARNING: 1}
        )
        
        report2 = ValidationReport(
            total_records=5,
            total_rules=2,
            passed_validations=4,
            failed_validations=1,
            results=[Mock(passed=True), Mock(passed=False)],
            summary_by_severity={ValidationSeverity.ERROR: 1}
        )
        
        merged = merge_validation_reports(report1, report2)
        
        assert merged.total_records == 15
        assert merged.total_rules == 2  # Max of the two
        assert merged.passed_validations == 2  # Count of passed results
        assert merged.failed_validations == 2  # Count of failed results
        assert len(merged.results) == 4
        assert merged.summary_by_severity[ValidationSeverity.ERROR] == 2
        assert merged.summary_by_severity[ValidationSeverity.WARNING] == 1
    
    def test_merge_no_reports(self):
        """Test merging with no reports provided."""
        with pytest.raises(ValidationAPIError) as exc_info:
            merge_validation_reports()
        
        assert "No reports provided for merging" in str(exc_info.value)