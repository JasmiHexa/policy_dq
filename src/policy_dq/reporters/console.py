"""
Console reporter for validation results.

This module provides colored console output with progress indicators
and summary statistics for validation reports.
"""

import sys
from typing import Optional, TextIO
from colorama import Fore, Style, init
from ..models import ValidationReport, ValidationResult, ValidationSeverity
from .base import Reporter


class ConsoleReporter(Reporter):
    """
    Reporter that outputs validation results to the console with colored formatting.
    
    Features:
    - Colored output based on severity levels
    - Progress indicators during validation
    - Summary statistics with severity breakdown
    - Detailed error listings
    """
    
    def __init__(self, output_stream: TextIO = sys.stdout, use_colors: bool = True):
        """
        Initialize the console reporter.
        
        Args:
            output_stream: Stream to write output to (default: stdout)
            use_colors: Whether to use colored output (default: True)
        """
        self.output_stream = output_stream
        self.use_colors = use_colors
        
        if self.use_colors:
            init(autoreset=True)
        
        # Color mappings for severity levels
        self.severity_colors = {
            ValidationSeverity.INFO: Fore.CYAN,
            ValidationSeverity.WARNING: Fore.YELLOW,
            ValidationSeverity.ERROR: Fore.RED,
            ValidationSeverity.CRITICAL: Fore.MAGENTA + Style.BRIGHT
        }
        
        # Symbols for severity levels
        self.severity_symbols = {
            ValidationSeverity.INFO: "ℹ",
            ValidationSeverity.WARNING: "⚠",
            ValidationSeverity.ERROR: "✗",
            ValidationSeverity.CRITICAL: "🚨"
        }
    
    def generate_report(self, report: ValidationReport, output_path: Optional[str] = None) -> None:
        """
        Generate and display the validation report to console.
        
        Args:
            report: The validation report to display
            output_path: Ignored for console reporter
        """
        self._print_header()
        self._print_summary(report)
        self._print_severity_breakdown(report)
        
        if report.failed_validations > 0:
            self._print_failed_validations(report)
        
        self._print_footer(report)
    
    def show_progress(self, current: int, total: int, message: str = "Processing") -> None:
        """
        Display a progress indicator.
        
        Args:
            current: Current progress count
            total: Total items to process
            message: Progress message to display
        """
        if total == 0:
            return
            
        percentage = (current / total) * 100
        bar_length = 40
        filled_length = int(bar_length * current // total)
        
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        
        color = Fore.GREEN if self.use_colors else ""
        reset = Style.RESET_ALL if self.use_colors else ""
        
        progress_line = f"\r{color}{message}: [{bar}] {percentage:.1f}% ({current}/{total}){reset}"
        
        self.output_stream.write(progress_line)
        self.output_stream.flush()
        
        if current == total:
            self.output_stream.write("\n")
    
    def _print_header(self) -> None:
        """Print the report header."""
        header_color = Fore.BLUE + Style.BRIGHT if self.use_colors else ""
        reset = Style.RESET_ALL if self.use_colors else ""
        
        self._print_line("=" * 60)
        self._print_line(f"{header_color}DATA VALIDATION REPORT{reset}")
        self._print_line("=" * 60)
    
    def _print_summary(self, report: ValidationReport) -> None:
        """Print the validation summary statistics."""
        success_color = Fore.GREEN if self.use_colors else ""
        error_color = Fore.RED if self.use_colors else ""
        reset = Style.RESET_ALL if self.use_colors else ""
        
        self._print_line(f"Total Records Processed: {report.total_records}")
        self._print_line(f"Total Rules Applied: {report.total_rules}")
        self._print_line(f"{success_color}Passed Validations: {report.passed_validations}{reset}")
        self._print_line(f"{error_color}Failed Validations: {report.failed_validations}{reset}")
        
        # Calculate success rate
        total_validations = report.passed_validations + report.failed_validations
        if total_validations > 0:
            success_rate = (report.passed_validations / total_validations) * 100
            rate_color = Fore.GREEN if success_rate >= 90 else Fore.YELLOW if success_rate >= 70 else Fore.RED
            rate_color = rate_color if self.use_colors else ""
            self._print_line(f"{rate_color}Success Rate: {success_rate:.1f}%{reset}")
    
    def _print_severity_breakdown(self, report: ValidationReport) -> None:
        """Print the breakdown of results by severity level."""
        if not report.summary_by_severity:
            return
        
        self._print_line("\nSeverity Breakdown:")
        self._print_line("-" * 20)
        
        for severity, count in report.summary_by_severity.items():
            if count > 0:
                color = self.severity_colors.get(severity, "") if self.use_colors else ""
                symbol = self.severity_symbols.get(severity, "•")
                reset = Style.RESET_ALL if self.use_colors else ""
                
                self._print_line(f"{color}{symbol} {severity.value.upper()}: {count}{reset}")
    
    def _print_failed_validations(self, report: ValidationReport) -> None:
        """Print detailed information about failed validations."""
        failed_results = [r for r in report.results if not r.passed]
        
        if not failed_results:
            return
        
        self._print_line(f"\nFailed Validations ({len(failed_results)}):")
        self._print_line("-" * 40)
        
        # Group by severity for better organization
        by_severity = {}
        for result in failed_results:
            if result.severity not in by_severity:
                by_severity[result.severity] = []
            by_severity[result.severity].append(result)
        
        # Print in order of severity (critical first)
        severity_order = [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR, 
                         ValidationSeverity.WARNING, ValidationSeverity.INFO]
        
        for severity in severity_order:
            if severity in by_severity:
                self._print_severity_group(severity, by_severity[severity])
    
    def _print_severity_group(self, severity: ValidationSeverity, results: list[ValidationResult]) -> None:
        """Print a group of results with the same severity."""
        color = self.severity_colors.get(severity, "") if self.use_colors else ""
        symbol = self.severity_symbols.get(severity, "•")
        reset = Style.RESET_ALL if self.use_colors else ""
        
        self._print_line(f"\n{color}{symbol} {severity.value.upper()} ({len(results)} issues):{reset}")
        
        for result in results:
            row_info = f"Row {result.row_index + 1}" if result.row_index is not None else "Dataset"
            field_info = f"Field '{result.field}'" if result.field else "Multiple fields"
            
            self._print_line(f"  • {row_info}, {field_info}: {result.message}")
            self._print_line(f"    Rule: {result.rule_name}")
    
    def _print_footer(self, report: ValidationReport) -> None:
        """Print the report footer with overall status."""
        self._print_line("\n" + "=" * 60)
        
        if report.failed_validations == 0:
            color = Fore.GREEN + Style.BRIGHT if self.use_colors else ""
            status = "✓ ALL VALIDATIONS PASSED"
        else:
            # Determine overall status based on severity
            has_critical = ValidationSeverity.CRITICAL in report.summary_by_severity
            has_errors = ValidationSeverity.ERROR in report.summary_by_severity
            
            if has_critical:
                color = Fore.MAGENTA + Style.BRIGHT if self.use_colors else ""
                status = "🚨 CRITICAL ISSUES FOUND"
            elif has_errors:
                color = Fore.RED + Style.BRIGHT if self.use_colors else ""
                status = "✗ VALIDATION ERRORS FOUND"
            else:
                color = Fore.YELLOW + Style.BRIGHT if self.use_colors else ""
                status = "⚠ VALIDATION WARNINGS FOUND"
        
        reset = Style.RESET_ALL if self.use_colors else ""
        self._print_line(f"{color}{status}{reset}")
        self._print_line("=" * 60)
    
    def _print_line(self, text: str) -> None:
        """Print a line to the output stream."""
        self.output_stream.write(text + "\n")
        self.output_stream.flush()