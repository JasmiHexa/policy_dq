"""
Uniqueness validation processor.

This module implements validation for field uniqueness, ensuring that
specified field values are unique across all records in the dataset.
"""

from typing import Any, Dict, List, Optional, Set

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class UniquenessProcessor(RuleProcessor):
    """
    Processor for uniqueness validation rules.
    
    Validates that field values are unique across all records in the dataset.
    Supports case-sensitive and case-insensitive uniqueness checks, and handles
    None values appropriately.
    """
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a uniqueness rule, False otherwise
        """
        return rule.rule_type == RuleType.UNIQUENESS
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for uniqueness validation.
        
        This method requires all_records to be provided for cross-record validation.
        It's more efficient to use process_dataset for uniqueness validation.
        
        Args:
            rule: The validation rule to apply
            record: The data record to validate
            record_index: Index of the record in the dataset
            all_records: All records in the dataset (required for uniqueness validation)
            
        Returns:
            ValidationResult indicating success or failure
        """
        if all_records is None:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message="Uniqueness validation requires access to all records in the dataset"
            )
        
        # Use the more efficient dataset processing method
        all_results = self.process_dataset(rule, all_records)
        
        # Return the result for this specific record
        if record_index < len(all_results):
            return all_results[record_index]
        else:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Record index {record_index} out of range"
            )
    
    def process_dataset(
        self, 
        rule: ValidationRule, 
        records: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Process all records in a dataset for uniqueness validation.
        
        This is the preferred method for uniqueness validation as it's more efficient
        than processing records individually.
        
        Args:
            rule: The validation rule to apply
            records: List of data records to validate
            
        Returns:
            List of ValidationResult objects
        """
        field_name = rule.field
        case_sensitive = rule.parameters.get("case_sensitive", True)
        ignore_none = rule.parameters.get("ignore_none", True)
        
        # Track seen values and their first occurrence
        seen_values: Dict[Any, int] = {}
        duplicate_indices: Set[int] = set()
        results: List[ValidationResult] = []
        
        # First pass: identify duplicates
        for i, record in enumerate(records):
            # Check if field exists in record
            if field_name not in record:
                results.append(self._create_result(
                    rule=rule,
                    record_index=i,
                    passed=False,
                    message=f"Field '{field_name}' is missing for uniqueness validation"
                ))
                continue
            
            field_value = record[field_name]
            
            # Handle None values
            if field_value is None:
                if ignore_none:
                    results.append(self._create_result(
                        rule=rule,
                        record_index=i,
                        passed=True,
                        message=f"Field '{field_name}' is None, skipping uniqueness validation"
                    ))
                    continue
                else:
                    # Treat None as a value that can be duplicated
                    normalized_value = None
            else:
                # Normalize value for comparison
                normalized_value = self._normalize_value(field_value, case_sensitive)
            
            # Check for duplicates
            if normalized_value in seen_values:
                # Mark both the original and current record as duplicates
                original_index = seen_values[normalized_value]
                duplicate_indices.add(original_index)
                duplicate_indices.add(i)
            else:
                # First occurrence of this value
                seen_values[normalized_value] = i
            
            # Placeholder result (will be updated in second pass)
            results.append(None)
        
        # Second pass: create final results
        for i, record in enumerate(records):
            if results[i] is not None:
                # Already processed (missing field or None value)
                continue
            
            field_value = record[field_name]
            
            if i in duplicate_indices:
                # This record has a duplicate value
                results[i] = self._create_result(
                    rule=rule,
                    record_index=i,
                    passed=False,
                    message=f"Field '{field_name}' value '{field_value}' is not unique (duplicate found)"
                )
            else:
                # This record has a unique value
                results[i] = self._create_result(
                    rule=rule,
                    record_index=i,
                    passed=True,
                    message=f"Field '{field_name}' value '{field_value}' is unique"
                )
        
        return results
    
    def _normalize_value(self, value: Any, case_sensitive: bool) -> Any:
        """
        Normalize a value for uniqueness comparison.
        
        Args:
            value: The value to normalize
            case_sensitive: Whether comparison should be case-sensitive
            
        Returns:
            Normalized value for comparison
        """
        if isinstance(value, str) and not case_sensitive:
            return value.lower()
        return value