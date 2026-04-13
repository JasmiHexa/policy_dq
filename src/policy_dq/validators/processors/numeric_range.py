"""
Numeric range validation processor.

This module implements validation for numeric range constraints, ensuring that
numeric field values fall within specified minimum and maximum bounds.
"""

from typing import Any, Dict, List, Optional, Union

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class NumericRangeProcessor(RuleProcessor):
    """
    Processor for numeric range validation rules.
    
    Validates that numeric field values fall within specified min/max ranges.
    Supports both inclusive and exclusive bounds, and handles type conversion
    from strings to numbers when possible.
    """
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a numeric range rule, False otherwise
        """
        return rule.rule_type == RuleType.NUMERIC_RANGE
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for numeric range validation.
        
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
                message=f"Field '{field_name}' is missing for numeric range validation"
            )
        
        field_value = record[field_name]
        
        # Skip validation for None values
        if field_value is None:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,  # None values pass range check (handled by required field validation)
                message=f"Field '{field_name}' is None, skipping numeric range validation"
            )
        
        # Convert value to numeric type
        try:
            numeric_value = self._convert_to_numeric(field_value)
        except ValueError as e:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Field '{field_name}' value '{field_value}' cannot be converted to number: {str(e)}"
            )
        
        # Get range parameters
        min_value = rule.parameters.get("min")
        max_value = rule.parameters.get("max")
        min_inclusive = rule.parameters.get("min_inclusive", True)
        max_inclusive = rule.parameters.get("max_inclusive", True)
        
        # Validate range parameters
        if min_value is None and max_value is None:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message="Numeric range rule must specify at least 'min' or 'max' parameter"
            )
        
        # Perform range validation
        validation_errors = []
        
        if min_value is not None:
            try:
                min_numeric = self._convert_to_numeric(min_value)
                if min_inclusive:
                    if numeric_value < min_numeric:
                        validation_errors.append(f"value {numeric_value} is less than minimum {min_numeric}")
                else:
                    if numeric_value <= min_numeric:
                        validation_errors.append(f"value {numeric_value} is less than or equal to minimum {min_numeric} (exclusive)")
            except ValueError:
                return self._create_result(
                    rule=rule,
                    record_index=record_index,
                    passed=False,
                    message=f"Invalid 'min' parameter value: {min_value}"
                )
        
        if max_value is not None:
            try:
                max_numeric = self._convert_to_numeric(max_value)
                if max_inclusive:
                    if numeric_value > max_numeric:
                        validation_errors.append(f"value {numeric_value} is greater than maximum {max_numeric}")
                else:
                    if numeric_value >= max_numeric:
                        validation_errors.append(f"value {numeric_value} is greater than or equal to maximum {max_numeric} (exclusive)")
            except ValueError:
                return self._create_result(
                    rule=rule,
                    record_index=record_index,
                    passed=False,
                    message=f"Invalid 'max' parameter value: {max_value}"
                )
        
        # Return result
        if validation_errors:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Field '{field_name}' numeric range validation failed: {'; '.join(validation_errors)}"
            )
        else:
            range_desc = self._get_range_description(min_value, max_value, min_inclusive, max_inclusive)
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,
                message=f"Field '{field_name}' value {numeric_value} is within range {range_desc}"
            )
    
    def _convert_to_numeric(self, value: Any) -> Union[int, float]:
        """
        Convert a value to a numeric type (int or float).
        
        Args:
            value: The value to convert
            
        Returns:
            Numeric value (int or float)
            
        Raises:
            ValueError: If the value cannot be converted to a number
        """
        # Already numeric
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return value
        
        # Try to convert string to number
        if isinstance(value, str):
            value = value.strip()
            
            # Try integer first
            try:
                return int(value)
            except ValueError:
                pass
            
            # Try float
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to number")
        
        # Other types
        raise ValueError(f"Cannot convert {type(value).__name__} to number")
    
    def _get_range_description(
        self, 
        min_value: Any, 
        max_value: Any, 
        min_inclusive: bool, 
        max_inclusive: bool
    ) -> str:
        """
        Get a human-readable description of the range.
        
        Args:
            min_value: Minimum value (or None)
            max_value: Maximum value (or None)
            min_inclusive: Whether minimum is inclusive
            max_inclusive: Whether maximum is inclusive
            
        Returns:
            Human-readable range description
        """
        if min_value is not None and max_value is not None:
            min_bracket = "[" if min_inclusive else "("
            max_bracket = "]" if max_inclusive else ")"
            return f"{min_bracket}{min_value}, {max_value}{max_bracket}"
        elif min_value is not None:
            operator = ">=" if min_inclusive else ">"
            return f"{operator} {min_value}"
        elif max_value is not None:
            operator = "<=" if max_inclusive else "<"
            return f"{operator} {max_value}"
        else:
            return "no range specified"