"""
Core validation engine that orchestrates rule processing.

This module contains the main DataValidator class that coordinates
validation rule execution across datasets and generates comprehensive reports.
"""

import logging
from typing import Any, Dict, List, Optional

from ..models import ValidationRule, ValidationResult, ValidationReport, ValidationSeverity
from .processors import (
    RuleProcessor,
    RequiredFieldProcessor,
    TypeCheckProcessor,
    RegexProcessor,
    NumericRangeProcessor,
    UniquenessProcessor,
    CrossFieldProcessor
)


logger = logging.getLogger(__name__)


class DataValidator:
    """
    Main validation engine that orchestrates rule processing.
    
    The DataValidator coordinates the execution of validation rules against
    datasets, manages rule processors, and generates comprehensive validation reports.
    """
    
    def __init__(self, rules: List[ValidationRule]):
        """
        Initialize the DataValidator with validation rules.
        
        Args:
            rules: List of validation rules to apply
        """
        self.rules = rules
        self.rule_processors = self._initialize_processors()
        logger.info(f"Initialized DataValidator with {len(rules)} rules")
    
    @property
    def processors(self):
        """Backward compatibility property for tests."""
        return {
            'required_field': next((p for p in self.rule_processors if isinstance(p, RequiredFieldProcessor)), None),
            'regex_check': next((p for p in self.rule_processors if isinstance(p, RegexProcessor)), None),
            'numeric_range': next((p for p in self.rule_processors if isinstance(p, NumericRangeProcessor)), None),
            'type_check': next((p for p in self.rule_processors if isinstance(p, TypeCheckProcessor)), None),
            'uniqueness': next((p for p in self.rule_processors if isinstance(p, UniquenessProcessor)), None),
            'cross_field': next((p for p in self.rule_processors if isinstance(p, CrossFieldProcessor)), None)
        }
    
    def _initialize_processors(self) -> List[RuleProcessor]:
        """
        Initialize all available rule processors.
        
        Returns:
            List of rule processor instances
        """
        processors = [
            RequiredFieldProcessor(),
            TypeCheckProcessor(),
            RegexProcessor(),
            NumericRangeProcessor(),
            UniquenessProcessor(),
            CrossFieldProcessor()
        ]
        logger.debug(f"Initialized {len(processors)} rule processors")
        return processors
    
    def validate(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        Execute all validation rules against the complete dataset.
        
        Args:
            data: List of data records to validate
            
        Returns:
            ValidationReport containing comprehensive validation results
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Cannot validate empty dataset")
        
        logger.info(f"Starting validation of {len(data)} records with {len(self.rules)} rules")
        
        all_results = []
        
        try:
            # Process each rule against the dataset
            for rule in self.rules:
                logger.debug(f"Processing rule: {rule.name}")
                
                # Find appropriate processor for this rule
                processor = self._find_processor(rule)
                if not processor:
                    logger.warning(f"No processor found for rule: {rule.name} (type: {rule.rule_type})")
                    # Create a failure result for unsupported rule
                    error_result = ValidationResult(
                        rule_name=rule.name,
                        field=rule.field,
                        row_index=None,
                        severity=ValidationSeverity.ERROR,
                        message=f"No processor available for rule type: {rule.rule_type}",
                        passed=False
                    )
                    all_results.append(error_result)
                    continue
                
                try:
                    # Process the rule against all records
                    rule_results = processor.process_dataset(rule, data)
                    all_results.extend(rule_results)
                    logger.debug(f"Rule {rule.name} generated {len(rule_results)} results")
                    
                except Exception as e:
                    logger.error(f"Error processing rule {rule.name}: {str(e)}")
                    # Create a failure result for processing error
                    error_result = ValidationResult(
                        rule_name=rule.name,
                        field=rule.field,
                        row_index=None,
                        severity=ValidationSeverity.ERROR,
                        message=f"Rule processing failed: {str(e)}",
                        passed=False
                    )
                    all_results.append(error_result)
            
            # Generate comprehensive report
            report = self._generate_report(data, all_results)
            logger.info(f"Validation completed: {report.passed_validations} passed, {report.failed_validations} failed")
            
            return report
            
        except Exception as e:
            logger.error(f"Critical error during validation: {str(e)}")
            raise
    
    def validate_record(self, record: Dict[str, Any], index: int) -> List[ValidationResult]:
        """
        Validate a single record against all applicable rules.
        
        Args:
            record: The data record to validate
            index: Index of the record in the dataset
            
        Returns:
            List of ValidationResult objects for this record
            
        Raises:
            ValueError: If record is invalid
        """
        if not isinstance(record, dict):
            raise ValueError("Record must be a dictionary")
        
        logger.debug(f"Validating record at index {index}")
        
        results = []
        
        for rule in self.rules:
            # Find appropriate processor for this rule
            processor = self._find_processor(rule)
            if not processor:
                logger.warning(f"No processor found for rule: {rule.name}")
                error_result = ValidationResult(
                    rule_name=rule.name,
                    field=rule.field,
                    row_index=index,
                    severity=ValidationSeverity.ERROR,
                    message=f"No processor available for rule type: {rule.rule_type}",
                    passed=False
                )
                results.append(error_result)
                continue
            
            try:
                # Process the rule against this record
                result = processor.process_record(rule, record, index)
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing rule {rule.name} for record {index}: {str(e)}")
                error_result = ValidationResult(
                    rule_name=rule.name,
                    field=rule.field,
                    row_index=index,
                    severity=ValidationSeverity.ERROR,
                    message=f"Rule processing failed: {str(e)}",
                    passed=False
                )
                results.append(error_result)
        
        return results
    
    def _find_processor(self, rule: ValidationRule) -> Optional[RuleProcessor]:
        """
        Find the appropriate processor for a validation rule.
        
        Args:
            rule: The validation rule to find a processor for
            
        Returns:
            RuleProcessor instance that can handle the rule, or None if not found
        """
        for processor in self.rule_processors:
            if processor.can_process(rule):
                return processor
        return None
    
    def _generate_report(self, data: List[Dict[str, Any]], results: List[ValidationResult]) -> ValidationReport:
        """
        Generate a comprehensive validation report from results.
        
        Args:
            data: The original dataset that was validated
            results: List of all validation results
            
        Returns:
            ValidationReport with summary statistics and detailed results
        """
        # Count passed and failed validations
        passed_count = sum(1 for result in results if result.passed)
        failed_count = sum(1 for result in results if not result.passed)
        
        # Count results by severity
        severity_counts = {severity: 0 for severity in ValidationSeverity}
        for result in results:
            severity_counts[result.severity] += 1
        
        report = ValidationReport(
            total_records=len(data),
            total_rules=len(self.rules),
            passed_validations=passed_count,
            failed_validations=failed_count,
            results=results,
            summary_by_severity=severity_counts
        )
        
        return report
    
    def filter_results_by_severity(
        self, 
        results: List[ValidationResult], 
        min_severity: ValidationSeverity
    ) -> List[ValidationResult]:
        """
        Filter validation results by minimum severity level.
        
        Args:
            results: List of validation results to filter
            min_severity: Minimum severity level to include
            
        Returns:
            Filtered list of validation results
        """
        severity_order = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.ERROR: 2,
            ValidationSeverity.CRITICAL: 3
        }
        
        min_level = severity_order[min_severity]
        
        return [
            result for result in results 
            if severity_order[result.severity] >= min_level
        ]
    
    def get_failed_results(self, results: List[ValidationResult]) -> List[ValidationResult]:
        """
        Get only the failed validation results.
        
        Args:
            results: List of validation results to filter
            
        Returns:
            List of failed validation results
        """
        return [result for result in results if not result.passed]
    
    def get_results_by_rule(
        self, 
        results: List[ValidationResult], 
        rule_name: str
    ) -> List[ValidationResult]:
        """
        Get validation results for a specific rule.
        
        Args:
            results: List of validation results to filter
            rule_name: Name of the rule to filter by
            
        Returns:
            List of validation results for the specified rule
        """
        return [result for result in results if result.rule_name == rule_name]
    
    def get_results_by_field(
        self, 
        results: List[ValidationResult], 
        field_name: str
    ) -> List[ValidationResult]:
        """
        Get validation results for a specific field.
        
        Args:
            results: List of validation results to filter
            field_name: Name of the field to filter by
            
        Returns:
            List of validation results for the specified field
        """
        return [result for result in results if result.field == field_name]
    
    def get_aggregated_stats(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get detailed aggregated statistics from validation results.
        
        Args:
            results: List of validation results to analyze
            
        Returns:
            Dictionary containing detailed statistics
        """
        if not results:
            return {
                "total_results": 0,
                "passed_count": 0,
                "failed_count": 0,
                "pass_rate": 0.0,
                "severity_breakdown": {severity.value: 0 for severity in ValidationSeverity},
                "rule_breakdown": {},
                "field_breakdown": {}
            }
        
        # Basic counts
        total_results = len(results)
        passed_count = sum(1 for result in results if result.passed)
        failed_count = total_results - passed_count
        pass_rate = (passed_count / total_results) * 100 if total_results > 0 else 0.0
        
        # Severity breakdown
        severity_breakdown = {severity.value: 0 for severity in ValidationSeverity}
        for result in results:
            severity_breakdown[result.severity.value] += 1
        
        # Rule breakdown
        rule_breakdown = {}
        for result in results:
            rule_name = result.rule_name
            if rule_name not in rule_breakdown:
                rule_breakdown[rule_name] = {"passed": 0, "failed": 0, "total": 0}
            
            rule_breakdown[rule_name]["total"] += 1
            if result.passed:
                rule_breakdown[rule_name]["passed"] += 1
            else:
                rule_breakdown[rule_name]["failed"] += 1
        
        # Field breakdown
        field_breakdown = {}
        for result in results:
            field_name = result.field
            if field_name not in field_breakdown:
                field_breakdown[field_name] = {"passed": 0, "failed": 0, "total": 0}
            
            field_breakdown[field_name]["total"] += 1
            if result.passed:
                field_breakdown[field_name]["passed"] += 1
            else:
                field_breakdown[field_name]["failed"] += 1
        
        return {
            "total_results": total_results,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "pass_rate": round(pass_rate, 2),
            "severity_breakdown": severity_breakdown,
            "rule_breakdown": rule_breakdown,
            "field_breakdown": field_breakdown
        }