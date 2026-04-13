"""
Base classes for validation rule processors.

This module defines the abstract base class for validation rule processors
that handle specific types of validation rules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...models import ValidationRule, ValidationResult


class RuleProcessor(ABC):
    """
    Abstract base class for validation rule processors.
    
    Rule processors are responsible for executing specific types of validation
    rules against data records and returning validation results.
    """
    
    @abstractmethod
    def can_process(self, rule: ValidationRule) -> bool:
        """
        Check if this processor can handle the given rule.
        
        Args:
            rule: The validation rule to check
            
        Returns:
            True if this processor can handle the rule, False otherwise
        """
        pass
    
    @abstractmethod
    def process_record(
        self, 
        rule: ValidationRule, 
        record: Dict[str, Any], 
        record_index: int,
        all_records: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """
        Process a single record against the validation rule.
        
        Args:
            rule: The validation rule to apply
            record: The data record to validate
            record_index: Index of the record in the dataset
            all_records: All records in the dataset (for cross-record validation)
            
        Returns:
            ValidationResult indicating success or failure
        """
        pass
    
    def process_dataset(
        self, 
        rule: ValidationRule, 
        records: List[Dict[str, Any]]
    ) -> List[ValidationResult]:
        """
        Process all records in a dataset against the validation rule.
        
        This default implementation calls process_record for each record.
        Subclasses can override this for more efficient dataset-level processing.
        
        Args:
            rule: The validation rule to apply
            records: List of data records to validate
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        for i, record in enumerate(records):
            result = self.process_record(rule, record, i, records)
            results.append(result)
        return results
    
    def _create_result(
        self,
        rule: ValidationRule,
        record_index: int,
        passed: bool,
        message: str
    ) -> ValidationResult:
        """
        Helper method to create a ValidationResult.
        
        Args:
            rule: The validation rule that was applied
            record_index: Index of the record that was validated
            passed: Whether the validation passed
            message: Human-readable message describing the result
            
        Returns:
            ValidationResult object
        """
        return ValidationResult(
            rule_name=rule.name,
            field=rule.field,
            row_index=record_index,
            severity=rule.severity,
            message=message,
            passed=passed
        )