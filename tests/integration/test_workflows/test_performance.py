"""
Performance tests for the validation system.

These tests verify that the system performs well with larger datasets
and maintains deterministic behavior under load.
"""

import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.policy_dq.engine import ValidationEngine
from src.policy_dq.config import ValidationConfig, RuleSourceConfig, OutputConfig
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity


class TestPerformance:
    """Performance tests for validation system."""
    
    @pytest.fixture
    def performance_config(self):
        """Configuration optimized for performance testing."""
        rule_source = RuleSourceConfig(source="test_rules")
        output_config = OutputConfig(
            generate_console_report=False,
            generate_json_report=False,
            generate_markdown_report=False
        )
        return ValidationConfig(rule_source=rule_source, output=output_config)
    
    @pytest.fixture
    def sample_rules(self):
        """Sample rules for performance testing."""
        return [
            ValidationRule(
                name="required_name",
                rule_type=RuleType.REQUIRED_FIELD,
                field="name",
                parameters={},
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="email_format",
                rule_type=RuleType.REGEX_CHECK,
                field="email",
                parameters={"pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"},
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="age_range",
                rule_type=RuleType.NUMERIC_RANGE,
                field="age",
                parameters={"min_value": 0, "max_value": 120},
                severity=ValidationSeverity.WARNING
            )
        ]
    
    def generate_large_dataset(self, size):
        """Generate large dataset for performance testing."""
        data = []
        for i in range(size):
            data.append({
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50)
            })
        return data
    
    def test_small_dataset_performance(self, performance_config, sample_rules):
        """Test performance with small dataset (should be very fast)."""
        data = self.generate_large_dataset(100)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                start_time = time.time()
                report = engine.validate_data(data)
                end_time = time.time()
                
                # Should complete very quickly
                execution_time = end_time - start_time
                assert execution_time < 1.0, f"Small dataset took {execution_time:.2f}s, expected < 1.0s"
                
                # Verify results
                assert report.total_records == 100
                assert len(report.results) == 300  # 3 rules × 100 records
    
    def test_medium_dataset_performance(self, performance_config, sample_rules):
        """Test performance with medium dataset."""
        data = self.generate_large_dataset(1000)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                start_time = time.time()
                report = engine.validate_data(data)
                end_time = time.time()
                
                # Should complete reasonably quickly
                execution_time = end_time - start_time
                assert execution_time < 5.0, f"Medium dataset took {execution_time:.2f}s, expected < 5.0s"
                
                # Verify results
                assert report.total_records == 1000
                assert len(report.results) == 3000  # 3 rules × 1000 records
    
    def test_large_dataset_performance(self, performance_config, sample_rules):
        """Test performance with large dataset."""
        data = self.generate_large_dataset(5000)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                start_time = time.time()
                report = engine.validate_data(data)
                end_time = time.time()
                
                # Should complete within reasonable time
                execution_time = end_time - start_time
                assert execution_time < 30.0, f"Large dataset took {execution_time:.2f}s, expected < 30.0s"
                
                # Verify results
                assert report.total_records == 5000
                assert len(report.results) == 15000  # 3 rules × 5000 records
    
    def test_performance_consistency(self, performance_config, sample_rules):
        """Test that performance is consistent across multiple runs."""
        data = self.generate_large_dataset(500)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                execution_times = []
                
                # Run validation multiple times
                for _ in range(5):
                    start_time = time.time()
                    report = engine.validate_data(data)
                    end_time = time.time()
                    
                    execution_times.append(end_time - start_time)
                    
                    # Verify consistent results
                    assert report.total_records == 500
                    assert len(report.results) == 1500
                
                # Check performance consistency with dynamic threshold
                avg_time = sum(execution_times) / len(execution_times)
                max_time = max(execution_times)
                min_time = min(execution_times)
                
                # Calculate dynamic threshold based on average time
                # Allow more variation for slower systems
                base_threshold = 0.5
                if avg_time > 0.1:  # If average time is high, allow more variation
                    dynamic_threshold = min(1.0, base_threshold + (avg_time * 2))
                elif avg_time < 0.01:  # If average time is very low, allow more variation due to timing precision
                    dynamic_threshold = min(1.5, base_threshold + 1.0)
                else:
                    dynamic_threshold = base_threshold
                
                # Performance should be relatively consistent
                variation = (max_time - min_time) / avg_time if avg_time > 0 else 0
                assert variation < dynamic_threshold, f"Performance variation too high: {variation:.2f}, threshold: {dynamic_threshold:.2f}, avg_time: {avg_time:.3f}s"
    
    def test_memory_efficiency_large_dataset(self, performance_config, sample_rules):
        """Test memory efficiency with large dataset."""
        # This test verifies that memory usage doesn't grow excessively
        data = self.generate_large_dataset(2000)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                # Run validation and verify it completes without memory issues
                try:
                    report = engine.validate_data(data)
                    
                    # Verify results
                    assert report.total_records == 2000
                    assert len(report.results) == 6000
                    
                    # If we get here, memory usage was acceptable
                    assert True
                    
                except MemoryError:
                    pytest.fail("Validation failed due to excessive memory usage")
    
    def test_deterministic_performance(self, performance_config, sample_rules):
        """Test that deterministic ordering doesn't significantly impact performance."""
        data = self.generate_large_dataset(1000)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                # Time multiple runs to ensure deterministic ordering doesn't slow things down
                times = []
                result_orders = []
                
                for _ in range(3):
                    start_time = time.time()
                    report = engine.validate_data(data)
                    end_time = time.time()
                    
                    times.append(end_time - start_time)
                    result_orders.append([r.rule_name for r in report.results])
                
                # Verify results are deterministic
                assert result_orders[0] == result_orders[1] == result_orders[2]
                
                # Verify performance is still good
                avg_time = sum(times) / len(times)
                assert avg_time < 10.0, f"Deterministic ordering caused slowdown: {avg_time:.2f}s"
    
    def test_rule_complexity_performance(self, performance_config):
        """Test performance with complex rules."""
        # Create more complex rules
        complex_rules = [
            ValidationRule(
                name="complex_email",
                rule_type=RuleType.REGEX_CHECK,
                field="email",
                parameters={"pattern": r"^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])$"},
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="required_name",
                rule_type=RuleType.REQUIRED_FIELD,
                field="name",
                parameters={},
                severity=ValidationSeverity.CRITICAL
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
                parameters={"pattern": r"^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$"},
                severity=ValidationSeverity.WARNING
            )
        ]
        
        # Generate data with phone field
        data = []
        for i in range(500):
            data.append({
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "age": 20 + (i % 50),
                "phone": f"555-{i:03d}-{(i*7) % 10000:04d}"
            })
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=complex_rules):
                engine = ValidationEngine(performance_config)
                
                start_time = time.time()
                report = engine.validate_data(data)
                end_time = time.time()
                
                # Should still complete in reasonable time despite complex rules
                execution_time = end_time - start_time
                assert execution_time < 15.0, f"Complex rules took {execution_time:.2f}s, expected < 15.0s"
                
                # Verify results
                assert report.total_records == 500
                assert len(report.results) == 2000  # 4 rules × 500 records
    
    def test_single_record_validation_performance(self, performance_config, sample_rules):
        """Test performance of single record validation."""
        record = {"name": "John Doe", "email": "john@example.com", "age": 30}
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                # Time many single record validations
                start_time = time.time()
                
                for _ in range(1000):
                    results = engine.validate_record(record)
                    assert len(results) == 3  # 3 rules
                
                end_time = time.time()
                
                # Should complete quickly
                execution_time = end_time - start_time
                assert execution_time < 2.0, f"1000 single record validations took {execution_time:.2f}s"
                
                # Average time per record should be very small
                avg_time_per_record = execution_time / 1000
                assert avg_time_per_record < 0.002, f"Average time per record: {avg_time_per_record:.4f}s"
    
    def test_file_parsing_performance(self, performance_config, sample_rules):
        """Test file parsing performance with large files."""
        # Generate large dataset
        data = self.generate_large_dataset(2000)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_file = f.name
        
        try:
            with patch.object(ValidationEngine, '_create_rule_manager'):
                with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                    engine = ValidationEngine(performance_config)
                    
                    start_time = time.time()
                    report = engine.validate_file(temp_file)
                    end_time = time.time()
                    
                    # Should complete within reasonable time including file parsing
                    execution_time = end_time - start_time
                    assert execution_time < 20.0, f"File validation took {execution_time:.2f}s"
                    
                    # Verify results
                    assert report.total_records == 2000
                    assert len(report.results) == 6000
        
        finally:
            # Clean up temp file
            Path(temp_file).unlink()
    
    def test_concurrent_validation_performance(self, performance_config, sample_rules):
        """Test that validation can handle concurrent-like usage patterns."""
        data = self.generate_large_dataset(200)
        
        with patch.object(ValidationEngine, '_create_rule_manager'):
            with patch.object(ValidationEngine, '_load_rules', return_value=sample_rules):
                engine = ValidationEngine(performance_config)
                
                # Simulate concurrent usage by running multiple validations quickly
                start_time = time.time()
                
                reports = []
                for _ in range(10):
                    report = engine.validate_data(data)
                    reports.append(report)
                
                end_time = time.time()
                
                # Should handle multiple validations efficiently
                execution_time = end_time - start_time
                assert execution_time < 10.0, f"10 concurrent validations took {execution_time:.2f}s"
                
                # All reports should be identical (deterministic)
                for report in reports[1:]:
                    assert report.total_records == reports[0].total_records
                    assert report.failed_validations == reports[0].failed_validations
                    assert len(report.results) == len(reports[0].results)