"""
Type check validation processor.

This module implements validation for data type checking, ensuring that
field values match expected data types.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class TypeCheckProcessor(RuleProcessor):
    """
    Processor for type check validation rules.
    
    Validates that field values match specified data types including:
    - string: Text values
    - int: Integer numbers
    - float: Floating point numbers
    - bool: Boolean values (true/false)
    - date: Date values in various formats
    """
    
    # Common date formats to try when parsing dates
    DATE_FORMATS = [
        "%Y-%m-%d",           # 2023-12-25
        "%m/%d/%Y",           # 12/25/2023
        "%d/%m/%Y",           # 25/12/2023
        "%Y-%m-%d %H:%M:%S",  # 2023-12-25 14:30:00
        "%m/%d/%Y %H:%M:%S",  # 12/25/2023 14:30:00
        "%d/%m/%Y %H:%M:%S",  # 25/12/2023 14:30:00
        "%Y-%m-%dT%H:%M:%S",  # 2023-12-25T14:30:00 (ISO format)
        "%Y-%m-%dT%H:%M:%SZ", # 2023-12-25T14:30:00Z (ISO with Z)
    ]
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a type check rule, False otherwise
        """
        return rule.rule_type == RuleType.TYPE_CHECK
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for type check validation.
        
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
                message=f"Field '{field_name}' is missing for type check"
            )
        
        field_value = record[field_name]
        expected_type = rule.parameters.get("type", "string").lower()
        
        # Skip validation for None values unless explicitly checking for None
        if field_value is None and expected_type != "none":
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,  # None values pass type check (handled by required field validation)
                message=f"Field '{field_name}' is None, skipping type check"
            )
        
        # Perform type validation
        is_valid, error_message = self._validate_type(field_value, expected_type)
        
        if is_valid:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,
                message=f"Field '{field_name}' has valid type '{expected_type}'"
            )
        else:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Field '{field_name}' type validation failed: {error_message}"
            )
    
    def _validate_type(self, value: Any, expected_type: str) -> tuple[bool, str]:
        """
        Validate that a value matches the expected type.
        
        Args:
            value: The value to validate
            expected_type: The expected type name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if expected_type == "string":
                return self._validate_string(value)
            elif expected_type == "int":
                return self._validate_int(value)
            elif expected_type == "float":
                return self._validate_float(value)
            elif expected_type == "bool":
                return self._validate_bool(value)
            elif expected_type == "date":
                return self._validate_date(value)
            elif expected_type == "none":
                return self._validate_none(value)
            else:
                return False, f"Unsupported type '{expected_type}'"
        except Exception as e:
            return False, f"Type validation error: {str(e)}"
    
    def _validate_string(self, value: Any) -> tuple[bool, str]:
        """Validate string type."""
        if isinstance(value, str):
            return True, ""
        return False, f"Expected string, got {type(value).__name__}"
    
    def _validate_int(self, value: Any) -> tuple[bool, str]:
        """Validate integer type."""
        # Check if already an integer
        if isinstance(value, int) and not isinstance(value, bool):
            return True, ""
        
        # Try to convert string to integer
        if isinstance(value, str):
            try:
                int(value)
                return True, ""
            except ValueError:
                return False, f"Cannot convert '{value}' to integer"
        
        return False, f"Expected integer, got {type(value).__name__}"
    
    def _validate_float(self, value: Any) -> tuple[bool, str]:
        """Validate float type."""
        # Check if already a float or int (int can be treated as float)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return True, ""
        
        # Try to convert string to float
        if isinstance(value, str):
            try:
                float(value)
                return True, ""
            except ValueError:
                return False, f"Cannot convert '{value}' to float"
        
        return False, f"Expected float, got {type(value).__name__}"
    
    def _validate_bool(self, value: Any) -> tuple[bool, str]:
        """Validate boolean type."""
        # Check if already a boolean
        if isinstance(value, bool):
            return True, ""
        
        # Try to convert string to boolean
        if isinstance(value, str):
            lower_value = value.lower().strip()
            if lower_value in ("true", "false", "yes", "no", "1", "0", "on", "off"):
                return True, ""
            return False, f"Cannot convert '{value}' to boolean"
        
        # Check for numeric boolean values
        if isinstance(value, (int, float)):
            if value in (0, 1):
                return True, ""
            return False, f"Numeric value '{value}' is not a valid boolean (0 or 1)"
        
        return False, f"Expected boolean, got {type(value).__name__}"
    
    def _validate_date(self, value: Any) -> tuple[bool, str]:
        """Validate date type."""
        # Check if already a datetime object
        if isinstance(value, datetime):
            return True, ""
        
        # Try to parse string as date
        if isinstance(value, str):
            for date_format in self.DATE_FORMATS:
                try:
                    datetime.strptime(value, date_format)
                    return True, ""
                except ValueError:
                    continue
            return False, f"Cannot parse '{value}' as date with supported formats"
        
        return False, f"Expected date, got {type(value).__name__}"
    
    def _validate_none(self, value: Any) -> tuple[bool, str]:
        """Validate None type."""
        if value is None:
            return True, ""
        return False, f"Expected None, got {type(value).__name__}"