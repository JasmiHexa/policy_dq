"""
MCP (Model Context Protocol) client for connecting to MCP servers.

This module provides the MCPClient class for establishing connections
to MCP servers and fetching validation rules.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import json

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    # Fallback for testing or when MCP is not available
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None

from ..rules.base import RuleLoadingError


logger = logging.getLogger(__name__)


class MCPConnectionError(RuleLoadingError):
    """Exception raised when MCP connection fails."""
    pass


class MCPClient:
    """
    Client for connecting to MCP servers and fetching validation rules.
    
    This client handles async connection management, authentication,
    and error handling for MCP server interactions.
    """
    
    def __init__(self, server_config: Dict[str, Any]):
        """
        Initialize MCP client with server configuration.
        
        Args:
            server_config: Configuration dictionary containing:
                - command: Command to start the MCP server
                - args: Arguments for the server command
                - env: Environment variables (optional)
                - timeout: Connection timeout in seconds (optional)
        """
        self.config = server_config
        self.session: Optional[ClientSession] = None
        self.connected = False
        
        # Validate required configuration
        if not server_config.get('command'):
            raise ValueError("MCP server configuration must include 'command'")
        
        self.command = server_config['command']
        self.args = server_config.get('args', [])
        self.env = server_config.get('env', {})
        self.timeout = server_config.get('timeout', 30)
        
        logger.debug(f"Initialized MCP client with command: {self.command}")
    
    async def connect(self) -> None:
        """
        Establish connection to the MCP server.
        
        Raises:
            MCPConnectionError: If connection cannot be established
        """
        if ClientSession is None:
            raise MCPConnectionError("MCP library not available")
        
        try:
            logger.info(f"Connecting to MCP server: {self.command}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env
            )
            
            # Establish connection with timeout
            try:
                async with asyncio.timeout(self.timeout):
                    # Store the context manager for later cleanup
                    self._client_context = stdio_client(server_params)
                    # Enter the context manager
                    read_stream, write_stream = await self._client_context.__aenter__()
                    
                    # Create session with the streams
                    self.session = ClientSession(read_stream, write_stream)
                    await self.session.initialize()
                    
                self.connected = True
                logger.info("Successfully connected to MCP server")
                
            except asyncio.TimeoutError:
                raise MCPConnectionError(f"Connection timeout after {self.timeout} seconds")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPConnectionError(f"Connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.session and self.connected:
            try:
                await self.session.close()
                # Also close the client context if it exists
                if hasattr(self, '_client_context'):
                    await self._client_context.__aexit__(None, None, None)
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.session = None
                self.connected = False
                if hasattr(self, '_client_context'):
                    delattr(self, '_client_context')
    
    async def fetch_rules(self, rule_set_id: str) -> List[Dict[str, Any]]:
        """
        Fetch validation rules from the MCP server.
        
        Args:
            rule_set_id: Identifier for the rule set to fetch
            
        Returns:
            List of rule dictionaries
            
        Raises:
            MCPConnectionError: If not connected or fetch fails
        """
        if not self.connected or not self.session:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            logger.debug(f"Fetching rules for rule set: {rule_set_id}")
            
            # Call the MCP server to get rules
            # This assumes the MCP server has a "get_validation_rules" tool
            result = await self.session.call_tool(
                "get_validation_rules",
                arguments={"rule_set_id": rule_set_id}
            )
            
            if not result.content:
                logger.warning("Empty response from MCP server")
                return []
            
            # Parse the response
            rules_data = []
            for content in result.content:
                if hasattr(content, 'text'):
                    try:
                        data = json.loads(content.text)
                        if isinstance(data, list):
                            rules_data.extend(data)
                        elif isinstance(data, dict):
                            rules_data.append(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse MCP response as JSON: {e}")
                        raise MCPConnectionError(f"Failed to parse JSON response: {e}")
            
            logger.info(f"Successfully fetched {len(rules_data)} rules from MCP server")
            return rules_data
            
        except Exception as e:
            logger.error(f"Failed to fetch rules from MCP server: {e}")
            raise MCPConnectionError(f"Failed to fetch rules: {e}")
    
    async def list_available_tools(self) -> List[str]:
        """
        List available tools on the MCP server.
        
        Returns:
            List of available tool names
            
        Raises:
            MCPConnectionError: If not connected or listing fails
        """
        if not self.connected or not self.session:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            tools = await self.session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            logger.debug(f"Available MCP tools: {tool_names}")
            return tool_names
            
        except Exception as e:
            logger.error(f"Failed to list MCP tools: {e}")
            raise MCPConnectionError(f"Failed to list tools: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()