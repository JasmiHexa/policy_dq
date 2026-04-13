# How to Run Policy Data Quality with MCP-Backed Rule Sources

## Step-by-Step Guide

### Method 1: Using Configuration File (Recommended)

#### Step 1: Create MCP Configuration File

Create a file called `mcp_config.json`:

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

#### Step 2: Run Validation with MCP Configuration

```bash
python -m src.policy_dq.cli validate test_mcp_simple.json --config mcp_config.json
```

### Method 2: Direct CLI Usage (When MCP Server is Running)

#### Step 1: Start MCP Server (Optional - for testing)

In one terminal:
```bash
python mcp_validation_server.py
```

#### Step 2: Run Validation with MCP Rule Source

In another terminal:
```bash
python -m src.policy_dq.cli validate test_mcp_simple.json --rules customer_data --output-dir reports
```

## Available MCP Rule Sets

You can use any of these rule sets as the `source` in your configuration:

- **`customer_data`** - Customer information validation
- **`financial_data`** - Financial transaction validation  
- **`product_catalog`** - Product catalog validation
- **`user_registration`** - User registration validation

## Example Commands

### 1. Customer Data Validation
```bash
# Using config file
python -m src.policy_dq.cli validate test_mcp_simple.json --config mcp_config.json

# Direct usage (if MCP server is running)
python -m src.policy_dq.cli validate test_mcp_simple.json --rules customer_data
```

### 2. Financial Data Validation
```bash
# Create financial config
echo '{
  "rule_source": {
    "source": "financial_data",
    "source_type": "mcp",
    "mcp_config": {
      "command": "python",
      "args": ["mcp_validation_server.py"],
      "timeout": 30
    }
  },
  "output": {
    "output_directory": "reports"
  }
}' > financial_config.json

# Run validation
python -m src.policy_dq.cli validate financial_data.json --config financial_config.json
```

### 3. With Custom Options
```bash
# With verbose output and custom severity threshold
python -m src.policy_dq.cli -v validate test_mcp_simple.json --config mcp_config.json

# With fail-fast mode
echo '{
  "rule_source": {
    "source": "customer_data",
    "source_type": "mcp",
    "mcp_config": {
      "command": "python",
      "args": ["mcp_validation_server.py"],
      "timeout": 30
    }
  },
  "fail_fast": true,
  "severity_threshold": "warning"
}' > mcp_failfast_config.json

python -m src.policy_dq.cli validate test_mcp_simple.json --config mcp_failfast_config.json
```

## Troubleshooting

### If MCP Connection Fails

1. **Check MCP Library Installation**:
   ```bash
   python -c "import mcp; print('MCP library available')"
   ```

2. **Use Fallback Configuration**:
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

3. **Test with Local Rules First**:
   ```bash
   python -m src.policy_dq.cli validate test_mcp_simple.json --rules sample_rules/customer_validation.yaml
   ```

### Common Issues

- **"MCP library not available"**: Install MCP with `pip install mcp`
- **Connection timeout**: Increase timeout in config or check server availability
- **Rule set not found**: Use one of the available rule sets listed above

## Comparison: Local vs MCP Rules

### Local Rules (Working)
```bash
python -m src.policy_dq.cli validate test_mcp_simple.json --rules sample_rules/customer_validation.yaml
```
✅ Fast and reliable
✅ No network dependency
❌ Static rules only

### MCP Rules (Advanced)
```bash
python -m src.policy_dq.cli validate test_mcp_simple.json --config mcp_config.json
```
✅ Dynamic rule generation
✅ Centralized management
✅ Template-based rules
❌ Requires MCP server
❌ Network dependency

## Quick Test

To quickly test MCP integration:

1. **Create test data** (already exists as `test_mcp_simple.json`)
2. **Create MCP config** (already exists as `mcp_config.json`)
3. **Run validation**:
   ```bash
   python -m src.policy_dq.cli validate test_mcp_simple.json --config mcp_config.json
   ```

The system will automatically:
- Connect to the MCP server
- Fetch the `customer_data` rule set
- Apply validation rules to your data
- Generate reports in the `reports/` directory

## Expected Output

When working correctly, you should see:
- Console output showing validation results
- JSON report in `reports/validation_report.json`
- Markdown report in `reports/validation_report.md`
- Detailed validation failures with rule names and messages