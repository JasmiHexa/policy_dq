"""
Cross-field validation processor.

This module implements validation for relationships between multiple fields
in the same record, such as date comparisons, conditional requirements, etc.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class CrossFieldProcessor(RuleProcessor):
    """
    Processor for cross-field validation rules.
    
    Validates relationships between multiple fields in the same record.
    Supports various comparison operations including:
    - Numeric comparisons (greater_than, less_than, equal, etc.)
    - Date comparisons
    - Conditional field requirements
    - Custom validation logic
    """
    
    # Supported comparison operations
    COMPARISON_OPERATIONS = {
        "equal": lambda a, b: a == b,
        "equals": lambda a, b: a == b,  # Alias for equal
        "not_equal": lambda a, b: a != b,
        "not_equals": lambda a, b: a != b,  # Alias for not_equal
        "greater_than": lambda a, b: a > b,
        "greater_than_or_equal": lambda a, b: a >= b,
        "less_than": lambda a, b: a < b,
        "less_than_or_equal": lambda a, b: a <= b,
    }
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a cross-field rule, False otherwise
        """
        return rule.rule_type == RuleType.CROSS_FIELD
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for cross-field validation.
        
        Args:
            rule: The validation rule to apply
            record: The data record to validate
            record_index: Index of the record in the dataset
            all_records: All records in the dataset (unused for this processor)
            
        Returns:
            ValidationResult indicating success or failure
        """
        primary_field = rule.field
        comparison = rule.parameters.get("comparison")
        compare_field = rule.parameters.get("compare_field")
        
        # Validate rule parameters
        if not comparison:
            return ValidationResult(
                rule_name=rule.name,
                field="",
                row_index=record_index,
                severity=rule.severity,
                message="Cross-field rule missing required 'comparison' parameter",
                passed=False
            )
        
        if not compare_field:
            return ValidationResult(
                rule_name=rule.name,
                field="",
                row_index=record_index,
                severity=rule.severity,
                message="Cross-field rule missing required 'compare_field' parameter",
                passed=False
            )
        
        # Check if both fields exist in record
        if primary_field not in record:
            return ValidationResult(
                rule_name=rule.name,
                field="",
                row_index=record_index,
                severity=rule.severity,
                message=f"Primary field '{primary_field}' is missing for cross-field validation",
                passed=False
            )
        
        if compare_field not in record:
            return ValidationResult(
                rule_name=rule.name,
                field="",
                row_index=record_index,
                severity=rule.severity,
                message=f"Compare field '{compare_field}' is missing for cross-field validation",
                passed=False
            )
        
        primary_value = record[primary_field]
        compare_value = record[compare_field]
        
        # Handle None values
        allow_none = rule.parameters.get("allow_none", True)
        if primary_value is None or compare_value is None:
            if allow_none:
                return ValidationResult(
                    rule_name=rule.name,
                    field="",
                    row_index=record_index,
                    severity=rule.severity,
                    message=f"Cross-field validation skipped due to None value(s) in '{primary_field}' or '{compare_field}'",
                    passed=True
                )
            else:
                return ValidationResult(
                    rule_name=rule.name,
                    field="",
                    row_index=record_index,
                    severity=rule.severity,
                    message=f"Cross-field validation failed: None values not allowed in '{primary_field}' or '{compare_field}'",
                    passed=False
                )
        
        # Perform the comparison
        try:
            result = self._perform_comparison(
                primary_value, 
                compare_value, 
                comparison, 
                rule.parameters
            )
            
            if result:
                return ValidationResult(
                    rule_name=rule.name,
                    field="",  # Cross-field validations don't have a single field
                    row_index=record_index,
                    severity=rule.severity,
                    message=f"Cross-field validation passed: '{primary_field}' ({primary_value}) {comparison} '{compare_field}' ({compare_value})",
                    passed=True
                )
            else:
                return ValidationResult(
                    rule_name=rule.name,
                    field="",  # Cross-field validations don't have a single field
                    row_index=record_index,
                    severity=rule.severity,
                    message=f"Cross-field validation failed: '{primary_field}' ({primary_value}) {comparison} '{compare_field}' ({compare_value})",
                    passed=False
                )
                
        except Exception as e:
            return ValidationResult(
                rule_name=rule.name,
                field="",  # Cross-field validations don't have a single field
                row_index=record_index,
                severity=rule.severity,
                message=f"Cross-field validation error: {str(e)}",
                passed=False
            )
    
    def _perform_comparison(
        self, 
        primary_value: Any, 
        compare_value: Any, 
        comparison: str, 
        parameters: Dict[str, Any]
    ) -> bool:
        """
        Perform the specified comparison between two values.
        
        Args:
            primary_value: The primary field value
            compare_value: The comparison field value
            comparison: The comparison operation to perform
            parameters: Additional rule parameters
            
        Returns:
            True if the comparison passes, False otherwise
            
        Raises:
            ValueError: If the comparison operation is not supported
            TypeError: If the values cannot be compared
        """
        # Check if comparison operation is supported
        if comparison not in self.COMPARISON_OPERATIONS:
            raise ValueError(f"Unsupported comparison operation: {comparison}")
        
        # Get the comparison function
        comparison_func = self.COMPARISON_OPERATIONS[comparison]
        
        # Handle type conversion if needed
        convert_types = parameters.get("convert_types", True)
        if convert_types:
            primary_value, compare_value = self._convert_values_for_comparison(
                primary_value, compare_value, parameters
            )
        
        # Perform the comparison
        try:
            return comparison_func(primary_value, compare_value)
        except TypeError as e:
            raise TypeError(f"Cannot compare {type(primary_value).__name__} and {type(compare_value).__name__}: {str(e)}")
    
    def _convert_values_for_comparison(
        self, 
        primary_value: Any, 
        compare_value: Any, 
        parameters: Dict[str, Any]
    ) -> tuple[Any, Any]:
        """
        Convert values to compatible types for comparison.
        
        Args:
            primary_value: The primary field value
            compare_value: The comparison field value
            parameters: Additional rule parameters
            
        Returns:
            Tuple of converted values
        """
        # Check if specific type conversion is requested
        convert_to_type = parameters.get("convert_to_type", "auto").lower()
        
        if convert_to_type == "date":
            return self._convert_to_dates(primary_value, compare_value)
        elif convert_to_type == "number":
            return self._convert_to_numbers(primary_value, compare_value)
        elif convert_to_type == "string":
            return str(primary_value), str(compare_value)
        elif convert_to_type == "auto":
            return self._auto_convert_values(primary_value, compare_value)
        else:
            # No conversion
            return primary_value, compare_value
    
    def _convert_to_dates(self, value1: Any, value2: Any) -> tuple[datetime, datetime]:
        """Convert values to datetime objects."""
        date_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        
        def parse_date(value):
            if isinstance(value, datetime):
                return value
            
            if isinstance(value, str):
                for fmt in date_formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse date: {value}")
            
            raise TypeError(f"Cannot convert {type(value).__name__} to date")
        
        return parse_date(value1), parse_date(value2)
    
    def _convert_to_numbers(self, value1: Any, value2: Any) -> tuple[Union[int, float], Union[int, float]]:
        """Convert values to numeric types."""
        def parse_number(value):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return value
            
            if isinstance(value, str):
                value = value.strip()
                try:
                    return int(value)
                except ValueError:
                    try:
                        return float(value)
                    except ValueError:
                        raise ValueError(f"Cannot parse number: {value}")
            
            raise TypeError(f"Cannot convert {type(value).__name__} to number")
        
        return parse_number(value1), parse_number(value2)
    
    def _auto_convert_values(self, value1: Any, value2: Any) -> tuple[Any, Any]:
        """Automatically convert values to compatible types."""
        # Try to convert both to numbers first (even if they're the same type)
        try:
            return self._convert_to_numbers(value1, value2)
        except (ValueError, TypeError):
            pass
        
        # Try to convert both to dates
        try:
            return self._convert_to_dates(value1, value2)
        except (ValueError, TypeError):
            pass
        
        # If both are already the same type and conversions failed, return as-is
        if type(value1) == type(value2):
            return value1, value2
        
        # Fall back to string conversion for different types
        return str(value1), str(value2)