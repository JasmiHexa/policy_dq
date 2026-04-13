"""
Regex pattern validation processor.

This module implements validation for pattern matching using regular expressions,
ensuring that field values match specified patterns.
"""

import re
from typing import Any, Dict, List, Optional

from .base import RuleProcessor
from ...models import ValidationRule, ValidationResult, RuleType


class RegexProcessor(RuleProcessor):
    """
    Processor for regex pattern validation rules.
    
    Validates that field values match specified regular expression patterns.
    Supports common patterns like email validation, phone numbers, etc.
    """
    
    def __init__(self):
        """Initialize the regex processor with compiled pattern cache."""
        self._pattern_cache: Dict[str, re.Pattern] = {}
    
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if the rule is a regex check rule, False otherwise
        """
        return rule.rule_type == RuleType.REGEX_CHECK
    
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record for regex pattern validation.
        
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
                message=f"Field '{field_name}' is missing for regex validation"
            )
        
        field_value = record[field_name]
        
        # Skip validation for None values
        if field_value is None:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,  # None values pass regex check (handled by required field validation)
                message=f"Field '{field_name}' is None, skipping regex validation"
            )
        
        # Convert value to string for regex matching
        str_value = str(field_value)
        
        # Get pattern from rule parameters
        pattern = rule.parameters.get("pattern")
        if not pattern:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message="Regex rule missing required 'pattern' parameter"
            )
        
        # Get or compile regex pattern
        try:
            compiled_pattern = self._get_compiled_pattern(pattern)
        except re.error as e:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Invalid regex pattern '{pattern}': {str(e)}"
            )
        
        # Check if pattern matches
        match_mode = rule.parameters.get("match_mode", "full").lower()
        
        if match_mode == "full":
            # Full match - entire string must match pattern
            is_match = compiled_pattern.fullmatch(str_value) is not None
        elif match_mode == "partial":
            # Partial match - pattern can match anywhere in string
            is_match = compiled_pattern.search(str_value) is not None
        else:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Invalid match_mode '{match_mode}'. Use 'full' or 'partial'"
            )
        
        if is_match:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=True,
                message=f"Field '{field_name}' matches pattern '{pattern}'"
            )
        else:
            return self._create_result(
                rule=rule,
                record_index=record_index,
                passed=False,
                message=f"Field '{field_name}' value '{str_value}' does not match pattern '{pattern}'"
            )
    
    def _get_compiled_pattern(self, pattern: str) -> re.Pattern:
        """
        Get a compiled regex pattern, using cache for performance.
        
        Args:
            pattern: The regex pattern string
            
        Returns:
            Compiled regex pattern
            
        Raises:
            re.error: If the pattern is invalid
        """
        if pattern not in self._pattern_cache:
            self._pattern_cache[pattern] = re.compile(pattern)
        return self._pattern_cache[pattern]
    
    def clear_pattern_cache(self) -> None:
        """Clear the compiled pattern cache."""
        self._pattern_cache.clear()