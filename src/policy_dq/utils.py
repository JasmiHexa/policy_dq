"""
Utility functions and convenience methods for the validation API.

This module provides helper functions for common validation scenarios,
data manipulation, and result analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .exceptions import ValidationAPIError, DataSourceError
from .models import ValidationReport, ValidationResult, ValidationSeverity


def analyze_validation_results(report: ValidationReport) -> Dict[str, Any]:
    """
    Analyze validation results and provide detailed statistics.
    
    Args:
        report: ValidationReport to analyze
        
    Returns:
        Dictionary with detailed analysis including:
        - Overall statistics
        - Field-level analysis
        - Rule-level analysis
        - Severity distribution
        - Top failing rules/fields
    """
    analysis = {
        'overall': {
            'total_records': report.total_records,
            'total_rules': report.total_rules,
            'total_validations': len(report.results),
            'passed_validations': report.passed_validations,
            'failed_validations': report.failed_validations,
            'success_rate': (report.passed_validations / len(report.results) * 100) if report.results else 0.0
        },
        'severity_distribution': dict(report.summary_by_severity),
        'field_analysis': {},
        'rule_analysis': {},
        'top_failing_fields': [],
        'top_failing_rules': [],
        'error_patterns': []
    }
    
    # Field-level analysis
    field_stats = {}
    for result in report.results:
        field = result.field
        if field not in field_stats:
            field_stats[field] = {'total': 0, 'passed': 0, 'failed': 0, 'errors': []}
        
        field_stats[field]['total'] += 1
        if result.passed:
            field_stats[field]['passed'] += 1
        else:
            field_stats[field]['failed'] += 1
            field_stats[field]['errors'].append({
                'rule': result.rule_name,
                'severity': result.severity.value,
                'message': result.message,
                'row': result.row_index
            })
    
    # Calculate field success rates and sort by failure rate
    for field, stats in field_stats.items():
        stats['success_rate'] = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        analysis['field_analysis'][field] = stats
    
    # Top failing fields
    analysis['top_failing_fields'] = sorted(
        [(field, stats['failed']) for field, stats in field_stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Rule-level analysis
    rule_stats = {}
    for result in report.results:
        rule = result.rule_name
        if rule not in rule_stats:
            rule_stats[rule] = {'total': 0, 'passed': 0, 'failed': 0, 'affected_fields': set()}
        
        rule_stats[rule]['total'] += 1
        rule_stats[rule]['affected_fields'].add(result.field)
        if result.passed:
            rule_stats[rule]['passed'] += 1
        else:
            rule_stats[rule]['failed'] += 1
    
    # Convert sets to lists and calculate success rates
    for rule, stats in rule_stats.items():
        stats['affected_fields'] = list(stats['affected_fields'])
        stats['success_rate'] = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0.0
        analysis['rule_analysis'][rule] = stats
    
    # Top failing rules
    analysis['top_failing_rules'] = sorted(
        [(rule, stats['failed']) for rule, stats in rule_stats.items()],
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    # Error patterns (common error messages)
    error_messages = {}
    for result in report.results:
        if not result.passed:
            msg = result.message
            if msg not in error_messages:
                error_messages[msg] = 0
            error_messages[msg] += 1
    
    analysis['error_patterns'] = sorted(
        error_messages.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return analysis


def get_validation_summary(report: ValidationReport) -> str:
    """
    Generate a human-readable summary of validation results.
    
    Args:
        report: ValidationReport to summarize
        
    Returns:
        String summary of validation results
    """
    total_validations = len(report.results)
    success_rate = (report.passed_validations / total_validations * 100) if total_validations > 0 else 0.0
    
    summary_lines = [
        "Validation Summary:",
        f"  Records processed: {report.total_records:,}",
        f"  Rules applied: {report.total_rules}",
        f"  Total validations: {total_validations:,}",
        f"  Passed: {report.passed_validations:,}",
        f"  Failed: {report.failed_validations:,}",
        f"  Success rate: {success_rate:.1f}%"
    ]
    
    if report.summary_by_severity:
        summary_lines.append("  Severity breakdown:")
        for severity, count in report.summary_by_severity.items():
            if count > 0:
                summary_lines.append(f"    {severity.value.upper()}: {count:,}")
    
    return "\n".join(summary_lines)


def filter_results(
    results: List[ValidationResult],
    field: Optional[str] = None,
    rule: Optional[str] = None,
    severity: Optional[ValidationSeverity] = None,
    passed: Optional[bool] = None,
    row_range: Optional[Tuple[int, int]] = None
) -> List[ValidationResult]:
    """
    Filter validation results based on various criteria.
    
    Args:
        results: List of ValidationResult objects to filter
        field: Filter by field name
        rule: Filter by rule name
        severity: Filter by severity level (exact match)
        passed: Filter by pass/fail status
        row_range: Filter by row index range (inclusive)
        
    Returns:
        Filtered list of ValidationResult objects
    """
    filtered = results
    
    if field is not None:
        filtered = [r for r in filtered if r.field == field]
    
    if rule is not None:
        filtered = [r for r in filtered if r.rule_name == rule]
    
    if severity is not None:
        filtered = [r for r in filtered if r.severity == severity]
    
    if passed is not None:
        filtered = [r for r in filtered if r.passed == passed]
    
    if row_range is not None:
        start_row, end_row = row_range
        filtered = [
            r for r in filtered 
            if r.row_index is not None and start_row <= r.row_index <= end_row
        ]
    
    return filtered


def group_results_by_field(results: List[ValidationResult]) -> Dict[str, List[ValidationResult]]:
    """
    Group validation results by field name.
    
    Args:
        results: List of ValidationResult objects
        
    Returns:
        Dictionary mapping field names to lists of results
    """
    grouped = {}
    for result in results:
        field = result.field
        if field not in grouped:
            grouped[field] = []
        grouped[field].append(result)
    
    return grouped


def group_results_by_rule(results: List[ValidationResult]) -> Dict[str, List[ValidationResult]]:
    """
    Group validation results by rule name.
    
    Args:
        results: List of ValidationResult objects
        
    Returns:
        Dictionary mapping rule names to lists of results
    """
    grouped = {}
    for result in results:
        rule = result.rule_name
        if rule not in grouped:
            grouped[rule] = []
        grouped[rule].append(result)
    
    return grouped


def get_worst_records(
    results: List[ValidationResult], 
    limit: int = 10
) -> List[Tuple[int, int, List[ValidationResult]]]:
    """
    Get records with the most validation failures.
    
    Args:
        results: List of ValidationResult objects
        limit: Maximum number of records to return
        
    Returns:
        List of tuples (row_index, failure_count, failed_results)
        sorted by failure count descending
    """
    # Group by row index
    by_row = {}
    for result in results:
        if result.row_index is not None and not result.passed:
            row_idx = result.row_index
            if row_idx not in by_row:
                by_row[row_idx] = []
            by_row[row_idx].append(result)
    
    # Sort by failure count
    worst_records = [
        (row_idx, len(failures), failures)
        for row_idx, failures in by_row.items()
    ]
    
    worst_records.sort(key=lambda x: x[1], reverse=True)
    
    return worst_records[:limit]


def export_results_to_csv(
    results: List[ValidationResult], 
    output_path: str,
    include_passed: bool = False
) -> None:
    """
    Export validation results to CSV format.
    
    Args:
        results: List of ValidationResult objects
        output_path: Path to output CSV file
        include_passed: Whether to include passed validations
        
    Raises:
        ValidationAPIError: If export fails
    """
    import csv
    
    try:
        filtered_results = results if include_passed else [r for r in results if not r.passed]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['rule_name', 'field', 'row_index', 'severity', 'message', 'passed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in filtered_results:
                writer.writerow({
                    'rule_name': result.rule_name,
                    'field': result.field,
                    'row_index': result.row_index,
                    'severity': result.severity.value,
                    'message': result.message,
                    'passed': result.passed
                })
        
    except Exception as e:
        raise ValidationAPIError(f"Failed to export results to CSV: {e}")


def load_sample_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load sample data from various formats for testing.
    
    Args:
        file_path: Path to sample data file
        
    Returns:
        List of data records
        
    Raises:
        DataSourceError: If file cannot be loaded
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            raise DataSourceError(f"Sample data file not found: {file_path}")
        
        if path.suffix.lower() == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else [data]
        
        elif path.suffix.lower() == '.csv':
            import csv
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        
        else:
            raise DataSourceError(f"Unsupported sample data format: {path.suffix}")
            
    except Exception as e:
        raise DataSourceError(f"Failed to load sample data: {e}")


def create_sample_rules(rule_types: List[str], fields: List[str]) -> List[Dict[str, Any]]:
    """
    Create sample validation rules for testing purposes.
    
    Args:
        rule_types: List of rule types to create
        fields: List of field names to create rules for
        
    Returns:
        List of rule dictionaries
    """
    sample_rules = []
    
    for i, (rule_type, field) in enumerate(zip(rule_types, fields)):
        rule = {
            'name': f'sample_{rule_type}_{field}',
            'type': rule_type,
            'field': field,
            'severity': 'error'
        }
        
        # Add type-specific parameters
        if rule_type == 'required_field':
            rule['parameters'] = {}
        elif rule_type == 'type_check':
            rule['parameters'] = {'expected_type': 'string'}
        elif rule_type == 'regex_check':
            rule['parameters'] = {'pattern': r'^[A-Za-z0-9]+$'}
        elif rule_type == 'numeric_range':
            rule['parameters'] = {'min': 0, 'max': 100}
        elif rule_type == 'uniqueness':
            rule['parameters'] = {}
        elif rule_type == 'cross_field':
            rule['parameters'] = {
                'comparison': 'greater_than',
                'compare_field': 'other_field'
            }
        
        sample_rules.append(rule)
    
    return sample_rules


def validate_rule_configuration(rules_data: Union[Dict, List]) -> List[str]:
    """
    Validate rule configuration format and return any issues found.
    
    Args:
        rules_data: Rule configuration data (dict or list)
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    try:
        # Handle different rule configuration formats
        if isinstance(rules_data, dict):
            if 'rules' in rules_data:
                rules = rules_data['rules']
            elif 'rule_sets' in rules_data:
                rules = []
                for rule_set in rules_data['rule_sets']:
                    if 'rules' in rule_set:
                        rules.extend(rule_set['rules'])
            else:
                issues.append("No 'rules' or 'rule_sets' found in configuration")
                return issues
        elif isinstance(rules_data, list):
            rules = rules_data
        else:
            issues.append("Rule configuration must be a dictionary or list")
            return issues
        
        # Validate individual rules
        required_fields = ['name', 'type', 'field']
        valid_types = ['required_field', 'type_check', 'regex_check', 'numeric_range', 'uniqueness', 'cross_field']
        valid_severities = ['info', 'warning', 'error', 'critical']
        
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                issues.append(f"Rule {i + 1}: Must be a dictionary")
                continue
            
            # Check required fields
            for field in required_fields:
                if field not in rule:
                    issues.append(f"Rule {i + 1}: Missing required field '{field}'")
            
            # Validate rule type
            if 'type' in rule and rule['type'] not in valid_types:
                issues.append(f"Rule {i + 1}: Invalid rule type '{rule['type']}'. Must be one of: {valid_types}")
            
            # Validate severity
            if 'severity' in rule and rule['severity'] not in valid_severities:
                issues.append(f"Rule {i + 1}: Invalid severity '{rule['severity']}'. Must be one of: {valid_severities}")
            
            # Validate parameters exist for rules that need them
            rule_type = rule.get('type')
            if rule_type in ['regex_check', 'numeric_range', 'cross_field']:
                if 'parameters' not in rule or not rule['parameters']:
                    issues.append(f"Rule {i + 1}: Rule type '{rule_type}' requires parameters")
    
    except Exception as e:
        issues.append(f"Error validating rule configuration: {e}")
    
    return issues


def merge_validation_reports(*reports: ValidationReport) -> ValidationReport:
    """
    Merge multiple validation reports into a single report.
    
    Args:
        *reports: ValidationReport objects to merge
        
    Returns:
        Merged ValidationReport
    """
    if not reports:
        raise ValidationAPIError("No reports provided for merging")
    
    # Combine all results
    all_results = []
    total_records = 0
    total_rules = 0
    
    for report in reports:
        all_results.extend(report.results)
        total_records += report.total_records
        total_rules = max(total_rules, report.total_rules)  # Use max to avoid double counting
    
    # Calculate combined statistics
    passed_count = sum(1 for result in all_results if result.passed)
    failed_count = sum(1 for result in all_results if not result.passed)
    
    # Combine severity counts
    combined_severity = {}
    for severity in ValidationSeverity:
        combined_severity[severity] = sum(
            report.summary_by_severity.get(severity, 0) for report in reports
        )
    
    return ValidationReport(
        total_records=total_records,
        total_rules=total_rules,
        passed_validations=passed_count,
        failed_validations=failed_count,
        results=all_results,
        summary_by_severity=combined_severity
    )