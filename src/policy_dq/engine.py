"""
Main validation engine that orchestrates the complete validation workflow.

This module provides the ValidationEngine class that coordinates parsers,
validators, and reporters to provide a unified API for data validation.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import ValidationConfig
from .exceptions import (
    ConfigurationError,
    ValidationExecutionError,
    DataSourceError,
    ReportGenerationError
)
from .models import ValidationReport, ValidationResult, ValidationSeverity
from .parsers.factory import ParserFactory, UnsupportedFormatError
from .parsers.base import DataParsingError
from .validators.core import DataValidator
from .rules.manager import RuleLoadingManager, MCPRuleLoadingManager
from .rules.base import RuleLoadingError
from .reporters.console import ConsoleReporter
from .reporters.json_reporter import JSONReporter
from .reporters.markdown import MarkdownReporter


logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Main validation engine that orchestrates the complete validation workflow.
    
    The ValidationEngine provides a high-level API for data validation that
    coordinates parsing, rule loading, validation execution, and report generation.
    It's designed to be completely independent of CLI concerns and suitable for
    integration into Python applications.
    """
    
    def __init__(self, config: ValidationConfig):
        """
        Initialize the validation engine with configuration.
        
        Args:
            config: ValidationConfig instance with all settings
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate configuration
        try:
            config.validate()
        except Exception as e:
            raise ConfigurationError(f"Invalid configuration: {e}")
        
        self.config = config
        
        # Initialize components
        self._setup_logging()
        self._parser_factory = ParserFactory()
        self._rule_manager = self._create_rule_manager()
        
        logger.info("ValidationEngine initialized successfully")
    
    def validate_file(
        self, 
        file_path: str,
        rule_source: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate a single data file against validation rules.
        
        Args:
            file_path: Path to the data file to validate
            rule_source: Optional override for rule source
            
        Returns:
            ValidationReport with validation results
            
        Raises:
            DataSourceError: If file cannot be accessed or parsed
            ValidationExecutionError: If validation fails
        """
        logger.info(f"Starting validation of file: {file_path}")
        
        try:
            # Parse the data file
            data = self._parse_file(file_path)
            logger.debug(f"Parsed {len(data)} records from {file_path}")
            
            # Load validation rules
            rules = self._load_rules(rule_source)
            logger.debug(f"Loaded {len(rules)} validation rules")
            
            # Execute validation
            report = self._execute_validation(data, rules)
            logger.info(f"Validation completed: {report.passed_validations} passed, {report.failed_validations} failed")
            
            # Generate reports
            self._generate_reports(report, file_path)
            
            return report
            
        except (DataParsingError, UnsupportedFormatError) as e:
            raise DataSourceError(f"Failed to parse data file: {e}", source_path=file_path)
        except DataSourceError:
            # Re-raise DataSourceError as-is
            raise
        except RuleLoadingError as e:
            raise ValidationExecutionError(f"Failed to load validation rules: {e}", stage="rule_loading")
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            raise ValidationExecutionError(f"Validation failed: {e}", stage="execution")
    
    def validate_data(
        self, 
        data: List[Dict[str, Any]],
        rule_source: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate data directly without file parsing.
        
        Args:
            data: List of data records to validate
            rule_source: Optional override for rule source
            
        Returns:
            ValidationReport with validation results
            
        Raises:
            ValidationExecutionError: If validation fails
        """
        logger.info(f"Starting validation of {len(data)} data records")
        
        try:
            # Validate input data
            if not data:
                raise ValidationExecutionError("Cannot validate empty dataset", stage="input_validation")
            
            if not isinstance(data, list):
                raise ValidationExecutionError("Data must be a list of records", stage="input_validation")
            
            # Load validation rules
            rules = self._load_rules(rule_source)
            logger.debug(f"Loaded {len(rules)} validation rules")
            
            # Execute validation
            report = self._execute_validation(data, rules)
            logger.info(f"Validation completed: {report.passed_validations} passed, {report.failed_validations} failed")
            
            # Generate reports
            self._generate_reports(report)
            
            return report
            
        except ValidationExecutionError:
            # Re-raise ValidationExecutionError as-is to preserve stage information
            raise
        except RuleLoadingError as e:
            raise ValidationExecutionError(f"Failed to load validation rules: {e}", stage="rule_loading")
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            raise ValidationExecutionError(f"Validation failed: {e}", stage="execution")
    
    def validate_record(
        self, 
        record: Dict[str, Any],
        rule_source: Optional[str] = None
    ) -> List[ValidationResult]:
        """
        Validate a single data record.
        
        Args:
            record: Data record to validate
            rule_source: Optional override for rule source
            
        Returns:
            List of ValidationResult objects for the record
            
        Raises:
            ValidationExecutionError: If validation fails
        """
        logger.debug("Starting validation of single record")
        
        try:
            # Validate input
            if not isinstance(record, dict):
                raise ValidationExecutionError("Record must be a dictionary", stage="input_validation")
            
            # Load validation rules
            rules = self._load_rules(rule_source)
            
            # Create validator and validate record
            validator = DataValidator(rules)
            results = validator.validate_record(record, 0)
            
            logger.debug(f"Record validation completed with {len(results)} results")
            return results
            
        except RuleLoadingError as e:
            raise ValidationExecutionError(f"Failed to load validation rules: {e}", stage="rule_loading")
        except Exception as e:
            logger.error(f"Unexpected error during record validation: {e}")
            raise ValidationExecutionError(f"Record validation failed: {e}", stage="execution")
    
    def check_severity_threshold(self, report: ValidationReport) -> bool:
        """
        Check if validation results meet the configured severity threshold.
        
        Args:
            report: ValidationReport to check
            
        Returns:
            True if results meet threshold (validation passed), False otherwise
        """
        severity_order = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 1,
            ValidationSeverity.ERROR: 2,
            ValidationSeverity.CRITICAL: 3
        }
        
        threshold_level = severity_order[self.config.severity_threshold]
        
        # Check if any failed results exceed the threshold
        for result in report.results:
            if not result.passed and severity_order[result.severity] >= threshold_level:
                return False
        
        return True
    
    def get_failed_results(self, report: ValidationReport) -> List[ValidationResult]:
        """
        Get only the failed validation results from a report.
        
        Args:
            report: ValidationReport to filter
            
        Returns:
            List of failed ValidationResult objects
        """
        return [result for result in report.results if not result.passed]
    
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
    
    def _parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse data file using appropriate parser.
        
        Args:
            file_path: Path to file to parse
            
        Returns:
            List of parsed data records
            
        Raises:
            DataSourceError: If file cannot be parsed
        """
        if not os.path.exists(file_path):
            raise DataSourceError(f"File not found: {file_path}", source_path=file_path)
        
        try:
            parser = self._parser_factory.create_parser(file_path)
            return parser.parse(file_path)
        except Exception as e:
            raise DataSourceError(f"Failed to parse file: {e}", source_path=file_path)
    
    def _load_rules(self, rule_source: Optional[str] = None):
        """
        Load validation rules from configured or specified source.
        
        Args:
            rule_source: Optional override for rule source
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If rules cannot be loaded
        """
        source = rule_source or self.config.rule_source.source
        
        return self._rule_manager.load_rules(
            source=source,
            loader_type=self.config.rule_source.source_type,
            fallback_sources=self.config.rule_source.fallback_sources,
            use_cache=self.config.rule_source.use_cache
        )
    
    def _execute_validation(self, data: List[Dict[str, Any]], rules) -> ValidationReport:
        """
        Execute validation rules against data.
        
        Args:
            data: Data records to validate
            rules: Validation rules to apply
            
        Returns:
            ValidationReport with results
        """
        validator = DataValidator(rules)
        
        if self.config.fail_fast:
            # Implement fail-fast validation
            return self._execute_fail_fast_validation(validator, data)
        else:
            # Standard validation
            return validator.validate(data)
    
    def _execute_fail_fast_validation(self, validator: DataValidator, data: List[Dict[str, Any]]) -> ValidationReport:
        """
        Execute validation with fail-fast behavior.
        
        Args:
            validator: DataValidator instance
            data: Data to validate
            
        Returns:
            ValidationReport (may be incomplete if failed fast)
        """
        # For fail-fast, we validate record by record and stop on first critical error
        all_results = []
        
        for index, record in enumerate(data):
            record_results = validator.validate_record(record, index)
            all_results.extend(record_results)
            
            # Check for critical failures
            for result in record_results:
                if (not result.passed and 
                    result.severity == ValidationSeverity.CRITICAL):
                    logger.warning(f"Fail-fast triggered at record {index + 1}")
                    break
            else:
                continue
            break
        
        # Generate report from collected results
        return validator._generate_report(data[:len([r for r in all_results if r.row_index is not None]) + 1], all_results)
    
    def _generate_reports(self, report: ValidationReport, source_file: Optional[str] = None) -> None:
        """
        Generate all configured report formats.
        
        Args:
            report: ValidationReport to generate reports from
            source_file: Optional source file path for report metadata
        """
        try:
            # Get rules source information
            rules_source = self.config.rule_source.source
            
            # Console report
            if self.config.output.generate_console_report:
                console_reporter = ConsoleReporter(use_colors=self.config.output.console_colors)
                console_reporter.generate_report(report)
            
            # File-based reports
            if self.config.output.output_directory:
                output_dir = Path(self.config.output.output_directory)
                
                # JSON report
                if self.config.output.generate_json_report:
                    json_reporter = JSONReporter()
                    json_path = output_dir / "validation_report.json"
                    json_reporter.generate_report(report, str(json_path), source_file, rules_source)
                
                # Markdown report
                if self.config.output.generate_markdown_report:
                    markdown_reporter = MarkdownReporter()
                    md_path = output_dir / "validation_report.md"
                    markdown_reporter.generate_report(report, str(md_path), source_file, rules_source)
                
                logger.info(f"Reports generated in: {output_dir}")
            
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate reports: {e}")
    
    def _create_rule_manager(self):
        """
        Create appropriate rule manager based on configuration.
        
        Returns:
            RuleLoadingManager instance
        """
        # Check if MCP configuration is provided in rule source or global config
        mcp_config = self.config.rule_source.mcp_config or self.config.mcp_config
        
        if mcp_config or self.config.rule_source.source_type == 'mcp':
            if not mcp_config:
                # If source_type is mcp but no config provided, create default config
                mcp_config = {
                    "command": "python",
                    "args": ["mcp_validation_server.py"],
                    "timeout": 30
                }
            return MCPRuleLoadingManager(mcp_config=mcp_config)
        else:
            return RuleLoadingManager()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level.upper())
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config.log_file
        )
        
        # Set library logger level
        library_logger = logging.getLogger('policy_dq')
        library_logger.setLevel(log_level)


