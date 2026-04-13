"""
Unit tests for MCP client functionality.

These tests verify the MCP client behavior with mocked dependencies
to ensure proper error handling and protocol compliance.
"""

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.policy_dq.mcp.client import MCPClient, MCPConnectionError


def create_mock_stdio_client(mock_session):
    """Helper to create properly mocked stdio_client."""
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=(mock_session, mock_session))
    mock_context.__aexit__ = AsyncMock(return_value=None)
    return mock_context


class TestMCPClient:
    """Unit tests for MCPClient class."""
    
    @pytest.fixture
    def valid_config(self):
        """Provide valid MCP client configuration."""
        return {
            "command": "python",
            "args": ["test_server.py"],
            "env": {"TEST_ENV": "true"},
            "timeout": 30
        }
    
    def test_client_initialization_valid_config(self, valid_config):
        """Test client initialization with valid configuration."""
        client = MCPClient(valid_config)
        
        assert client.command == "python"
        assert client.args == ["test_server.py"]
        assert client.env == {"TEST_ENV": "true"}
        assert client.timeout == 30
        assert not client.connected
        assert client.session is None
    
    def test_client_initialization_minimal_config(self):
        """Test client initialization with minimal configuration."""
        config = {"command": "test_command"}
        client = MCPClient(config)
        
        assert client.command == "test_command"
        assert client.args == []
        assert client.env == {}
        assert client.timeout == 30
    
    def test_client_initialization_invalid_config(self):
        """Test client initialization with invalid configuration."""
        # Missing command
        with pytest.raises(ValueError, match="MCP server configuration must include 'command'"):
            MCPClient({})
        
        # Empty command
        with pytest.raises(ValueError, match="MCP server configuration must include 'command'"):
            MCPClient({"command": ""})
    
    @pytest.mark.asyncio
    async def test_connect_success(self, valid_config):
        """Test successful connection to MCP server."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters') as mock_params_class:
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    mock_params = MagicMock()
                    mock_params_class.return_value = mock_params
                    
                    client = MCPClient(valid_config)
                    
                    # Test connection
                    await client.connect()
                    
                    # Verify connection was established
                    assert client.connected is True
                    mock_stdio_client.assert_called_once()
                    mock_session.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_timeout(self, valid_config):
        """Test connection timeout."""
        with patch('src.policy_dq.mcp.client.ClientSession'):
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Mock timeout
                    mock_stdio_client.side_effect = asyncio.TimeoutError()
                    
                    client = MCPClient(valid_config)
                    
                    with pytest.raises(MCPConnectionError, match="Connection timeout"):
                        await client.connect()
    
    @pytest.mark.asyncio
    async def test_connect_general_error(self, valid_config):
        """Test connection with general error."""
        with patch('src.policy_dq.mcp.client.ClientSession'):
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Mock general error
                    mock_stdio_client.side_effect = RuntimeError("Connection failed")
                    
                    client = MCPClient(valid_config)
                    
                    with pytest.raises(MCPConnectionError, match="Connection failed"):
                        await client.connect()
    
    @pytest.mark.asyncio
    async def test_connect_mcp_not_available(self, valid_config):
        """Test connection when MCP library is not available."""
        with patch('src.policy_dq.mcp.client.ClientSession', None):
            client = MCPClient(valid_config)
            
            with pytest.raises(MCPConnectionError, match="MCP library not available"):
                await client.connect()
    
    @pytest.mark.asyncio
    async def test_disconnect_success(self, valid_config):
        """Test successful disconnection."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test disconnection
                    await client.disconnect()
                    
                    # Verify disconnection
                    assert client.connected is False
                    mock_session.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_with_error(self, valid_config):
        """Test disconnection with error (should not raise)."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session.close.side_effect = RuntimeError("Close failed")
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test disconnection (should not raise)
                    await client.disconnect()
                    
                    # Should still be marked as disconnected
                    assert client.connected is False
    
    @pytest.mark.asyncio
    async def test_fetch_rules_success(self, valid_config):
        """Test successful rule fetching."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    # Mock tool call response
                    mock_content = MagicMock()
                    mock_content.text = json.dumps([
                        {"name": "rule1", "type": "regex_check", "field": "email"},
                        {"name": "rule2", "type": "required_field", "field": "name"}
                    ])
                    mock_result = MagicMock()
                    mock_result.content = [mock_content]
                    mock_session.call_tool.return_value = mock_result
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test rule fetching
                    rules = await client.fetch_rules("test_tool")
                    
                    assert len(rules) == 2
                    assert rules[0]["name"] == "rule1"
                    assert rules[1]["name"] == "rule2"
    
    @pytest.mark.asyncio
    async def test_fetch_rules_not_connected(self, valid_config):
        """Test rule fetching when not connected."""
        client = MCPClient(valid_config)
        
        with pytest.raises(MCPConnectionError, match="Not connected to MCP server"):
            await client.fetch_rules("test_tool")
    
    @pytest.mark.asyncio
    async def test_fetch_rules_empty_response(self, valid_config):
        """Test rule fetching with empty response."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    # Mock empty response
                    mock_result = MagicMock()
                    mock_result.content = []
                    mock_session.call_tool.return_value = mock_result
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test rule fetching
                    rules = await client.fetch_rules("test_tool")
                    
                    assert rules == []
    
    @pytest.mark.asyncio
    async def test_fetch_rules_invalid_json(self, valid_config):
        """Test rule fetching with invalid JSON response."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    # Mock invalid JSON response
                    mock_content = MagicMock()
                    mock_content.text = "invalid json {"
                    mock_result = MagicMock()
                    mock_result.content = [mock_content]
                    mock_session.call_tool.return_value = mock_result
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test rule fetching
                    with pytest.raises(MCPConnectionError, match="Failed to parse JSON response"):
                        await client.fetch_rules("test_tool")
    
    @pytest.mark.asyncio
    async def test_list_available_tools_success(self, valid_config):
        """Test listing available tools."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    # Mock tools response
                    mock_tool1 = MagicMock()
                    mock_tool1.name = "get_validation_rules"
                    mock_tool2 = MagicMock()
                    mock_tool2.name = "generate_custom_rules"
                    
                    mock_tools_result = MagicMock()
                    mock_tools_result.tools = [mock_tool1, mock_tool2]
                    mock_session.list_tools.return_value = mock_tools_result
                    
                    client = MCPClient(valid_config)
                    await client.connect()
                    
                    # Test tool listing
                    tools = await client.list_available_tools()
                    
                    assert len(tools) == 2
                    assert "get_validation_rules" in tools
                    assert "generate_custom_rules" in tools
    
    @pytest.mark.asyncio
    async def test_list_available_tools_not_connected(self, valid_config):
        """Test listing tools when not connected."""
        client = MCPClient(valid_config)
        
        with pytest.raises(MCPConnectionError, match="Not connected to MCP server"):
            await client.list_available_tools()
    
    @pytest.mark.asyncio
    async def test_context_manager(self, valid_config):
        """Test using client as async context manager."""
        with patch('src.policy_dq.mcp.client.ClientSession') as mock_session_class:
            with patch('src.policy_dq.mcp.client.stdio_client') as mock_stdio_client:
                with patch('src.policy_dq.mcp.client.StdioServerParameters'):
                    # Setup mocks
                    mock_session = AsyncMock()
                    mock_session_class.return_value = mock_session
                    mock_stdio_client.return_value = create_mock_stdio_client(mock_session)
                    
                    client = MCPClient(valid_config)
                    
                    # Test context manager
                    async with client as ctx_client:
                        assert ctx_client is client
                        assert client.connected is True
                    
                    # Should be disconnected after context
                    assert client.connected is False