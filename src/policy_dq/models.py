"""
Core data models for the validation system.

This module defines the fundamental data structures used throughout
the validation system including enums, validation rules, results, and reports.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation results."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleType(Enum):
    """Types of validation rules supported by the system."""
    REQUIRED_FIELD = "required_field"
    TYPE_CHECK = "type_check"
    REGEX_CHECK = "regex_check"
    NUMERIC_RANGE = "numeric_range"
    UNIQUENESS = "uniqueness"
    CROSS_FIELD = "cross_field"


@dataclass
class ValidationRule:
    """
    Represents a single validation rule.
    
    Attributes:
        name: Unique identifier for the rule
        rule_type: Type of validation to perform
        field: Primary field to validate
        parameters: Rule-specific configuration parameters
        severity: Severity level for validation failures
    """
    name: str
    rule_type: RuleType
    field: str
    parameters: Dict[str, Any]
    severity: ValidationSeverity = ValidationSeverity.ERROR


@dataclass
class ValidationResult:
    """
    Represents the result of applying a validation rule to data.
    
    Attributes:
        rule_name: Name of the rule that was applied
        field: Field that was validated
        row_index: Index of the record (None for dataset-level validations)
        severity: Severity level of the result
        message: Human-readable description of the result
        passed: Whether the validation passed or failed
    """
    rule_name: str
    field: str
    row_index: Optional[int]
    severity: ValidationSeverity
    message: str
    passed: bool


@dataclass
class ValidationReport:
    """
    Comprehensive report of validation results for a dataset.
    
    Attributes:
        total_records: Number of records processed
        total_rules: Number of rules applied
        passed_validations: Count of successful validations
        failed_validations: Count of failed validations
        results: List of individual validation results
        summary_by_severity: Count of results grouped by severity level
    """
    total_records: int
    total_rules: int
    passed_validations: int
    failed_validations: int
    results: List[ValidationResult]
    summary_by_severity: Dict[ValidationSeverity, int]