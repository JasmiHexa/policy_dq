"""
Configuration management for the validation API.

This module provides configuration classes and utilities for managing
validation engine settings, rule sources, and output options.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import os

from .exceptions import ConfigurationError
from .models import ValidationSeverity


@dataclass
class RuleSourceConfig:
    """Configuration for a validation rule source."""
    
    source: str
    source_type: str = 'auto'  # 'auto', 'file', or 'mcp'
    fallback_sources: Optional[List[Dict[str, str]]] = None
    use_cache: bool = True
    mcp_config: Optional[Dict[str, Any]] = None  # MCP server configuration
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.source:
            raise ConfigurationError("Rule source cannot be empty")
        
        if self.fallback_sources is None:
            self.fallback_sources = []
        
        # Validate MCP configuration if source_type is mcp
        if self.source_type == 'mcp' and not self.mcp_config:
            raise ConfigurationError(
                "MCP configuration is required when source_type is 'mcp'",
                config_key="mcp_config"
            )


@dataclass
class OutputConfig:
    """Configuration for validation output and reporting."""
    
    output_directory: Optional[str] = None
    generate_console_report: bool = True
    generate_json_report: bool = True
    generate_markdown_report: bool = True
    console_colors: bool = True
    include_passed_results: bool = False
    
    def __post_init__(self):
        """Validate and normalize output configuration."""
        if self.output_directory:
            # Ensure output directory exists
            output_path = Path(self.output_directory)
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise ConfigurationError(
                    f"Cannot create output directory: {self.output_directory}",
                    config_key="output_directory",
                    details={"error": str(e)}
                )


@dataclass
class ValidationConfig:
    """
    Comprehensive configuration for the validation engine.
    
    This class encapsulates all configuration options for validation
    including rule sources, output settings, and execution parameters.
    """
    
    # Rule configuration
    rule_source: RuleSourceConfig
    
    # Output configuration
    output: OutputConfig = field(default_factory=OutputConfig)
    
    # Validation behavior
    fail_fast: bool = False
    severity_threshold: ValidationSeverity = ValidationSeverity.ERROR
    max_errors_per_rule: Optional[int] = None
    
    # Performance settings
    batch_size: Optional[int] = None
    parallel_processing: bool = False
    
    # MCP configuration
    mcp_config: Optional[Dict[str, Any]] = None
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ValidationConfig':
        """
        Create ValidationConfig from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            ValidationConfig instance
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Extract rule source configuration
            rule_source_data = config_dict.get('rule_source', {})
            if isinstance(rule_source_data, str):
                # Simple string source
                rule_source = RuleSourceConfig(source=rule_source_data)
            else:
                rule_source = RuleSourceConfig(**rule_source_data)
            
            # Extract output configuration
            output_data = config_dict.get('output', {})
            output = OutputConfig(**output_data)
            
            # Extract other configuration
            other_config = {
                key: value for key, value in config_dict.items()
                if key not in ['rule_source', 'output']
            }
            
            # Handle severity threshold conversion
            if 'severity_threshold' in other_config:
                threshold_value = other_config['severity_threshold']
                if isinstance(threshold_value, str):
                    try:
                        other_config['severity_threshold'] = ValidationSeverity(threshold_value.lower())
                    except ValueError:
                        raise ConfigurationError(
                            f"Invalid severity threshold: {threshold_value}",
                            config_key="severity_threshold"
                        )
            
            return cls(
                rule_source=rule_source,
                output=output,
                **other_config
            )
            
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration format: {e}")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ValidationConfig':
        """
        Load configuration from file.
        
        Args:
            config_path: Path to configuration file (JSON or YAML)
            
        Returns:
            ValidationConfig instance
            
        Raises:
            ConfigurationError: If file cannot be loaded or is invalid
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path}",
                config_key="config_file"
            )
        
        try:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                import yaml
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = yaml.safe_load(f)
            elif config_file.suffix.lower() == '.json':
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_dict = json.load(f)
            else:
                raise ConfigurationError(
                    f"Unsupported configuration file format: {config_file.suffix}",
                    config_key="config_file"
                )
            
            return cls.from_dict(config_dict)
            
        except Exception as e:
            # Handle YAML and JSON parsing errors
            if 'yaml' in str(type(e)).lower() or 'json' in str(type(e)).lower():
                raise ConfigurationError(
                    f"Failed to parse configuration file: {e}",
                    config_key="config_file"
                )
            else:
                raise ConfigurationError(
                    f"Error loading configuration file: {e}",
                    config_key="config_file"
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            'rule_source': {
                'source': self.rule_source.source,
                'source_type': self.rule_source.source_type,
                'fallback_sources': self.rule_source.fallback_sources,
                'use_cache': self.rule_source.use_cache,
                'mcp_config': self.rule_source.mcp_config
            },
            'output': {
                'output_directory': self.output.output_directory,
                'generate_console_report': self.output.generate_console_report,
                'generate_json_report': self.output.generate_json_report,
                'generate_markdown_report': self.output.generate_markdown_report,
                'console_colors': self.output.console_colors,
                'include_passed_results': self.output.include_passed_results
            },
            'fail_fast': self.fail_fast,
            'severity_threshold': self.severity_threshold.value,
            'max_errors_per_rule': self.max_errors_per_rule,
            'batch_size': self.batch_size,
            'parallel_processing': self.parallel_processing,
            'mcp_config': self.mcp_config,
            'log_level': self.log_level,
            'log_file': self.log_file
        }
    
    def validate(self) -> None:
        """
        Validate the configuration for consistency and completeness.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate rule source
        if not self.rule_source.source:
            raise ConfigurationError("Rule source must be specified")
        
        # Validate severity threshold
        if not isinstance(self.severity_threshold, ValidationSeverity):
            raise ConfigurationError("Invalid severity threshold")
        
        # Validate batch size
        if self.batch_size is not None and self.batch_size <= 0:
            raise ConfigurationError(
                "Batch size must be positive",
                config_key="batch_size"
            )
        
        # Validate max errors per rule
        if self.max_errors_per_rule is not None and self.max_errors_per_rule <= 0:
            raise ConfigurationError(
                "Max errors per rule must be positive",
                config_key="max_errors_per_rule"
            )
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level: {self.log_level}. Must be one of: {valid_log_levels}",
                config_key="log_level"
            )


