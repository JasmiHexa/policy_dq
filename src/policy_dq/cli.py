"""
Command-line interface for the data validation system.

This module provides CLI commands for validating data files and processing
validation reports using the click framework.
"""

import json
import sys
import traceback
from pathlib import Path

import click

from .engine import ValidationEngine
from .config import ValidationConfig, RuleSourceConfig, OutputConfig
from .exceptions import (
    ValidationAPIError, 
    ConfigurationError, 
    DataSourceError, 
    ValidationExecutionError,
    ReportGenerationError
)
from .utils import analyze_validation_results
from .models import ValidationSeverity


# Exit codes for different error conditions
class ExitCodes:
    """Standard exit codes for the CLI application."""
    SUCCESS = 0                    # Validation passed
    VALIDATION_FAILED = 1          # Validation failed (severity threshold exceeded)
    CONFIGURATION_ERROR = 2        # Configuration or argument errors
    DATA_SOURCE_ERROR = 3          # Input file or data source errors
    VALIDATION_EXECUTION_ERROR = 4 # Validation execution errors
    REPORT_GENERATION_ERROR = 5    # Report generation errors
    UNEXPECTED_ERROR = 10          # Unexpected system errors


@click.group()
@click.version_option(version="1.0.0", prog_name="policy-dq")
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.pass_context
def cli(ctx, verbose):
    """
    Policy Data Quality - A comprehensive data validation system.
    
    This tool validates structured data files (CSV and JSON) against configurable
    business and data-quality policies. It supports flexible rule loading from
    local files or MCP sources and generates detailed reports in multiple formats.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose


@cli.command()
@click.argument('input_file', type=click.Path(readable=True))
@click.option(
    '--rules', '-r',
    required=False,
    type=str,
    help='Path to rules file or MCP source identifier'
)
@click.option(
    '--output-dir', '-o',
    type=click.Path(),
    help='Output directory for validation reports'
)
@click.option(
    '--severity-threshold', '-s',
    type=click.Choice(['info', 'warning', 'error', 'critical'], case_sensitive=False),
    default='error',
    help='Minimum severity level for exit code determination (default: error)'
)
@click.option(
    '--fail-fast',
    is_flag=True,
    help='Stop validation on first critical error'
)
@click.option(
    '--no-console',
    is_flag=True,
    help='Disable console output'
)
@click.option(
    '--no-json',
    is_flag=True,
    help='Disable JSON report generation'
)
@click.option(
    '--no-markdown',
    is_flag=True,
    help='Disable Markdown report generation'
)
@click.option(
    '--no-colors',
    is_flag=True,
    help='Disable colored console output'
)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, readable=True),
    help='Configuration file (JSON or YAML)'
)
@click.pass_context
def validate(ctx, input_file, rules, output_dir, severity_threshold, fail_fast, 
             no_console, no_json, no_markdown, no_colors, config):
    """
    Validate a data file against validation rules.
    
    INPUT_FILE: Path to the data file to validate (CSV or JSON)
    
    Examples:
    
      # Validate CSV file with local rules
      policy-dq validate data.csv --rules rules.yaml
      
      # Validate with custom output directory
      policy-dq validate data.csv --rules rules.json --output-dir ./reports
      
      # Validate with custom severity threshold
      policy-dq validate data.csv --rules rules.yaml --severity-threshold warning
      
      # Validate with MCP source
      policy-dq validate data.csv --rules mcp://server/ruleset-id
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Check if input file exists
        if not Path(input_file).exists():
            raise DataSourceError(f"Input file not found: {input_file}", source_path=input_file)
        
        # Load configuration
        if config:
            validation_config = ValidationConfig.from_file(config)
        else:
            # Validate that rules are provided when not using config file
            if not rules:
                raise ConfigurationError("Either --rules option or --config file must be provided")
            
            # Create configuration from command line options
            rule_source = RuleSourceConfig(source=rules)
            output_config = OutputConfig(
                output_directory=output_dir,
                generate_console_report=not no_console,
                generate_json_report=not no_json,
                generate_markdown_report=not no_markdown,
                console_colors=not no_colors
            )
            
            validation_config = ValidationConfig(
                rule_source=rule_source,
                output=output_config,
                fail_fast=fail_fast,
                severity_threshold=ValidationSeverity(severity_threshold.lower()),
                log_level='DEBUG' if verbose else 'INFO'
            )
        
        if verbose:
            click.echo(f"Validating file: {input_file}")
            click.echo(f"Using rules: {rules}")
            if output_dir:
                click.echo(f"Output directory: {output_dir}")
        
        # Create validation engine and validate file
        engine = ValidationEngine(validation_config)
        report = engine.validate_file(input_file)
        
        # Check severity threshold for exit code
        threshold_met = engine.check_severity_threshold(report)
        
        if verbose:
            click.echo("\nValidation completed:")
            click.echo(f"  Total records: {report.total_records:,}")
            click.echo(f"  Passed validations: {report.passed_validations:,}")
            click.echo(f"  Failed validations: {report.failed_validations:,}")
            
            if report.summary_by_severity:
                click.echo("  Severity breakdown:")
                for severity, count in report.summary_by_severity.items():
                    if count > 0:
                        click.echo(f"    {severity.value.upper()}: {count:,}")
        
        # Exit with appropriate code based on severity threshold
        if not threshold_met:
            failed_above_threshold = _count_failures_above_threshold(
                report, ValidationSeverity(severity_threshold.lower())
            )
            
            if verbose:
                click.echo(f"\nValidation failed: {failed_above_threshold} validation(s) exceed {severity_threshold} threshold")
            else:
                click.echo(f"Validation failed: {failed_above_threshold} validation(s) at {severity_threshold} level or higher", err=True)
            
            sys.exit(ExitCodes.VALIDATION_FAILED)
        else:
            if verbose:
                click.echo(f"\nValidation passed: All results meet {severity_threshold} threshold")
            
            sys.exit(ExitCodes.SUCCESS)
            
    except ConfigurationError as e:
        _handle_configuration_error(e, verbose)
    except DataSourceError as e:
        _handle_data_source_error(e, verbose)
    except ValidationExecutionError as e:
        _handle_validation_execution_error(e, verbose)
    except ReportGenerationError as e:
        _handle_report_generation_error(e, verbose)
    except ValidationAPIError as e:
        _handle_generic_validation_error(e, verbose)
    except (KeyboardInterrupt, click.Abort):
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(ExitCodes.UNEXPECTED_ERROR)
    except Exception as e:
        _handle_unexpected_error(e, verbose)


