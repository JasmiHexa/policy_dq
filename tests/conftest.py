"""
Shared pytest configuration and fixtures for the test suite.

This module provides common fixtures and configuration for all tests
to ensure consistent, readable, and deterministic test execution.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType, ValidationReport, ValidationResult


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_validation_rules():
    """Standard set of validation rules for testing."""
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
            parameters={"min_value": 0, "max_value": 120},
            severity=ValidationSeverity.WARNING
        ),
        ValidationRule(
            name="phone_format",
            rule_type=RuleType.REGEX_CHECK,
            field="phone",
            parameters={
                "pattern": r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"
            },
            severity=ValidationSeverity.INFO
        )
    ]


@pytest.fixture
def sample_data_records():
    """Standard set of data records for testing."""
    return [
        {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "phone": "555-123-4567"
        },
        {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25,
            "phone": "(555) 987-6543"
        },
        {
            "name": "",  # Invalid: empty name
            "email": "invalid-email",  # Invalid: bad email format
            "age": 150,  # Invalid: age out of range
            "phone": "not-a-phone"  # Invalid: bad phone format
        },
        {
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "age": -5,  # Invalid: negative age
            "phone": "555.321.9876"
        }
    ]


@pytest.fixture
def sample_validation_results():
    """Standard set of validation results for testing."""
    return [
        ValidationResult(
            rule_name="required_name",
            field="name",
            row_index=2,
            severity=ValidationSeverity.CRITICAL,
            message="Name is required and cannot be empty",
            passed=False
        ),
        ValidationResult(
            rule_name="email_format",
            field="email",
            row_index=2,
            severity=ValidationSeverity.ERROR,
            message="Invalid email format: 'invalid-email'",
            passed=False
        ),
        ValidationResult(
            rule_name="age_range",
            field="age",
            row_index=2,
            severity=ValidationSeverity.WARNING,
            message="Age value 150 is outside the valid range (0-120)",
            passed=False
        ),
        ValidationResult(
            rule_name="age_range",
            field="age",
            row_index=3,
            severity=ValidationSeverity.WARNING,
            message="Age value -5 is outside the valid range (0-120)",
            passed=False
        ),
        ValidationResult(
            rule_name="phone_format",
            field="phone",
            row_index=2,
            severity=ValidationSeverity.INFO,
            message="Phone number format is invalid",
            passed=False
        )
    ]


@pytest.fixture
def sample_validation_report(sample_validation_results):
    """Standard validation report for testing."""
    return ValidationReport(
        total_records=4,
        total_rules=4,
        passed_validations=11,  # 4 records × 4 rules - 5 failures
        failed_validations=5,
        results=sample_validation_results,
        summary_by_severity={
            ValidationSeverity.CRITICAL: 1,
            ValidationSeverity.ERROR: 1,
            ValidationSeverity.WARNING: 2,
            ValidationSeverity.INFO: 1
        }
    )


@pytest.fixture
def sample_rules_json():
    """Standard rules JSON structure for testing."""
    return {
        "version": "1.0",
        "rule_sets": [
            {
                "name": "customer_validation",
                "rules": [
                    {
                        "name": "required_name",
                        "type": "required_field",
                        "field": "name",
                        "parameters": {"allow_empty": False},
                        "severity": "critical"
                    },
                    {
                        "name": "email_format",
                        "type": "regex_check",
                        "field": "email",
                        "parameters": {
                            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                            "message": "Invalid email format"
                        },
                        "severity": "error"
                    },
                    {
                        "name": "age_range",
                        "type": "numeric_range",
                        "field": "age",
                        "parameters": {
                            "min_value": 0,
                            "max_value": 120
                        },
                        "severity": "warning"
                    }
                ]
            }
        ]
    }


@pytest.fixture
def create_temp_csv_file(temp_directory):
    """Factory fixture to create temporary CSV files."""
    def _create_csv_file(data, filename="test_data.csv"):
        file_path = Path(temp_directory) / filename
        
        if data:
            # Extract headers from first record
            headers = list(data[0].keys())
            
            # Write CSV content
            lines = [",".join(headers)]
            for record in data:
                values = [str(record.get(header, "")) for header in headers]
                lines.append(",".join(values))
            
            file_path.write_text("\n".join(lines))
        else:
            # Empty CSV with just headers
            file_path.write_text("name,email,age,phone\n")
        
        return str(file_path)
    
    return _create_csv_file


@pytest.fixture
def create_temp_json_file(temp_directory):
    """Factory fixture to create temporary JSON files."""
    def _create_json_file(data, filename="test_data.json"):
        file_path = Path(temp_directory) / filename
        file_path.write_text(json.dumps(data, indent=2))
        return str(file_path)
    
    return _create_json_file


@pytest.fixture
def create_temp_rules_file(temp_directory):
    """Factory fixture to create temporary rules files."""
    def _create_rules_file(rules_data, filename="test_rules.json"):
        file_path = Path(temp_directory) / filename
        file_path.write_text(json.dumps(rules_data, indent=2))
        return str(file_path)
    
    return _create_rules_file


@pytest.fixture
def mock_validation_engine():
    """Mock ValidationEngine for testing."""
    engine = Mock()
    engine.config = Mock()
    engine.validate_file = Mock()
    engine.validate_data = Mock()
    engine.validate_record = Mock()
    engine.check_severity_threshold = Mock()
    engine.get_failed_results = Mock()
    engine.filter_results_by_severity = Mock()
    return engine


@pytest.fixture
def mock_rule_loader():
    """Mock RuleLoader for testing."""
    loader = Mock()
    loader.load_rules = Mock()
    loader.validate_source = Mock()
    return loader


@pytest.fixture
def mock_validation_processor():
    """Mock ValidationProcessor for testing."""
    processor = Mock()
    processor.process = Mock()
    return processor


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add integration marker to integration tests
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        # Add slow marker to tests that might take longer
        if any(keyword in item.name.lower() for keyword in ["large", "performance", "concurrent"]):
            item.add_marker(pytest.mark.slow)


# Ensure deterministic test execution
@pytest.fixture(autouse=True)
def ensure_deterministic_execution():
    """Ensure tests run deterministically."""
    # This fixture runs automatically for all tests
    # Can be used to set up deterministic conditions
    import random
    random.seed(42)  # Fixed seed for any random operations
    
    yield
    
    # Cleanup after test if needed


# Performance test configuration
@pytest.fixture
def performance_threshold():
    """Performance thresholds for different test categories."""
    return {
        "small_dataset": 1.0,    # seconds
        "medium_dataset": 5.0,   # seconds
        "large_dataset": 30.0,   # seconds
        "single_record": 0.001,  # seconds
        "file_parsing": 10.0     # seconds
    }


# Test data generators
@pytest.fixture
def generate_test_data():
    """Factory to generate test data of various sizes."""
    def _generate_data(size, include_invalid=True):
        data = []
        for i in range(size):
            record = {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
                "phone": f"555-{i:03d}-{(i*7) % 10000:04d}"
            }
            
            # Add some invalid records if requested
            if include_invalid and i % 10 == 0:
                if i % 30 == 0:
                    record["name"] = ""  # Invalid name
                if i % 20 == 0:
                    record["email"] = "invalid-email"  # Invalid email
                if i % 40 == 0:
                    record["age"] = 150  # Invalid age
            
            data.append(record)
        
        return data
    
    return _generate_data