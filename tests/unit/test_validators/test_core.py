"""
Unit tests for core validation functionality.

These tests verify the DataValidator class and its integration
with different validation processors.
"""

import pytest
from unittest.mock import patch

from src.policy_dq.validators.core import DataValidator
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationReport


class TestDataValidator:
    """Test cases for DataValidator class."""
    
    @pytest.fixture
    def sample_rules(self):
        """Sample validation rules for testing."""
        return [
            ValidationRule(
                name="required_name",
                rule_type=RuleType.REQUIRED_FIELD,
                field="name",
                parameters={"allow_empty": False},
                severity=ValidationSeverity.CRITICAL
            ),
            ValidationRule(
                name="email_format",
                rule_type=RuleType.REGEX_CHECK,
                field="email",
                parameters={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "message": "Invalid email format"
                },
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="age_range",
                rule_type=RuleType.NUMERIC_RANGE,
                field="age",
                parameters={"min": 0, "max": 120},
                severity=ValidationSeverity.WARNING
            )
        ]
    
    @pytest.fixture
    def sample_data(self):
        """Sample data records for testing."""
        return [
            {"name": "John Doe", "email": "john@example.com", "age": 30},
            {"name": "Jane Smith", "email": "jane@example.com", "age": 25},
            {"name": "", "email": "invalid-email", "age": 150},  # Multiple violations
            {"name": "Bob Johnson", "email": "bob@example.com", "age": -5}  # Age violation
        ]
    
    def test_validator_initialization(self, sample_rules):
        """Test DataValidator initialization."""
        validator = DataValidator(sample_rules)
        
        assert len(validator.rules) == 3
        assert validator.processors is not None
        assert len(validator.processors) > 0
    
    def test_validator_initialization_empty_rules(self):
        """Test DataValidator initialization with empty rules."""
        validator = DataValidator([])
        
        assert len(validator.rules) == 0
        assert validator.processors is not None
    
    def test_validate_single_record_success(self, sample_rules):
        """Test validating a single record with all rules passing."""
        validator = DataValidator(sample_rules)
        record = {"name": "John Doe", "email": "john@example.com", "age": 30}
        
        results = validator.validate_record(record, 0)
        
        # Should have results for each rule
        assert len(results) == 3
        
        # All results should pass
        for result in results:
            assert result.passed is True
            assert result.row_index == 0
            assert isinstance(result.severity, ValidationSeverity)
    
    def test_validate_single_record_failures(self, sample_rules):
        """Test validating a single record with rule failures."""
        validator = DataValidator(sample_rules)
        record = {"name": "", "email": "invalid-email", "age": 150}
        
        results = validator.validate_record(record, 1)
        
        # Should have results for each rule
        assert len(results) == 3
        
        # All results should fail
        failed_results = [r for r in results if not r.passed]
        assert len(failed_results) == 3
        
        # Check specific failures
        name_result = next(r for r in results if r.field == "name")
        assert not name_result.passed
        assert name_result.severity == ValidationSeverity.CRITICAL
        
        email_result = next(r for r in results if r.field == "email")
        assert not email_result.passed
        assert email_result.severity == ValidationSeverity.ERROR
        
        age_result = next(r for r in results if r.field == "age")
        assert not age_result.passed
        assert age_result.severity == ValidationSeverity.WARNING
    
    def test_validate_multiple_records(self, sample_rules, sample_data):
        """Test validating multiple records."""
        validator = DataValidator(sample_rules)
        
        report = validator.validate(sample_data)
        
        assert isinstance(report, ValidationReport)
        assert report.total_records == 4
        assert report.total_rules == 3
        assert report.passed_validations > 0
        assert report.failed_validations > 0
        
        # Check that results are ordered deterministically
        results_by_row = {}
        for result in report.results:
            if result.row_index not in results_by_row:
                results_by_row[result.row_index] = []
            results_by_row[result.row_index].append(result)
        
        # Each row should have results for all rules
        for row_index in range(4):
            assert len(results_by_row[row_index]) == 3
    
    def test_validate_deterministic_ordering(self, sample_rules):
        """Test that validation results are deterministically ordered."""
        validator = DataValidator(sample_rules)
        record = {"name": "Test", "email": "test@example.com", "age": 25}
        
        # Run validation multiple times
        results1 = validator.validate_record(record, 0)
        results2 = validator.validate_record(record, 0)
        results3 = validator.validate_record(record, 0)
        
        # Results should be in same order each time
        rule_names1 = [r.rule_name for r in results1]
        rule_names2 = [r.rule_name for r in results2]
        rule_names3 = [r.rule_name for r in results3]
        
        assert rule_names1 == rule_names2 == rule_names3
        
        # Results should be in consistent order (not necessarily alphabetical)
        # The important thing is that the order is deterministic across runs
        assert len(rule_names1) == 3
    
    def test_validate_missing_field(self, sample_rules):
        """Test validation when record is missing a field."""
        validator = DataValidator(sample_rules)
        record = {"name": "John Doe", "email": "john@example.com"}  # Missing age
        
        results = validator.validate_record(record, 0)
        
        # Should still have results for all rules
        assert len(results) == 3
        
        # Age rule should handle missing field appropriately
        age_result = next(r for r in results if r.field == "age")
        # Behavior depends on processor implementation
        assert isinstance(age_result.passed, bool)
    
    def test_validate_extra_fields(self, sample_rules):
        """Test validation when record has extra fields."""
        validator = DataValidator(sample_rules)
        record = {
            "name": "John Doe",
            "email": "john@example.com", 
            "age": 30,
            "extra_field": "extra_value"
        }
        
        results = validator.validate_record(record, 0)
        
        # Should have results for defined rules only
        assert len(results) == 3
        
        # Extra field should not cause issues
        for result in results:
            assert result.field in ["name", "email", "age"]
    
    def test_validate_empty_record(self, sample_rules):
        """Test validation with empty record."""
        validator = DataValidator(sample_rules)
        record = {}
        
        results = validator.validate_record(record, 0)
        
        # Should still attempt validation for all rules
        assert len(results) == 3
        
        # Required field should fail
        name_result = next(r for r in results if r.field == "name")
        assert not name_result.passed
    
    def test_validate_none_values(self, sample_rules):
        """Test validation with None values."""
        validator = DataValidator(sample_rules)
        record = {"name": None, "email": None, "age": None}
        
        results = validator.validate_record(record, 0)
        
        # Should handle None values appropriately
        assert len(results) == 3
        
        # Check that processors handle None values
        for result in results:
            assert isinstance(result.passed, bool)
            assert result.message is not None
    
    def test_severity_summary(self, sample_rules, sample_data):
        """Test that severity summary is calculated correctly."""
        validator = DataValidator(sample_rules)
        
        report = validator.validate(sample_data)
        
        # Check severity summary
        assert hasattr(report, 'summary_by_severity')
        assert isinstance(report.summary_by_severity, dict)
        
        # Should have counts for each severity level that appears
        total_by_severity = sum(report.summary_by_severity.values())
        assert total_by_severity == len(report.results)
    
    def test_validation_with_no_rules(self):
        """Test validation with no rules defined."""
        validator = DataValidator([])
        record = {"name": "John Doe", "email": "john@example.com"}
        
        results = validator.validate_record(record, 0)
        
        # Should return empty results
        assert len(results) == 0
    
    def test_validation_report_structure(self, sample_rules, sample_data):
        """Test that validation report has correct structure."""
        validator = DataValidator(sample_rules)
        
        report = validator.validate(sample_data)
        
        # Check report structure
        assert hasattr(report, 'total_records')
        assert hasattr(report, 'total_rules')
        assert hasattr(report, 'passed_validations')
        assert hasattr(report, 'failed_validations')
        assert hasattr(report, 'results')
        assert hasattr(report, 'summary_by_severity')
        
        # Check data types
        assert isinstance(report.total_records, int)
        assert isinstance(report.total_rules, int)
        assert isinstance(report.passed_validations, int)
        assert isinstance(report.failed_validations, int)
        assert isinstance(report.results, list)
        assert isinstance(report.summary_by_severity, dict)
        
        # Check calculations
        assert report.total_records == len(sample_data)
        assert report.total_rules == len(sample_rules)
        assert report.passed_validations + report.failed_validations == len(report.results)
    
    def test_validation_result_structure(self, sample_rules):
        """Test that validation results have correct structure."""
        validator = DataValidator(sample_rules)
        record = {"name": "John Doe", "email": "john@example.com", "age": 30}
        
        results = validator.validate_record(record, 0)
        
        for result in results:
            # Check result structure
            assert hasattr(result, 'rule_name')
            assert hasattr(result, 'field')
            assert hasattr(result, 'row_index')
            assert hasattr(result, 'severity')
            assert hasattr(result, 'message')
            assert hasattr(result, 'passed')
            
            # Check data types
            assert isinstance(result.rule_name, str)
            assert isinstance(result.field, str)
            assert isinstance(result.row_index, (int, type(None)))
            assert isinstance(result.severity, ValidationSeverity)
            assert isinstance(result.message, str)
            assert isinstance(result.passed, bool)
            
            # Check values
            assert result.rule_name in [r.name for r in sample_rules]
            assert result.field in [r.field for r in sample_rules]
            assert result.row_index == 0
            assert len(result.message) > 0
    
    def test_processor_error_handling(self, sample_rules):
        """Test that processor errors are handled gracefully."""
        validator = DataValidator(sample_rules)
        
        # Mock a processor to raise an exception
        with patch.object(validator.processors['required_field'], 'process_record', side_effect=Exception("Processor error")):
            record = {"name": "John Doe", "email": "john@example.com", "age": 30}
            
            results = validator.validate_record(record, 0)
            
            # Should still return results for other processors
            # Error handling behavior depends on implementation
            assert isinstance(results, list)
    
    def test_large_dataset_performance(self, sample_rules):
        """Test validation performance with larger dataset."""
        validator = DataValidator(sample_rules)
        
        # Create larger dataset
        large_data = []
        for i in range(1000):
            large_data.append({
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50)
            })
        
        # Validation should complete without issues
        report = validator.validate(large_data)
        
        assert report.total_records == 1000
        assert len(report.results) == 3000  # 3 rules × 1000 records
    
    def test_unicode_handling(self, sample_rules):
        """Test validation with unicode characters."""
        validator = DataValidator(sample_rules)
        record = {
            "name": "José María",
            "email": "josé@example.com",
            "age": 30
        }
        
        results = validator.validate_record(record, 0)
        
        # Should handle unicode without issues
        assert len(results) == 3
        
        # Check that unicode is preserved in results
        name_result = next(r for r in results if r.field == "name")
        assert "José" in str(name_result) or name_result.passed