@cli.command()
@click.argument('report_file', type=click.Path(readable=True))
@click.option(
    '--format', '-f',
    type=click.Choice(['summary', 'detailed', 'analysis'], case_sensitive=False),
    default='summary',
    help='Output format (default: summary)'
)
@click.option(
    '--field',
    type=str,
    help='Filter results by field name'
)
@click.option(
    '--rule',
    type=str,
    help='Filter results by rule name'
)
@click.option(
    '--severity',
    type=click.Choice(['info', 'warning', 'error', 'critical'], case_sensitive=False),
    help='Filter results by severity level'
)
@click.option(
    '--failed-only',
    is_flag=True,
    help='Show only failed validations'
)
@click.option(
    '--limit', '-l',
    type=int,
    default=50,
    help='Limit number of results shown (default: 50)'
)
@click.pass_context
def summarize(ctx, report_file, format, field, rule, severity, failed_only, limit):
    """
    Summarize and analyze an existing JSON validation report.
    
    REPORT_FILE: Path to the JSON validation report file
    
    Examples:
    
      # Basic summary
      policy-dq summarize validation_report.json
      
      # Detailed analysis
      policy-dq summarize validation_report.json -f analysis
      
      # Filter by field
      policy-dq summarize validation_report.json --field email
      
      # Show only failed validations
      policy-dq summarize validation_report.json --failed-only
    """
    verbose = ctx.obj.get('verbose', False)
    
    try:
        # Load the JSON report
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        if verbose:
            click.echo(f"Loading report: {report_file}")
        
        # Convert to ValidationReport object (simplified reconstruction)
        from .models import ValidationResult, ValidationSeverity
        
        # Extract basic report info
        metadata = report_data.get('metadata', {})
        summary = report_data.get('summary', {})
        results_data = report_data.get('results', [])
        
        # Validate required fields
        if 'total_records' not in summary:
            raise KeyError("'total_records' missing from summary")
        if 'passed_validations' not in summary:
            raise KeyError("'passed_validations' missing from summary")
        if 'failed_validations' not in summary:
            raise KeyError("'failed_validations' missing from summary")
        
        # Reconstruct ValidationResult objects
        results = []
        for result_data in results_data:
            result = ValidationResult(
                rule_name=result_data['rule_name'],
                field=result_data['field'],
                row_index=result_data.get('row_index'),
                severity=ValidationSeverity(result_data['severity']),
                message=result_data['message'],
                passed=result_data['passed']
            )
            results.append(result)
        
        # Apply filters
        filtered_results = results
        
        if field:
            filtered_results = [r for r in filtered_results if r.field == field]
        
        if rule:
            filtered_results = [r for r in filtered_results if r.rule_name == rule]
        
        if severity:
            target_severity = ValidationSeverity(severity.lower())
            filtered_results = [r for r in filtered_results if r.severity == target_severity]
        
        if failed_only:
            filtered_results = [r for r in filtered_results if not r.passed]
        
        # Limit results
        if limit > 0:
            filtered_results = filtered_results[:limit]
        
        # Generate output based on format
        if format == 'summary':
            _show_summary(report_data, filtered_results, verbose)
        elif format == 'detailed':
            _show_detailed(report_data, filtered_results, verbose)
        elif format == 'analysis':
            _show_analysis(report_data, results, verbose)
        
        # Exit successfully
        sys.exit(ExitCodes.SUCCESS)
        
    except FileNotFoundError:
        click.echo(f"Report file not found: {report_file}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Verify the report file path is correct", err=True)
        click.echo("  - Check if the file was moved or deleted", err=True)
        click.echo("  - Ensure you have read permissions for the file", err=True)
        sys.exit(ExitCodes.DATA_SOURCE_ERROR)
    except json.JSONDecodeError as e:
        click.echo(f"Invalid JSON in report file: {e}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Verify the file is a valid JSON report", err=True)
        click.echo("  - Check if the file was corrupted during transfer", err=True)
        click.echo("  - Ensure the file was generated by this tool", err=True)
        if verbose:
            click.echo(f"\nJSON error details: {e}", err=True)
        sys.exit(ExitCodes.DATA_SOURCE_ERROR)
    except KeyError as e:
        click.echo(f"Missing required field in report file: {e}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Verify the file is a complete validation report", err=True)
        click.echo("  - Check if the report format is compatible", err=True)
        click.echo("  - Try regenerating the report", err=True)
        if verbose:
            click.echo(f"\nMissing field: {e}", err=True)
        sys.exit(ExitCodes.DATA_SOURCE_ERROR)
    except ValueError as e:
        click.echo(f"Invalid data in report file: {e}", err=True)
        click.echo("\nSuggestions:", err=True)
        click.echo("  - Check if severity values are valid", err=True)
        click.echo("  - Verify the report format is correct", err=True)
        click.echo("  - Try with a different report file", err=True)
        if verbose:
            click.echo(f"\nValue error details: {e}", err=True)
        sys.exit(ExitCodes.DATA_SOURCE_ERROR)
    except (KeyboardInterrupt, click.Abort):
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(ExitCodes.UNEXPECTED_ERROR)
    except Exception as e:
        click.echo(f"Error processing report: {e}", err=True)
        click.echo("\nThis appears to be an unexpected error.", err=True)
        if verbose:
            click.echo("\nFull traceback:", err=True)
            click.echo(traceback.format_exc(), err=True)
        else:
            click.echo("Run with --verbose flag for detailed error information.", err=True)
        sys.exit(ExitCodes.UNEXPECTED_ERROR)