# Convenience functions for common use cases

def validate_file(
    file_path: str,
    rule_source: str,
    output_dir: Optional[str] = None,
    **config_kwargs
) -> ValidationReport:
    """
    Convenience function to validate a file with minimal configuration.
    
    Args:
        file_path: Path to data file to validate
        rule_source: Path to rule source file or MCP identifier
        output_dir: Optional output directory for reports
        **config_kwargs: Additional configuration options
        
    Returns:
        ValidationReport with validation results
    """
    from .config import create_default_config
    
    config = create_default_config(rule_source, output_dir)
    
    # Apply any additional configuration
    for key, value in config_kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    engine = ValidationEngine(config)
    return engine.validate_file(file_path)


def validate_data(
    data: List[Dict[str, Any]],
    rule_source: str,
    output_dir: Optional[str] = None,
    **config_kwargs
) -> ValidationReport:
    """
    Convenience function to validate data with minimal configuration.
    
    Args:
        data: List of data records to validate
        rule_source: Path to rule source file or MCP identifier
        output_dir: Optional output directory for reports
        **config_kwargs: Additional configuration options
        
    Returns:
        ValidationReport with validation results
    """
    from .config import create_default_config
    
    config = create_default_config(rule_source, output_dir)
    
    # Apply any additional configuration
    for key, value in config_kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    engine = ValidationEngine(config)
    return engine.validate_data(data)


def quick_validate(
    file_path: str,
    rule_source: str
) -> bool:
    """
    Quick validation that returns True/False based on validation success.
    
    Args:
        file_path: Path to data file to validate
        rule_source: Path to rule source file or MCP identifier
        
    Returns:
        True if validation passed, False if failed
    """
    try:
        report = validate_file(file_path, rule_source)
        return report.failed_validations == 0
    except Exception:
        return False