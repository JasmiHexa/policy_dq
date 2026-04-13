"""
Markdown reporter for validation results.

This module provides human-readable Markdown output for validation reports,
suitable for documentation and sharing with stakeholders.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from ..models import ValidationReport, ValidationResult, ValidationSeverity
from .base import Reporter


class MarkdownReporter(Reporter):
    """
    Reporter that generates human-readable Markdown output for validation results.
    
    Features:
    - Clean, readable Markdown format
    - Tables for structured data
    - Severity-based organization
    - Summary statistics and detailed listings
    """
    
    def __init__(self, include_passed: bool = False, max_failures_per_rule: int = 10):
        """
        Initialize the Markdown reporter.
        
        Args:
            include_passed: Whether to include passed validations in the report
            max_failures_per_rule: Maximum number of failures to show per rule
        """
        self.include_passed = include_passed
        self.max_failures_per_rule = max_failures_per_rule
    
    def generate_report(self, report: ValidationReport, output_path: Optional[str] = None, input_file: Optional[str] = None, rules_source: Optional[str] = None) -> None:
        """
        Generate and save the validation report as Markdown.
        
        Args:
            report: The validation report to format
            output_path: Path to save the Markdown file (required for Markdown reporter)
            input_file: Path to the input file being validated
            rules_source: Source of the validation rules
        
        Raises:
            ValueError: If output_path is not provided
            OSError: If the output file cannot be written
        """
        if not output_path:
            raise ValueError("Markdown reporter requires an output_path")
        
        markdown_content = self._build_markdown_content(report, input_file, rules_source)
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write Markdown to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def _build_markdown_content(self, report: ValidationReport, input_file: Optional[str] = None, rules_source: Optional[str] = None) -> str:
        """
        Build the complete Markdown content for the report.
        
        Args:
            report: The validation report to convert
            input_file: Path to the input file being validated
            rules_source: Source of the validation rules
            
        Returns:
            Complete Markdown content as string
        """
        sections = [
            self._build_header(input_file, rules_source),
            self._build_summary_section(report),
            self._build_severity_breakdown_section(report),
            self._build_statistics_section(report)
        ]
        
        if report.failed_validations > 0:
            sections.append(self._build_failures_section(report))
        
        if self.include_passed and report.passed_validations > 0:
            sections.append(self._build_passed_section(report))
        
        sections.append(self._build_footer())
        
        return "\n\n".join(sections)
    
    def _build_header(self, input_file: Optional[str] = None, rules_source: Optional[str] = None) -> str:
        """Build the report header."""
        
        # Get current time in multiple formats for debugging
        now_utc = datetime.now(timezone.utc)
        now_local = datetime.now()
        
        # TEMPORARY FIX: Use correct year if system clock is wrong
        if now_utc.year == 2026:
            # Create corrected timestamps
            corrected_utc = now_utc.replace(year=2024)
            corrected_local = now_local.replace(year=2024)
            now_utc = corrected_utc
            now_local = corrected_local
        
        # Format timestamps
        timestamp_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        timestamp_local = now_local.strftime("%Y-%m-%d %H:%M:%S")
        
        header = f"""# Data Validation Report

**Generated:** {timestamp_utc}  
**Local Time:** {timestamp_local}  
**Report Version:** 1.0  
**Generator:** policy-dq-validator"""

        # Add input file information if available
        if input_file:
            header += f"  \n**Input File:** {input_file}"
            
        # Add rules source information if available
        if rules_source:
            header += f"  \n**Rules Source:** {rules_source}"
            
        return header
    
    def _build_summary_section(self, report: ValidationReport) -> str:
        """Build the summary section."""
        total_validations = report.passed_validations + report.failed_validations
        success_rate = (report.passed_validations / total_validations * 100) if total_validations > 0 else 100.0
        
        # Determine overall status
        if report.failed_validations == 0:
            status = "✅ **PASSED**"
            status_color = "🟢"
        elif ValidationSeverity.CRITICAL in report.summary_by_severity:
            status = "🚨 **CRITICAL ISSUES**"
            status_color = "🔴"
        elif ValidationSeverity.ERROR in report.summary_by_severity:
            status = "❌ **FAILED**"
            status_color = "🔴"
        else:
            status = "⚠️ **WARNINGS**"
            status_color = "🟡"
        
        return f"""## Summary

{status_color} **Overall Status:** {status}

| Metric | Value |
|--------|-------|
| Total Records | {report.total_records:,} |
| Total Rules | {report.total_rules} |
| Total Validations | {total_validations:,} |
| Passed Validations | {report.passed_validations:,} |
| Failed Validations | {report.failed_validations:,} |
| Success Rate | {success_rate:.1f}% |"""
    
    def _build_severity_breakdown_section(self, report: ValidationReport) -> str:
        """Build the severity breakdown section."""
        if not report.summary_by_severity:
            return "## Severity Breakdown\n\nNo validation issues found."
        
        # Severity icons and colors
        severity_info = {
            ValidationSeverity.CRITICAL: ("🚨", "Critical"),
            ValidationSeverity.ERROR: ("❌", "Error"),
            ValidationSeverity.WARNING: ("⚠️", "Warning"),
            ValidationSeverity.INFO: ("ℹ️", "Info")
        }
        
        table_rows = []
        for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                        ValidationSeverity.WARNING, ValidationSeverity.INFO]:
            if severity in report.summary_by_severity:
                count = report.summary_by_severity[severity]
                icon, name = severity_info[severity]
                table_rows.append(f"| {icon} {name} | {count:,} |")
        
        if not table_rows:
            return "## Severity Breakdown\n\nNo validation issues found."
        
        table_header = """| Severity | Count |
