"""
Unit tests for MCP rule loader functionality.

These tests verify the MCP rule loader behavior with mocked MCP client
to ensure proper rule parsing and error handling.
"""

import pytest
from unittest.mock import patch

from src.policy_dq.mcp.rule_loader import MCPRuleLoader, MCPRuleLoaderFactory
from src.policy_dq.mcp.client import MCPConnectionError
from src.policy_dq.rules.base import RuleLoadingError
from src.policy_dq.models import ValidationRule, ValidationSeverity, RuleType


class TestMCPRuleLoader:
    """Unit tests for MCPRuleLoader class."""
    
    @pytest.fixture
    def server_config(self):
        """Sample MCP server configuration."""
        return {
            "command": "python",
            "args": ["test_server.py"],
            "timeout": 30
        }
    
    @pytest.fixture
    def sample_rules_data(self):
        """Sample rule data from MCP server."""
        return [
            {
                "name": "email_format",
                "type": "regex_check",
                "field": "email",
                "parameters": {
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "message": "Invalid email format"
                },
                "severity": "error"
            },
            {
                "name": "required_name",
                "type": "required_field",
                "field": "name",
                "parameters": {
                    "allow_empty": False,
                    "message": "Name is required"
                },
                "severity": "critical"
            },
            {
                "name": "age_range",
                "type": "numeric_range",
                "field": "age",
                "parameters": {
                    "min_value": 0,
                    "max_value": 120,
                    "inclusive": True
                },
                "severity": "warning"
            }
        ]
    
    def test_initialization(self, server_config):
        """Test MCP rule loader initialization."""
        loader = MCPRuleLoader(server_config)
        
        assert loader.server_config == server_config
        assert loader.client is not None
        assert loader.client.command == "python"
        assert loader.client.args == ["test_server.py"]
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_load_rules_success(self, mock_asyncio_run, server_config, sample_rules_data):
        """Test successful rule loading."""
        # Mock the async operation to return parsed rules
        expected_rules = [
            ValidationRule(
                name="email_format",
                rule_type=RuleType.REGEX_CHECK,
                field="email",
                parameters={
                    "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "message": "Invalid email format"
                },
                severity=ValidationSeverity.ERROR
            ),
            ValidationRule(
                name="required_name",
                rule_type=RuleType.REQUIRED_FIELD,
                field="name",
                parameters={
                    "allow_empty": False,
                    "message": "Name is required"
                },
                severity=ValidationSeverity.CRITICAL
            ),
            ValidationRule(
                name="age_range",
                rule_type=RuleType.NUMERIC_RANGE,
                field="age",
                parameters={
                    "min_value": 0,
                    "max_value": 120,
                    "inclusive": True
                },
                severity=ValidationSeverity.WARNING
            )
        ]
        mock_asyncio_run.return_value = expected_rules
        
        loader = MCPRuleLoader(server_config)
        rules = loader.load_rules("test_rules")
        
        assert len(rules) == 3
        assert all(isinstance(rule, ValidationRule) for rule in rules)
        assert rules[0].name == "email_format"
        assert rules[1].name == "required_name"
        assert rules[2].name == "age_range"
        
        mock_asyncio_run.assert_called_once()
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_load_rules_connection_error(self, mock_asyncio_run, server_config):
        """Test rule loading with connection error."""
        mock_asyncio_run.side_effect = MCPConnectionError("Connection failed")
        
        loader = MCPRuleLoader(server_config)
        
        with pytest.raises(RuleLoadingError, match="MCP rule loading failed: Connection failed"):
            loader.load_rules("test_rules")
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_load_rules_general_error(self, mock_asyncio_run, server_config):
        """Test rule loading with general error."""
        mock_asyncio_run.side_effect = RuntimeError("Unexpected error")
        
        loader = MCPRuleLoader(server_config)
        
        with pytest.raises(RuleLoadingError, match="MCP rule loading failed: Unexpected error"):
            loader.load_rules("test_rules")
    
    def test_parse_rule_data_valid(self, server_config):
        """Test parsing valid rule data."""
        loader = MCPRuleLoader(server_config)
        
        rule_data = {
            "name": "test_rule",
            "type": "regex_check",
            "field": "test_field",
            "parameters": {"pattern": "test_pattern"},
            "severity": "warning"
        }
        
        rule = loader._parse_rule_data(rule_data)
        
        assert rule.name == "test_rule"
        assert rule.rule_type == RuleType.REGEX_CHECK
        assert rule.field == "test_field"
        assert rule.parameters == {"pattern": "test_pattern"}
        assert rule.severity == ValidationSeverity.WARNING
    
    def test_parse_rule_data_missing_required_fields(self, server_config):
        """Test parsing rule data with missing required fields."""
        loader = MCPRuleLoader(server_config)
        
        # Missing 'name'
        rule_data = {
            "type": "regex_check",
            "field": "test_field"
        }
        
        with pytest.raises(ValueError, match="Missing required field: name"):
            loader._parse_rule_data(rule_data)
        
        # Missing 'type'
        rule_data = {
            "name": "test_rule",
            "field": "test_field"
        }
        
        with pytest.raises(ValueError, match="Missing required field: type"):
            loader._parse_rule_data(rule_data)
        
        # Missing 'field'
        rule_data = {
            "name": "test_rule",
            "type": "regex_check"
        }
        
        with pytest.raises(ValueError, match="Missing required field: field"):
            loader._parse_rule_data(rule_data)
    
    def test_parse_rule_data_invalid_rule_type(self, server_config):
        """Test parsing rule data with invalid rule type."""
        loader = MCPRuleLoader(server_config)
        
        rule_data = {
            "name": "test_rule",
            "type": "invalid_type",
            "field": "test_field"
        }
        
        with pytest.raises(ValueError, match="Invalid rule type: invalid_type"):
            loader._parse_rule_data(rule_data)
    
    def test_parse_rule_data_invalid_severity(self, server_config):
        """Test parsing rule data with invalid severity (should default to ERROR)."""
        loader = MCPRuleLoader(server_config)
        
        rule_data = {
            "name": "test_rule",
            "type": "regex_check",
            "field": "test_field",
            "severity": "invalid_severity"
        }
        
        # Should not raise error, but default to ERROR severity
        rule = loader._parse_rule_data(rule_data)
        assert rule.severity == ValidationSeverity.ERROR
    
    def test_parse_rule_data_default_severity(self, server_config):
        """Test parsing rule data without severity (should default to ERROR)."""
        loader = MCPRuleLoader(server_config)
        
        rule_data = {
            "name": "test_rule",
            "type": "regex_check",
            "field": "test_field"
        }
        
        rule = loader._parse_rule_data(rule_data)
        assert rule.severity == ValidationSeverity.ERROR
    
    def test_parse_rule_data_default_parameters(self, server_config):
        """Test parsing rule data without parameters (should default to empty dict)."""
        loader = MCPRuleLoader(server_config)
        
        rule_data = {
            "name": "test_rule",
            "type": "required_field",
            "field": "test_field"
        }
        
        rule = loader._parse_rule_data(rule_data)
        assert rule.parameters == {}
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_validate_source_success(self, mock_asyncio_run, server_config):
        """Test successful source validation."""
        mock_asyncio_run.return_value = True
        
        loader = MCPRuleLoader(server_config)
        result = loader.validate_source("test_rules")
        
        assert result is True
        mock_asyncio_run.assert_called_once()
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_validate_source_failure(self, mock_asyncio_run, server_config):
        """Test source validation failure."""
        mock_asyncio_run.return_value = False
        
        loader = MCPRuleLoader(server_config)
        result = loader.validate_source("invalid_rules")
        
        assert result is False
    
    @patch('src.policy_dq.mcp.rule_loader.asyncio.run')
    def test_validate_source_exception(self, mock_asyncio_run, server_config):
        """Test source validation with exception."""
        mock_asyncio_run.side_effect = Exception("Connection error")
        
        loader = MCPRuleLoader(server_config)
        result = loader.validate_source("test_rules")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_load_rules_async_success(self, server_config, sample_rules_data):
        """Test async rule loading success."""
        with patch.object(MCPRuleLoader, '_load_rules_async') as mock_load_async:
            mock_load_async.return_value = [
                ValidationRule(
                    name="test_rule",
                    rule_type=RuleType.REGEX_CHECK,
                    field="test_field",
                    parameters={},
                    severity=ValidationSeverity.ERROR
                )
            ]
            
            loader = MCPRuleLoader(server_config)
            
            # Mock the client context manager and fetch_rules
            with patch.object(loader.client, '__aenter__', return_value=loader.client):
                with patch.object(loader.client, '__aexit__', return_value=None):
                    with patch.object(loader.client, 'fetch_rules', return_value=sample_rules_data):
                        rules = await loader._load_rules_async("test_rules")
                        
                        assert len(rules) == 1
                        assert rules[0].name == "test_rule"
    
    @pytest.mark.asyncio
    async def test_validate_source_async_success(self, server_config):
        """Test async source validation success."""
        loader = MCPRuleLoader(server_config)
        
        # Mock the client context manager and methods
        async def mock_aenter():
            return loader.client
        async def mock_aexit(*args):
            return None
        async def mock_list_tools():
            return ["tool1", "tool2"]
        async def mock_fetch_rules(*args):
            return []
        
        # Mock the connect method to avoid actual connection
        with patch.object(loader.client, 'connect', return_value=None):
            loader.client.__aenter__ = mock_aenter
            loader.client.__aexit__ = mock_aexit
            loader.client.list_available_tools = mock_list_tools
            loader.client.fetch_rules = mock_fetch_rules
            
            result = await loader._validate_source_async("test_rules")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_source_async_connection_error(self, server_config):
        """Test async source validation with connection error."""
        loader = MCPRuleLoader(server_config)
        
        # Mock the client context manager to raise connection error
        with patch.object(loader.client, '__aenter__', side_effect=MCPConnectionError("Connection failed")):
            result = await loader._validate_source_async("test_rules")
            
            assert result is False


