# MCP Integration Summary

## Overview

The Policy Data Quality system now supports MCP (Model Context Protocol) backed rule sources, allowing you to load validation rules from a centralized MCP server instead of local files.

## How to Use MCP-Backed Rule Sources

### Method 1: Using Configuration File (Recommended)

1. Create an MCP configuration file (`mcp_config.json`):

```json
{
  "rule_source": {
    "source": "customer_data",
    "source_type": "mcp",
    "mcp_config": {
      "command": "python",
      "args": ["mcp_validation_server.py"],
      "timeout": 30
    }
  },
  "output": {
    "output_directory": "reports",
    "generate_console_report": true,
    "generate_json_report": true,
    "generate_markdown_report": true
  },
  "severity_threshold": "error"
}
```

2. Run validation with the config file:

```bash
python -m src.policy_dq.cli validate data.json --config mcp_config.json
```

### Method 2: Direct CLI Usage

When the MCP server is running and properly configured, you can use MCP rule sources directly:

```bash
# The system will auto-detect that 'customer_data' is an MCP rule source
python -m src.policy_dq.cli validate data.json --rules customer_data --output-dir reports
```

## Available MCP Rule Sets

The MCP server provides these pre-configured rule sets:

- **customer_data**: Customer information validation
  - Email format validation
  - Phone number validation
  - Required field checks (customer_id, first_name, last_name)
  - String length validation for names
  - Uniqueness checks for customer_id

- **financial_data**: Financial transaction validation
  - Required field checks (transaction_id, amount)
  - Numeric range validation for amounts (0.01 to 1,000,000)
  - Date format validation (YYYY-MM-DD)
  - Uniqueness checks for transaction_id

- **product_catalog**: Product catalog validation
  - Required field checks (product_id, product_name, price)
  - Numeric range validation for prices
  - String length validation for product names
  - Uniqueness checks for product_id

- **user_registration**: User registration validation
  - Email format validation
  - Required field checks (username, password)
  - String length validation (username: 3-30 chars, password: 8-128 chars)
  - Uniqueness checks for username and email

## MCP Server Setup

1. The MCP server is already implemented in `mcp_validation_server.py`
2. To start the server (for testing):
   ```bash
   python mcp_validation_server.py
   ```

## Comparison: Local vs MCP Rules

### Local Rules (File-based)
```bash
python -m src.policy_dq.cli validate data.json --rules sample_rules/customer_validation.yaml
```
- ✅ No network dependency
- ✅ Fast loading
- ❌ Static rule definitions
- ❌ Distributed rule management

### MCP Rules (Server-based)
```bash
python -m src.policy_dq.cli validate data.json --rules customer_data
```
- ✅ Centralized rule management
- ✅ Dynamic rule generation
- ✅ Consistent across teams
- ✅ Template-based rules
- ❌ Network dependency
- ❌ Requires MCP server

## Example Usage

### 1. Customer Data Validation
```bash
# Create test data
echo '[
  {
    "customer_id": "CUST001",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567"
  },
  {
    "customer_id": "CUST002",
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "invalid-email",
    "phone": "555-987-6543"
  }
]' > test_customers.json

# Validate with MCP rules
python -m src.policy_dq.cli validate test_customers.json --config mcp_config.json
```

### 2. Financial Data Validation
```bash
# Update config for financial rules
sed 's/"customer_data"/"financial_data"/' mcp_config.json > financial_config.json

# Validate financial data
python -m src.policy_dq.cli validate transactions.json --config financial_config.json
```

## Fallback Support

The system supports fallback to local rules if MCP server is unavailable:

```json
{
  "rule_source": {
    "source": "customer_data",
    "source_type": "mcp",
    "fallback_sources": [
      {
        "source": "sample_rules/customer_validation.yaml",
        "type": "file"
      }
    ],
    "mcp_config": {
      "command": "python",
      "args": ["mcp_validation_server.py"],
      "timeout": 30
    }
  }
}
```

## Benefits of MCP Integration

1. **Centralized Rule Management**: All teams use consistent rule definitions
2. **Dynamic Rule Generation**: Rules can be generated based on data schema
3. **Template-Based Rules**: Reusable validation patterns
4. **Domain-Specific Rule Sets**: Pre-configured rules for common use cases
5. **Version Control**: Centralized rule versioning and tracking
6. **Rule Validation**: Server-side validation of rule configurations
7. **Consistency**: Ensures all validation follows the same standards

## Implementation Details

The MCP integration is implemented through:

- **MCPClient** (`src/policy_dq/mcp/client.py`): Handles MCP server connections
- **MCPRuleLoader** (`src/policy_dq/mcp/rule_loader.py`): Loads rules from MCP servers
- **MCPRuleLoadingManager** (`src/policy_dq/rules/manager.py`): Manages MCP rule loading with fallback
- **MCP Server** (`mcp_validation_server.py`): Provides rule templates and domain rule sets

The system automatically detects when to use MCP based on:
- Explicit `source_type: "mcp"` in configuration
- Rule source identifiers that don't match local file patterns
- MCP configuration presence

## Troubleshooting

If MCP validation fails:

1. **Check MCP server is running**: Ensure `mcp_validation_server.py` is accessible
2. **Verify configuration**: Check MCP config in your configuration file
3. **Use fallback**: Configure fallback to local rules for reliability
4. **Check logs**: Use `-v` flag for verbose logging to debug connection issues

## Next Steps

To use MCP-backed rule sources in your workflow:

1. Set up your MCP configuration file
2. Test with sample data to ensure connectivity
3. Configure fallback rules for production reliability
4. Integrate into your CI/CD pipeline for automated validation