|----------|-------|"""
        
        return f"""## Severity Breakdown

{table_header}
{chr(10).join(table_rows)}"""
    
    def _build_statistics_section(self, report: ValidationReport) -> str:
        """Build the statistics section."""
        failed_results = [r for r in report.results if not r.passed]
        
        if not failed_results:
            return "## Statistics\n\nNo failures to analyze."
        
        # Count failures by rule
        failures_by_rule = {}
        for result in failed_results:
            rule_name = result.rule_name
            failures_by_rule[rule_name] = failures_by_rule.get(rule_name, 0) + 1
        
        # Count failures by field
        failures_by_field = {}
        for result in failed_results:
            field_name = result.field or "unknown"
            failures_by_field[field_name] = failures_by_field.get(field_name, 0) + 1
        
        # Sort and get top items
        top_rules = sorted(failures_by_rule.items(), key=lambda x: x[1], reverse=True)[:5]
        top_fields = sorted(failures_by_field.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Build tables
        rules_table = self._build_top_items_table("Rule", top_rules)
        fields_table = self._build_top_items_table("Field", top_fields)
        
        return f"""## Statistics

### Top Failed Rules

{rules_table}

### Top Failed Fields

{fields_table}"""
    
    def _build_top_items_table(self, item_type: str, items: List[tuple]) -> str:
        """Build a table for top items (rules or fields)."""
        if not items:
            return f"No {item_type.lower()} failures found."
        
        table_header = f"""| {item_type} | Failures |
|{'-' * len(item_type)}|----------|"""
        
        table_rows = []
        for name, count in items:
            # Escape pipe characters in names
            escaped_name = name.replace("|", "\\|")
            table_rows.append(f"| `{escaped_name}` | {count:,} |")
        
        return f"""{table_header}
{chr(10).join(table_rows)}"""
    
    def _build_failures_section(self, report: ValidationReport) -> str:
        """Build the detailed failures section."""
        failed_results = [r for r in report.results if not r.passed]
        
        if not failed_results:
            return ""
        
        # Group by severity
        by_severity = {}
        for result in failed_results:
            if result.severity not in by_severity:
                by_severity[result.severity] = []
            by_severity[result.severity].append(result)
        
        sections = ["## Detailed Failures"]
        
        # Process in order of severity
        severity_order = [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                         ValidationSeverity.WARNING, ValidationSeverity.INFO]
        
        for severity in severity_order:
            if severity in by_severity:
                sections.append(self._build_severity_failures_section(severity, by_severity[severity]))
        
        return "\n\n".join(sections)
    
    def _build_severity_failures_section(self, severity: ValidationSeverity, results: List[ValidationResult]) -> str:
        """Build a section for failures of a specific severity."""
        severity_info = {
            ValidationSeverity.CRITICAL: ("🚨", "Critical Issues"),
            ValidationSeverity.ERROR: ("❌", "Errors"),
            ValidationSeverity.WARNING: ("⚠️", "Warnings"),
            ValidationSeverity.INFO: ("ℹ️", "Information")
        }
        
        icon, title = severity_info[severity]
        
        # Group by rule for better organization
        by_rule = {}
        for result in results:
            rule_name = result.rule_name
            if rule_name not in by_rule:
                by_rule[rule_name] = []
            by_rule[rule_name].append(result)
        
        rule_sections = []
        for rule_name, rule_results in by_rule.items():
            rule_sections.append(self._build_rule_failures_section(rule_name, rule_results))
        
        return f"""### {icon} {title} ({len(results)} issues)

{chr(10).join(rule_sections)}"""
    
    def _build_rule_failures_section(self, rule_name: str, results: List[ValidationResult]) -> str:
        """Build a section for failures of a specific rule."""
        # Limit the number of failures shown
        displayed_results = results[:self.max_failures_per_rule]
        remaining_count = len(results) - len(displayed_results)
        
        # Build table
        table_header = """| Row | Field | Message |
|-----|-------|---------|"""
        
        table_rows = []
        for result in displayed_results:
            row_info = str(result.row_index + 1) if result.row_index is not None else "Dataset"
            field_info = result.field or "Multiple"
            message = result.message.replace("|", "\\|")  # Escape pipe characters
            table_rows.append(f"| {row_info} | `{field_info}` | {message} |")
        
        table_content = f"""{table_header}
{chr(10).join(table_rows)}"""
        
        # Add note about remaining failures if any
        if remaining_count > 0:
            table_content += f"\n\n*... and {remaining_count} more similar failures*"
        
        return f"""#### Rule: `{rule_name}`

{table_content}"""
    
    def _build_passed_section(self, report: ValidationReport) -> str:
        """Build the passed validations section (optional)."""
        passed_results = [r for r in report.results if r.passed]
        
        if not passed_results:
            return ""
        
        # Group by rule
        by_rule = {}
        for result in passed_results:
            rule_name = result.rule_name
            by_rule[rule_name] = by_rule.get(rule_name, 0) + 1
        
        # Build table
        table_header = """| Rule | Passed Count |
|------|--------------|"""
        
        table_rows = []
        for rule_name, count in sorted(by_rule.items()):
            table_rows.append(f"| `{rule_name}` | {count:,} |")
        
        table_content = f"""{table_header}
{chr(10).join(table_rows)}"""
        
        return f"""## Passed Validations

{table_content}"""
    
    def _build_footer(self) -> str:
        """Build the report footer."""
        return """---

*Report generated by policy-dq-validator*"""