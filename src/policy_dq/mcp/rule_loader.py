"""
MCP-based rule loader for loading validation rules from MCP servers.

This module provides the MCPRuleLoader class that implements the RuleLoader
interface for loading rules from Model Context Protocol servers.
"""

import asyncio
import logging
from typing import Any, Dict, List
import json

from ..rules.base import RuleLoader, RuleLoadingError
from ..models import ValidationRule, ValidationSeverity, RuleType
from .client import MCPClient, MCPConnectionError


logger = logging.getLogger(__name__)


class MCPRuleLoader(RuleLoader):
    """
    Rule loader that fetches validation rules from MCP servers.
    
    This loader connects to MCP servers to retrieve rule configurations
    and converts them into ValidationRule objects.
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize MCP rule loader with server configuration.
        
        Args:
            server_config: MCP server configuration dictionary
        """
        self.server_config = server_config
        self.client = MCPClient(server_config)
        logger.debug("Initialized MCP rule loader")
    
    def load_rules(self, source: str) -> List[ValidationRule]:
        """
        Load validation rules from MCP server.
        
        Args:
            source: Rule set identifier on the MCP server
            
        Returns:
            List of ValidationRule objects
            
        Raises:
            RuleLoadingError: If rules cannot be loaded or parsed
        """
        try:
            # Run the async operation in a new event loop
            return asyncio.run(self._load_rules_async(source))
        except Exception as e:
            logger.error(f"Failed to load rules from MCP server: {e}")
            raise RuleLoadingError(f"MCP rule loading failed: {e}")
    
    async def _load_rules_async(self, source: str) -> List[ValidationRule]:
        """
        Async implementation of rule loading.
        
        Args:
            source: Rule set identifier on the MCP server
            
        Returns:
            List of ValidationRule objects
        """
        async with self.client:
            # Fetch raw rule data from MCP server
            rules_data = await self.client.fetch_rules(source)
            
            # Convert raw data to ValidationRule objects
            validation_rules = []
            for rule_data in rules_data:
                try:
                    rule = self._parse_rule_data(rule_data)
                    validation_rules.append(rule)
                except Exception as e:
                    logger.warning(f"Failed to parse rule data: {rule_data}, error: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(validation_rules)} rules from MCP server")
            return validation_rules
    
    def _parse_rule_data(self, rule_data: Dict[str, Any]) -> ValidationRule:
        """
        Parse raw rule data into a ValidationRule object.
        
        Args:
            rule_data: Raw rule data from MCP server
            
        Returns:
            ValidationRule object
            
        Raises:
            ValueError: If rule data is invalid
        """
        # Validate required fields
        required_fields = ['name', 'type', 'field']
        for field in required_fields:
            if field not in rule_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse rule type
        try:
            rule_type = RuleType(rule_data['type'])
        except ValueError:
            raise ValueError(f"Invalid rule type: {rule_data['type']}")
        
        # Parse severity (with default)
        severity_str = rule_data.get('severity', 'error')
        try:
            severity = ValidationSeverity(severity_str)
        except ValueError:
            logger.warning(f"Invalid severity '{severity_str}', using ERROR")
            severity = ValidationSeverity.ERROR
        
        # Extract parameters
        parameters = rule_data.get('parameters', {})
        
        return ValidationRule(
            name=rule_data['name'],
            rule_type=rule_type,
            field=rule_data['field'],
            parameters=parameters,
            severity=severity
        )
    
    def validate_source(self, source: str) -> bool:
        """
        Validate that the MCP server is accessible and the rule set exists.
        
        Args:
            source: Rule set identifier to validate
            
        Returns:
            True if source is valid and accessible, False otherwise
        """
        try:
            return asyncio.run(self._validate_source_async(source))
        except Exception as e:
            logger.debug(f"Source validation failed: {e}")
            return False
    
    async def _validate_source_async(self, source: str) -> bool:
        """
        Async implementation of source validation.
        
        Args:
            source: Rule set identifier to validate
            
        Returns:
            True if source is valid and accessible, False otherwise
        """
        try:
            async with self.client:
                # Try to fetch a small amount of data to validate connectivity
                await self.client.list_available_tools()
                
                # Optionally, try to fetch the actual rules to validate the source
                try:
                    rules_data = await self.client.fetch_rules(source)
                    return len(rules_data) >= 0  # Even empty rule sets are valid
                except MCPConnectionError:
                    # If we can connect but can't fetch rules, the source might not exist
                    return False
                
        except Exception:
            return False


class MCPRuleLoaderFactory:
    """
    Factory for creating MCP rule loaders with different configurations.
    """
    
    @staticmethod
    def create_loader(server_config: Dict[str, Any]) -> MCPRuleLoader:
        """
        Create an MCP rule loader with the given configuration.
        
        Args:
            server_config: MCP server configuration
            
        Returns:
            MCPRuleLoader instance
        """
        return MCPRuleLoader(server_config)
    
    @staticmethod
    def create_from_config_file(config_path: str) -> MCPRuleLoader:
        """
        Create an MCP rule loader from a configuration file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            MCPRuleLoader instance
            
        Raises:
            RuleLoadingError: If configuration cannot be loaded
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return MCPRuleLoader(config)
        except Exception as e:
            raise RuleLoadingError(f"Failed to load MCP configuration: {e}")