class TestMCPRuleLoaderFactory:
    """Unit tests for MCPRuleLoaderFactory class."""
    
    def test_create_loader(self):
        """Test creating loader with configuration."""
        config = {
            "command": "python",
            "args": ["server.py"],
            "timeout": 30
        }
        
        loader = MCPRuleLoaderFactory.create_loader(config)
        
        assert isinstance(loader, MCPRuleLoader)
        assert loader.server_config == config
    
    def test_create_from_config_file(self, tmp_path):
        """Test creating loader from configuration file."""
        config = {
            "command": "python",
            "args": ["server.py"],
            "timeout": 30
        }
        
        # Create temporary config file
        config_file = tmp_path / "mcp_config.json"
        config_file.write_text(
            '{"command": "python", "args": ["server.py"], "timeout": 30}'
        )
        
        loader = MCPRuleLoaderFactory.create_from_config_file(str(config_file))
        
        assert isinstance(loader, MCPRuleLoader)
        assert loader.server_config == config
    
    def test_create_from_config_file_not_found(self):
        """Test creating loader from non-existent config file."""
        with pytest.raises(RuleLoadingError, match="Failed to load MCP configuration"):
            MCPRuleLoaderFactory.create_from_config_file("nonexistent.json")
    
    def test_create_from_config_file_invalid_json(self, tmp_path):
        """Test creating loader from invalid JSON config file."""
        # Create temporary config file with invalid JSON
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text('{"command": "python", invalid json')
        
        with pytest.raises(RuleLoadingError, match="Failed to load MCP configuration"):
            MCPRuleLoaderFactory.create_from_config_file(str(config_file))