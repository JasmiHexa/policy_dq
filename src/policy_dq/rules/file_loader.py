"""
File-based rule loader implementation.

This module provides a rule loader that can read validation rules
from YAML and JSON files with schema validation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None

from .base import RuleLoader, RuleLoadingError
from ..models import ValidationRule, ValidationSeverity, RuleType


class FileRuleLoader(RuleLoader):
    """
    Rule loader that reads validation rules from YAML or JSON files.
    
    Supports both YAML and JSON formats with schema validation to ensure
    rule configurations are properly structured.
    """
    
    # Schema for validating rule configuration files
    RULE_SCHEMA = {
        "type": "object",
        "required": ["version", "rule_sets"],
        "properties": {
            "version": {"type": "string"},
            "rule_sets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "rules"],
                    "properties": {
                        "name": {"type": "string"},
                        "rules": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "type", "field"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "type": {
                                        "type": "string",
                                        "enum": [
                                            "required_field",
                                            "type_check", 
                                            "regex_check",
                                            "numeric_range",
                                            "uniqueness",
                                            "cross_field"
                                        ]
                                    },
                                    "field": {"type": "string"},
                                    "parameters": {"type": "object"},
                                    "severity": {
                                        "type": "string",
                                        "enum": ["info", "warning", "error", "critical"]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize the file rule loader."""
        self._cache: Dict[str, List[ValidationRule]] = {}
    
    def load_rules(self, source: str) -> List[ValidationRule]:
        """
        Load validation rules from a YAML or JSON file.
        
        Args:
            source: Path to the rule configuration file
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If file cannot be read or parsed
        """
        if not self.validate_source(source):
            raise RuleLoadingError(f"Invalid or inaccessible source: {source}")
        
        # Check cache first
        if source in self._cache:
            return self._cache[source]
        
        try:
            # Read and parse the file
            file_path = Path(source)
            content = file_path.read_text(encoding='utf-8')
            
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                if yaml is None:
                    raise RuleLoadingError("PyYAML is required for YAML file support")
                data = yaml.safe_load(content)
            elif file_path.suffix.lower() == '.json':
                data = json.loads(content)
            else:
                raise RuleLoadingError(f"Unsupported file format: {file_path.suffix}")
            
            # Validate schema
            self._validate_schema(data, source)
            
            # Convert to ValidationRule objects
            rules = self._parse_rules(data)
            
            # Cache the results
            self._cache[source] = rules
            
            return rules
            
        except (OSError, IOError) as e:
            raise RuleLoadingError(f"Failed to read file {source}: {e}")
        except json.JSONDecodeError as e:
            raise RuleLoadingError(f"Failed to parse file {source}: {e}")
        except Exception as e:
            # Handle YAML errors if PyYAML is available
            if yaml is not None and hasattr(yaml, 'YAMLError') and isinstance(e, yaml.YAMLError):
                raise RuleLoadingError(f"Failed to parse file {source}: {e}")
            raise RuleLoadingError(f"Unexpected error loading rules from {source}: {e}")
    
    def validate_source(self, source: str) -> bool:
        """
        Validate that the source file exists and has a supported extension.
        
        Args:
            source: Path to the rule configuration file
            
        Returns:
            True if source is valid, False otherwise
        """
        try:
            file_path = Path(source)
            
            # Check if file exists and is readable
            if not file_path.exists() or not file_path.is_file():
                return False
            
            # Check if file has supported extension
            supported_extensions = ['.yaml', '.yml', '.json']
            if file_path.suffix.lower() not in supported_extensions:
                return False
            
            # Check if file is readable
            try:
                file_path.read_text(encoding='utf-8')
                return True
            except (OSError, IOError, UnicodeDecodeError):
                return False
                
        except Exception:
            return False
    
    def clear_cache(self) -> None:
        """Clear the internal rule cache."""
        self._cache.clear()
    
    def _validate_schema(self, data: Dict[str, Any], source: str) -> None:
        """
        Validate the loaded data against the expected schema.
        
        Args:
            data: Parsed rule configuration data
            source: Source file path for error reporting
            
        Raises:
            RuleLoadingError: If schema validation fails
        """
        # Basic schema validation (simplified version)
        if not isinstance(data, dict):
            raise RuleLoadingError(f"Rule file {source} must contain a JSON object")
        
        if "version" not in data:
            raise RuleLoadingError(f"Rule file {source} missing required 'version' field")
        
        if "rule_sets" not in data:
            raise RuleLoadingError(f"Rule file {source} missing required 'rule_sets' field")
        
        if not isinstance(data["rule_sets"], list):
            raise RuleLoadingError(f"Rule file {source} 'rule_sets' must be an array")
        
        for i, rule_set in enumerate(data["rule_sets"]):
            if not isinstance(rule_set, dict):
                raise RuleLoadingError(f"Rule file {source} rule_set {i} must be an object")
            
            if "name" not in rule_set:
                raise RuleLoadingError(f"Rule file {source} rule_set {i} missing 'name' field")
            
            if "rules" not in rule_set:
                raise RuleLoadingError(f"Rule file {source} rule_set {i} missing 'rules' field")
            
            if not isinstance(rule_set["rules"], list):
                raise RuleLoadingError(f"Rule file {source} rule_set {i} 'rules' must be an array")
            
            for j, rule in enumerate(rule_set["rules"]):
                self._validate_rule_schema(rule, source, i, j)
    
    def _validate_rule_schema(self, rule: Dict[str, Any], source: str, set_idx: int, rule_idx: int) -> None:
        """
        Validate a single rule's schema.
        
        Args:
            rule: Rule configuration dictionary
            source: Source file path for error reporting
            set_idx: Rule set index for error reporting
            rule_idx: Rule index for error reporting
            
        Raises:
            RuleLoadingError: If rule schema validation fails
        """
        rule_path = f"rule_set {set_idx}, rule {rule_idx}"
        
        if not isinstance(rule, dict):
            raise RuleLoadingError(f"Rule file {source} {rule_path} must be an object")
        
        required_fields = ["name", "type", "field"]
        for field in required_fields:
            if field not in rule:
                raise RuleLoadingError(f"Rule file {source} {rule_path} missing required '{field}' field")
        
        # Validate rule type
        valid_types = ["required_field", "type_check", "regex_check", "numeric_range", "uniqueness", "cross_field"]
        if rule["type"] not in valid_types:
            raise RuleLoadingError(f"Rule file {source} {rule_path} has invalid type '{rule['type']}'")
        
        # Validate severity if present
        if "severity" in rule:
            valid_severities = ["info", "warning", "error", "critical"]
            if rule["severity"] not in valid_severities:
                raise RuleLoadingError(f"Rule file {source} {rule_path} has invalid severity '{rule['severity']}'")
    
    def _parse_rules(self, data: Dict[str, Any]) -> List[ValidationRule]:
        """
        Parse rule configuration data into ValidationRule objects.
        
        Args:
            data: Parsed rule configuration data
            
        Returns:
            List of ValidationRule objects
        """
        rules = []
        
        for rule_set in data["rule_sets"]:
            for rule_config in rule_set["rules"]:
                rule = ValidationRule(
                    name=rule_config["name"],
                    rule_type=RuleType(rule_config["type"]),
                    field=rule_config["field"],
                    parameters=rule_config.get("parameters", {}),
                    severity=ValidationSeverity(rule_config.get("severity", "error"))
                )
                rules.append(rule)
        
        return rules