def create_default_config(rule_source: str, output_dir: Optional[str] = None) -> ValidationConfig:
    """
    Create a default configuration with minimal required settings.
    
    Args:
        rule_source: Path to rule source file or MCP identifier
        output_dir: Optional output directory for reports
        
    Returns:
        ValidationConfig with default settings
    """
    rule_config = RuleSourceConfig(source=rule_source)
    output_config = OutputConfig(output_directory=output_dir)
    
    return ValidationConfig(
        rule_source=rule_config,
        output=output_config
    )


def create_config_from_env() -> ValidationConfig:
    """
    Create configuration from environment variables.
    
    Environment variables:
    - POLICY_DQ_RULE_SOURCE: Rule source path or identifier
    - POLICY_DQ_OUTPUT_DIR: Output directory for reports
    - POLICY_DQ_SEVERITY_THRESHOLD: Minimum severity threshold
    - POLICY_DQ_FAIL_FAST: Enable fail-fast mode (true/false)
    - POLICY_DQ_LOG_LEVEL: Logging level
    
    Returns:
        ValidationConfig created from environment variables
        
    Raises:
        ConfigurationError: If required environment variables are missing
    """
    rule_source = os.getenv('POLICY_DQ_RULE_SOURCE')
    if not rule_source:
        raise ConfigurationError(
            "POLICY_DQ_RULE_SOURCE environment variable is required",
            config_key="POLICY_DQ_RULE_SOURCE"
        )
    
    config_dict = {
        'rule_source': {'source': rule_source},
        'output': {
            'output_directory': os.getenv('POLICY_DQ_OUTPUT_DIR')
        },
        'fail_fast': os.getenv('POLICY_DQ_FAIL_FAST', 'false').lower() == 'true',
        'log_level': os.getenv('POLICY_DQ_LOG_LEVEL', 'INFO')
    }
    
    # Handle severity threshold
    severity_threshold = os.getenv('POLICY_DQ_SEVERITY_THRESHOLD')
    if severity_threshold:
        config_dict['severity_threshold'] = severity_threshold
    
    return ValidationConfig.from_dict(config_dict)