def _show_summary(report_data, filtered_results, verbose):
    """Show summary format output."""
    metadata = report_data.get('metadata', {})
    summary = report_data.get('summary', {})
    
    click.echo("=== Validation Report Summary ===")
    
    if metadata:
        click.echo(f"Input file: {metadata.get('input_file', 'Unknown')}")
        click.echo(f"Rules source: {metadata.get('rules_source', 'Unknown')}")
        click.echo(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
        click.echo()
    
    click.echo(f"Total records: {summary.get('total_records', 0):,}")
    click.echo(f"Total rules: {metadata.get('total_rules', 0)}")
    click.echo(f"Passed validations: {summary.get('passed_validations', 0):,}")
    click.echo(f"Failed validations: {summary.get('failed_validations', 0):,}")
    
    # Show severity breakdown
    severity_summary = summary.get('by_severity', {})
    if severity_summary:
        click.echo("\nSeverity breakdown:")
        for severity, count in severity_summary.items():
            if count > 0:
                click.echo(f"  {severity.upper()}: {count:,}")
    
    # Show filtered results count
    if len(filtered_results) < len(report_data.get('results', [])):
        click.echo(f"\nShowing {len(filtered_results)} filtered results")


def _show_detailed(report_data, filtered_results, verbose):
    """Show detailed format output."""
    _show_summary(report_data, filtered_results, verbose)
    
    if not filtered_results:
        click.echo("\nNo results to display.")
        return
    
    click.echo(f"\n=== Detailed Results ({len(filtered_results)} items) ===")
    
    for i, result in enumerate(filtered_results, 1):
        status = "PASS" if result.passed else "FAIL"
        row_info = f" (row {result.row_index})" if result.row_index is not None else ""
        
        click.echo(f"\n{i}. [{status}] {result.rule_name}")
        click.echo(f"   Field: {result.field}{row_info}")
        click.echo(f"   Severity: {result.severity.value.upper()}")
        click.echo(f"   Message: {result.message}")


def _show_analysis(report_data, results, verbose):
    """Show analysis format output."""
    from .models import ValidationReport, ValidationSeverity
    
    # Reconstruct ValidationReport for analysis
    metadata = report_data.get('metadata', {})
    summary = report_data.get('summary', {})
    
    # Convert severity summary back to enum keys
    severity_by_enum = {}
    for severity_str, count in summary.get('by_severity', {}).items():
        try:
            severity_enum = ValidationSeverity(severity_str.lower())
            severity_by_enum[severity_enum] = count
        except ValueError:
            continue
    
    report = ValidationReport(
        total_records=summary.get('total_records', 0),
        total_rules=metadata.get('total_rules', 0),
        passed_validations=summary.get('passed_validations', 0),
        failed_validations=summary.get('failed_validations', 0),
        results=results,
        summary_by_severity=severity_by_enum
    )
    
    # Generate analysis
    analysis = analyze_validation_results(report)
    
    click.echo("=== Validation Analysis ===")
    
    # Overall statistics
    overall = analysis['overall']
    click.echo(f"Success rate: {overall['success_rate']:.1f}%")
    click.echo(f"Total validations: {overall['total_validations']:,}")
    
    # Top failing fields
    click.echo("\nTop failing fields:")
    for field, failure_count in analysis['top_failing_fields'][:5]:
        click.echo(f"  {field}: {failure_count:,} failures")
    
    # Top failing rules
    click.echo("\nTop failing rules:")
    for rule, failure_count in analysis['top_failing_rules'][:5]:
        click.echo(f"  {rule}: {failure_count:,} failures")
    
    # Common error patterns
    click.echo("\nCommon error patterns:")
    for message, count in analysis['error_patterns'][:5]:
        # Truncate long messages
        display_message = message[:60] + "..." if len(message) > 60 else message
        click.echo(f"  {display_message}: {count:,} occurrences")


def _count_failures_above_threshold(report, threshold_severity):
    """
    Count validation failures at or above the specified severity threshold.
    
    Args:
        report: ValidationReport to analyze
        threshold_severity: ValidationSeverity threshold level
        
    Returns:
        Number of failed validations at or above threshold
    """
    severity_order = {
        ValidationSeverity.INFO: 0,
        ValidationSeverity.WARNING: 1,
        ValidationSeverity.ERROR: 2,
        ValidationSeverity.CRITICAL: 3
    }
    
    threshold_level = severity_order[threshold_severity]
    
    count = 0
    for result in report.results:
        if not result.passed and severity_order[result.severity] >= threshold_level:
            count += 1
    
    return count


def _handle_configuration_error(error, verbose):
    """Handle configuration-related errors with user-friendly messages."""
    if hasattr(error, 'config_key') and error.config_key:
        click.echo(f"Configuration error in '{error.config_key}': {error.message}", err=True)
    else:
        click.echo(f"Configuration error: {error.message}", err=True)
    
    # Provide helpful suggestions
    click.echo("\nSuggestions:", err=True)
    click.echo("  - Check your configuration file syntax (JSON/YAML)", err=True)
    click.echo("  - Verify all required configuration parameters are provided", err=True)
    click.echo("  - Use --help to see available options", err=True)
    
    if verbose and hasattr(error, 'details') and error.details:
        click.echo(f"\nDetails: {error.details}", err=True)
    
    sys.exit(ExitCodes.CONFIGURATION_ERROR)


def _handle_data_source_error(error, verbose):
    """Handle data source-related errors with user-friendly messages."""
    if hasattr(error, 'source_path') and error.source_path:
        click.echo(f"Data source error with '{error.source_path}': {error.message}", err=True)
    else:
        click.echo(f"Data source error: {error.message}", err=True)
    
    # Provide helpful suggestions
    click.echo("\nSuggestions:", err=True)
    click.echo("  - Verify the input file exists and is readable", err=True)
    click.echo("  - Check file format is supported (CSV or JSON)", err=True)
    click.echo("  - Ensure file is not corrupted or malformed", err=True)
    click.echo("  - Check file encoding (UTF-8 recommended)", err=True)
    
    if verbose and hasattr(error, 'details') and error.details:
        click.echo(f"\nDetails: {error.details}", err=True)
    
    sys.exit(ExitCodes.DATA_SOURCE_ERROR)


def _handle_validation_execution_error(error, verbose):
    """Handle validation execution errors with user-friendly messages."""
    stage_info = f" during {error.stage}" if hasattr(error, 'stage') and error.stage else ""
    click.echo(f"Validation execution error{stage_info}: {error.message}", err=True)
    
    # Provide helpful suggestions based on stage
    click.echo("\nSuggestions:", err=True)
    if hasattr(error, 'stage'):
        if error.stage == 'rule_loading':
            click.echo("  - Verify rules file exists and is accessible", err=True)
            click.echo("  - Check rules file format and syntax", err=True)
            click.echo("  - Ensure MCP server is running (if using MCP rules)", err=True)
        elif error.stage == 'input_validation':
            click.echo("  - Check input data format and structure", err=True)
            click.echo("  - Ensure data is not empty", err=True)
        else:
            click.echo("  - Check system resources (memory, disk space)", err=True)
            click.echo("  - Try with a smaller dataset", err=True)
    else:
        click.echo("  - Check system resources and try again", err=True)
        click.echo("  - Verify all input files are accessible", err=True)
    
    if verbose and hasattr(error, 'details') and error.details:
        click.echo(f"\nDetails: {error.details}", err=True)
    
    sys.exit(ExitCodes.VALIDATION_EXECUTION_ERROR)


def _handle_report_generation_error(error, verbose):
    """Handle report generation errors with user-friendly messages."""
    report_type_info = f" for {error.report_type} report" if hasattr(error, 'report_type') and error.report_type else ""
    click.echo(f"Report generation error{report_type_info}: {error.message}", err=True)
    
    # Provide helpful suggestions
    click.echo("\nSuggestions:", err=True)
    click.echo("  - Check output directory exists and is writable", err=True)
    click.echo("  - Ensure sufficient disk space is available", err=True)
    click.echo("  - Verify file permissions for output location", err=True)
    click.echo("  - Try a different output directory", err=True)
    
    if verbose and hasattr(error, 'details') and error.details:
        click.echo(f"\nDetails: {error.details}", err=True)
    
    sys.exit(ExitCodes.REPORT_GENERATION_ERROR)


def _handle_generic_validation_error(error, verbose):
    """Handle generic validation API errors."""
    click.echo(f"Validation error: {error.message}", err=True)
    
    if verbose and hasattr(error, 'details') and error.details:
        click.echo(f"\nDetails: {error.details}", err=True)
    
    sys.exit(ExitCodes.VALIDATION_EXECUTION_ERROR)


def _handle_unexpected_error(error, verbose):
    """Handle unexpected system errors."""
    click.echo(f"Unexpected error: {error}", err=True)
    
    click.echo("\nThis appears to be an unexpected system error.", err=True)
    click.echo("Please report this issue with the following information:", err=True)
    
    if verbose:
        click.echo("\nFull traceback:", err=True)
        click.echo(traceback.format_exc(), err=True)
    else:
        click.echo("Run with --verbose flag for detailed error information.", err=True)
    
    sys.exit(ExitCodes.UNEXPECTED_ERROR)


if __name__ == '__main__':
    cli()