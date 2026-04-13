"""
Required field validation processor.

This module implements validation for required fields, ensuring that
specified fields exist and contain non-empty values.
"""

from typing import Any, Dict, List, Optional

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class RequiredFieldProcessor(RuleProcessor):
    """
    Processor for required field validation rules.
    
    Validates that specified fields exist in records and contain non-empty values.
    Empty strings, None values, and missing fields are considered validation failures.
    """
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a required field rule, False otherwise
        """
        return rule.rule_type == RuleType.REQUIRED_FIELD
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for required field validation.
        
        Args:
            rule: The validation rule to apply
            record: The data record to validate
            record_index: Index of the record in the dataset
            all_records: All records in the dataset (unused for this processor)
            
        Returns:
            ValidationResult indicating success or failure
        """
        field_name = rule.field
        
        # Check if field exists in record
        if field_name not in record:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Required field '{field_name}' is missing"
            )
        
        # Get field value
        field_value = record[field_name]
        
        # Check if field value is empty
        if self._is_empty_value(field_value):
            # Check if empty values are allowed
            allow_empty = rule.parameters.get("allow_empty", False)
            if allow_empty:
                return self._create_result(
                    rule=rule,
                    record_index=record_index,
                    passed=True,
                    message=f"Field '{field_name}' is empty but allowed"
                )
            else:
                return self._create_result(
                    rule=rule,
                    record_index=record_index,
                    passed=False,
                    message=f"Required field '{field_name}' is empty"
                )
        
        # Field exists and has a non-empty value
        return self._create_result(
            rule=rule,
            record_index=record_index,
            passed=True,
            message=f"Field '{field_name}' validation passed"
        )
    
    def _is_empty_value(self, value: Any) -> bool:
        """
        Check if a value is considered empty for required field validation.
        
        Args:
            value: The value to check
            
        Returns:
            True if the value is considered empty, False otherwise
        """
        # None is empty
        if value is None:
            return True
        
        # Empty string is empty
        if isinstance(value, str) and value.strip() == "":
            return True
        
        # Empty collections are empty
        if hasattr(value, '__len__') and len(value) == 0:
            return True
        
        # All other values are considered non-empty
        return False