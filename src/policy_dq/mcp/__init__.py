"""
Model Context Protocol integration.

This package provides MCP client functionality and rule loading
capabilities for integrating with MCP servers.
"""

from .client import MCPClient, MCPConnectionError
from .rule_loader import MCPRuleLoader, MCPRuleLoaderFactory

__all__ = [
    'MCPClient',
    'MCPConnectionError', 
    'MCPRuleLoader',
    'MCPRuleLoaderFactory'
]