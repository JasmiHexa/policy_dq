"""
Tests for the uniqueness validation processor.
"""


from src.policy_dq.validators.processors.uniqueness import UniquenessProcessor
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity


class TestUniquenessProcessor:
    """Test cases for the UniquenessProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = UniquenessProcessor()
    
    def create_rule(self, field_name: str, **parameters) -> ValidationRule:
        """Helper to create a uniqueness validation rule."""
        return ValidationRule(
            name=f"{field_name}_uniqueness_check",
            rule_type=RuleType.UNIQUENESS,
            field=field_name,
            parameters=parameters,
            severity=ValidationSeverity.ERROR
        )
    
    def test_can_process_uniqueness_rule(self):
        """Test that processor can handle uniqueness rules."""
        rule = self.create_rule("customer_id")
        assert self.processor.can_process(rule) is True
    
    def test_can_process_other_rule_types(self):
        """Test that processor rejects other rule types."""
        other_rule = ValidationRule(
            name="required_field",
            rule_type=RuleType.REQUIRED_FIELD,
            field="customer_id",
            parameters={},
            severity=ValidationSeverity.ERROR
        )
        
        assert self.processor.can_process(other_rule) is False
    
    def test_process_record_without_all_records(self):
        """Test that process_record fails without all_records parameter."""
        rule = self.create_rule("customer_id")
        record = {"customer_id": "123"}
        
        result = self.processor.process_record(rule, record, 0)
        
        assert result.passed is False
        assert "requires access to all records" in result.message
    
    def test_process_dataset_all_unique(self):
        """Test validation when all values are unique."""
        rule = self.create_rule("customer_id")
        records = [
            {"customer_id": "123"},
            {"customer_id": "456"},
            {"customer_id": "789"},
            {"customer_id": "ABC"},
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 4
        for result in results:
            assert result.passed is True
            assert "is unique" in result.message
    
    def test_process_dataset_with_duplicates(self):
        """Test validation when there are duplicate values."""
        rule = self.create_rule("customer_id")
        records = [
            {"customer_id": "123"},  # First occurrence - should fail
            {"customer_id": "456"},  # Unique - should pass
            {"customer_id": "123"},  # Duplicate - should fail
            {"customer_id": "789"},  # Unique - should pass
            {"customer_id": "456"},  # Duplicate - should fail
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 5
        assert results[0].passed is False  # First "123"
        assert results[1].passed is False  # First "456" (has duplicate later)
        assert results[2].passed is False  # Second "123"
        assert results[3].passed is True   # "789" is unique
        assert results[4].passed is False  # Second "456"
        
        # Check error messages
        assert "is not unique" in results[0].message
        assert "is not unique" in results[2].message
        assert "is not unique" in results[4].message
    
    def test_process_dataset_missing_field(self):
        """Test validation when field is missing from some records."""
        rule = self.create_rule("customer_id")
        records = [
            {"customer_id": "123"},
            {"name": "John"},  # Missing customer_id
            {"customer_id": "456"},
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 3
        assert results[0].passed is True   # "123" is unique
        assert results[1].passed is False  # Missing field
        assert results[2].passed is True   # "456" is unique
        
        assert "is missing for uniqueness validation" in results[1].message
    
    def test_process_dataset_with_none_values_ignore(self):
        """Test validation with None values when ignore_none=True (default)."""
        rule = self.create_rule("customer_id")  # Default ignore_none=True
        records = [
            {"customer_id": "123"},
            {"customer_id": None},
            {"customer_id": "456"},
            {"customer_id": None},  # Multiple None values should be ignored
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 4
        assert results[0].passed is True  # "123" is unique
        assert results[1].passed is True  # None is ignored
        assert results[2].passed is True  # "456" is unique
        assert results[3].passed is True  # None is ignored
        
        assert "is None, skipping uniqueness validation" in results[1].message
        assert "is None, skipping uniqueness validation" in results[3].message
    
    def test_process_dataset_with_none_values_no_ignore(self):
        """Test validation with None values when ignore_none=False."""
        rule = self.create_rule("customer_id", ignore_none=False)
        records = [
            {"customer_id": "123"},
            {"customer_id": None},
            {"customer_id": "456"},
            {"customer_id": None},  # Duplicate None - should fail
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 4
        assert results[0].passed is True   # "123" is unique
        assert results[1].passed is False  # First None (has duplicate)
        assert results[2].passed is True   # "456" is unique
        assert results[3].passed is False  # Second None (duplicate)
        
        assert "is not unique" in results[1].message
        assert "is not unique" in results[3].message
    
    def test_case_sensitive_uniqueness_default(self):
        """Test case-sensitive uniqueness validation (default behavior)."""
        rule = self.create_rule("email")  # Default case_sensitive=True
        records = [
            {"email": "user@example.com"},
            {"email": "USER@EXAMPLE.COM"},  # Different case - should be unique
            {"email": "user@example.com"},  # Exact duplicate - should fail
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 3
        assert results[0].passed is False  # First occurrence of duplicate
        assert results[1].passed is True   # Different case - unique
        assert results[2].passed is False  # Exact duplicate
    
    def test_case_insensitive_uniqueness(self):
        """Test case-insensitive uniqueness validation."""
        rule = self.create_rule("email", case_sensitive=False)
        records = [
            {"email": "user@example.com"},
            {"email": "USER@EXAMPLE.COM"},  # Same when case-insensitive - should fail
            {"email": "other@example.com"}, # Different - should be unique
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 3
        assert results[0].passed is False  # First occurrence of duplicate
        assert results[1].passed is False  # Case-insensitive duplicate
        assert results[2].passed is True   # Different email - unique
    
    def test_non_string_values(self):
        """Test uniqueness validation with non-string values."""
        rule = self.create_rule("id")
        records = [
            {"id": 123},
            {"id": 456},
            {"id": 123},    # Duplicate number
            {"id": True},
            {"id": False},
            {"id": True},   # Duplicate boolean
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 6
        assert results[0].passed is False  # First 123 (has duplicate)
        assert results[1].passed is True   # 456 is unique
        assert results[2].passed is False  # Second 123 (duplicate)
        assert results[3].passed is False  # First True (has duplicate)
        assert results[4].passed is True   # False is unique
        assert results[5].passed is False  # Second True (duplicate)
    
    def test_mixed_type_values(self):
        """Test uniqueness validation with mixed data types."""
        rule = self.create_rule("value")
        records = [
            {"value": "123"},
            {"value": 123},     # Different type - should be unique
            {"value": "123"},   # String duplicate
            {"value": 124},     # Different value - should be unique
        ]
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 4
        assert results[0].passed is False  # First "123" (has duplicate)
        assert results[1].passed is True   # 123 (int) is unique
        assert results[2].passed is False  # Second "123" (duplicate)
        assert results[3].passed is True   # 124 (int) is unique
    
    def test_process_record_with_all_records(self):
        """Test process_record when all_records is provided."""
        rule = self.create_rule("customer_id")
        records = [
            {"customer_id": "123"},
            {"customer_id": "456"},
            {"customer_id": "123"},  # Duplicate
        ]
        
        # Test processing the first record (which has a duplicate)
        result = self.processor.process_record(rule, records[0], 0, records)
        assert result.passed is False
        assert "is not unique" in result.message
        
        # Test processing the second record (which is unique)
        result = self.processor.process_record(rule, records[1], 1, records)
        assert result.passed is True
        assert "is unique" in result.message
    
    def test_process_record_out_of_range_index(self):
        """Test process_record with an out-of-range index."""
        rule = self.create_rule("customer_id")
        records = [{"customer_id": "123"}]
        record = {"customer_id": "456"}
        
        result = self.processor.process_record(rule, record, 5, records)  # Index 5 is out of range
        
        assert result.passed is False
        assert "Record index 5 out of range" in result.message
    
    def test_large_dataset_performance(self):
        """Test uniqueness validation with a larger dataset."""
        rule = self.create_rule("id")
        
        # Create a dataset with 1000 unique records and a few duplicates
        records = []
        for i in range(1000):
            records.append({"id": f"unique_{i}"})
        
        # Add some duplicates
        records.append({"id": "unique_0"})    # Duplicate of first
        records.append({"id": "unique_500"})  # Duplicate of middle
        records.append({"id": "unique_999"})  # Duplicate of last
        
        results = self.processor.process_dataset(rule, records)
        
        assert len(results) == 1003
        
        # Check that the original records with duplicates are marked as failed
        assert results[0].passed is False    # unique_0 has duplicate
        assert results[500].passed is False  # unique_500 has duplicate
        assert results[999].passed is False  # unique_999 has duplicate
        
        # Check that the duplicate records are marked as failed
        assert results[1000].passed is False  # Duplicate of unique_0
        assert results[1001].passed is False  # Duplicate of unique_500
        assert results[1002].passed is False  # Duplicate of unique_999
        
        # Check that some unique records pass
        assert results[1].passed is True     # unique_1 is unique
        assert results[250].passed is True   # unique_250 is unique
    
    def test_normalize_value_method(self):
        """Test the _normalize_value helper method."""
        # Case sensitive (default)
        assert self.processor._normalize_value("Test", True) == "Test"
        assert self.processor._normalize_value("TEST", True) == "TEST"
        assert self.processor._normalize_value(123, True) == 123
        
        # Case insensitive
        assert self.processor._normalize_value("Test", False) == "test"
        assert self.processor._normalize_value("TEST", False) == "test"
        assert self.processor._normalize_value(123, False) == 123  # Non-string unchanged