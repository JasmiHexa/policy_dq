# Configuration Guide

This guide covers how to configure validation rules, set up MCP integration, and customize the Policy DQ system.

## Rule Configuration

### Rule File Formats

Policy DQ supports both YAML and JSON formats for rule configuration files.

#### YAML Format (Recommended)

YAML provides better readability and supports comments:

```yaml
version: "1.0"
rule_sets:
  - name: "customer_validation"
    description: "Validation rules for customer data"
    rules:
      - name: "email_required"
        type: "required_field"
        field: "email"
        severity: "error"
        description: "Email address is mandatory"
      
      - name: "email_format"
        type: "regex_check"
        field: "email"
        parameters:
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        severity: "error"
        description: "Email must be in valid format"
```

#### JSON Format

JSON format for programmatic generation:

```json
{
  "version": "1.0",
  "rule_sets": [
    {
      "name": "customer_validation",
      "description": "Validation rules for customer data",
      "rules": [
        {
          "name": "email_required",
          "type": "required_field",
          "field": "email",
          "severity": "error",
          "description": "Email address is mandatory"
        }
      ]
    }
  ]
}
```

### Rule Schema

#### Top-Level Structure

```yaml
version: "1.0"                    # Required: Schema version
rule_sets:                        # Required: Array of rule sets
  - name: "rule_set_name"         # Required: Unique rule set identifier
    description: "Description"     # Optional: Human-readable description
    rules: []                     # Required: Array of validation rules
```

#### Rule Structure

Each rule must contain:

```yaml
- name: "unique_rule_name"        # Required: Unique rule identifier
  type: "rule_type"               # Required: One of the supported rule types
  field: "field_name"             # Required: Field to validate
  parameters: {}                  # Optional: Rule-specific parameters
  severity: "severity_level"      # Optional: Default is "error"
  description: "Description"      # Optional: Human-readable description
```

### Rule Types

#### 1. Required Field

Validates that a field exists and is not empty.

```yaml
- name: "name_required"
  type: "required_field"
  field: "name"
  severity: "error"
  description: "Name field must be present and non-empty"
```

**Parameters:** None

**Validation Logic:**
- Field must exist in the record
- Field value must not be empty string, null, or whitespace-only

#### 2. Type Check

Validates that field values match the specified data type.

```yaml
- name: "age_is_numeric"
  type: "type_check"
  field: "age"
  parameters:
    expected_type: "int"          # Required: int, float, str, bool, date
    date_format: "%Y-%m-%d"       # Optional: For date type validation
  severity: "error"
```

**Supported Types:**
- `int`: Integer numbers
- `float`: Decimal numbers
- `str`: String values
- `bool`: Boolean values (true/false)
- `date`: Date values (requires date_format parameter)

**Date Format Examples:**
- `%Y-%m-%d`: 2024-01-15
- `%m/%d/%Y`: 01/15/2024
- `%d-%b-%Y`: 15-Jan-2024

#### 3. Regex Check

Validates that field values match a regular expression pattern.

```yaml
- name: "email_format"
  type: "regex_check"
  field: "email"
  parameters:
    pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
  severity: "error"
```

**Parameters:**
- `pattern` (required): Regular expression pattern

**Common Patterns:**
```yaml
# Email validation
pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"

# Phone number (XXX-XXXX format)
pattern: "^\\d{3}-\\d{4}$"

# Customer ID format (CUSTXXX)
pattern: "^CUST\\d{3}$"

# Postal code (5 digits)
pattern: "^\\d{5}$"

# Status values
pattern: "^(active|inactive|pending)$"
```

#### 4. Numeric Range

Validates that numeric values fall within specified bounds.

```yaml
- name: "age_range"
  type: "numeric_range"
  field: "age"
  parameters:
    min: 18                       # Optional: Minimum value (inclusive)
    max: 99                       # Optional: Maximum value (inclusive)
  severity: "warning"
```

**Parameters:**
- `min` (optional): Minimum allowed value (inclusive)
- `max` (optional): Maximum allowed value (inclusive)

**Examples:**
```yaml
# Age between 18 and 65
parameters:
  min: 18
  max: 65

# Price must be positive
parameters:
  min: 0.01

# Score cannot exceed 100
parameters:
  max: 100
```

#### 5. Uniqueness

Validates that field values are unique across all records.

```yaml
- name: "customer_id_unique"
  type: "uniqueness"
  field: "customer_id"
  severity: "critical"
```

**Parameters:** None

**Notes:**
- Compares values across the entire dataset
- Case-sensitive comparison
- Empty values are not considered duplicates of each other

#### 6. Cross-Field Validation

Validates relationships between multiple fields in the same record.

```yaml
- name: "date_consistency"
  type: "cross_field"
  field: "end_date"
  parameters:
    comparison: "greater_than_or_equal"    # Required: Comparison operator
    compare_field: "start_date"            # Required: Field to compare against
  severity: "error"
```

**Comparison Operators:**
- `greater_than`: field > compare_field
- `greater_than_or_equal`: field >= compare_field
- `less_than`: field < compare_field
- `less_than_or_equal`: field <= compare_field
- `equal`: field == compare_field
- `not_equal`: field != compare_field

**Examples:**
```yaml
# End date after start date
- name: "date_order"
  type: "cross_field"
  field: "end_date"
  parameters:
    comparison: "greater_than_or_equal"
    compare_field: "start_date"

# Confirm password matches password
- name: "password_confirmation"
  type: "cross_field"
  field: "confirm_password"
  parameters:
    comparison: "equal"
    compare_field: "password"

# Discount cannot exceed price
- name: "discount_validation"
  type: "cross_field"
  field: "discount"
  parameters:
    comparison: "less_than_or_equal"
    compare_field: "price"
```

### Severity Levels

Configure the impact level of validation failures:

- **`critical`**: System-breaking issues that must be fixed immediately
- **`error`**: Data quality issues that should be addressed
- **`warning`**: Minor issues or recommendations
- **`info`**: Informational messages

```yaml
- name: "customer_id_required"
  type: "required_field"
  field: "customer_id"
  severity: "critical"            # Will cause exit code 2

- name: "email_format"
  type: "regex_check"
  field: "email"
  severity: "error"               # Will cause exit code 1

- name: "phone_format"
  type: "regex_check"
  field: "phone"
  severity: "warning"             # Will not affect exit code by default
```

### Rule Organization

#### Multiple Rule Sets

Organize rules into logical groups:

```yaml
version: "1.0"
rule_sets:
  - name: "customer_basic_validation"
    description: "Basic customer data validation"
    rules:
      - name: "customer_id_required"
        type: "required_field"
        field: "customer_id"
        severity: "critical"
  
  - name: "customer_advanced_validation"
    description: "Advanced customer data validation"
    rules:
      - name: "email_format"
        type: "regex_check"
        field: "email"
        parameters:
          pattern: "^[^@]+@[^@]+\\.[^@]+$"
        severity: "error"
```

#### Rule Dependencies

While not explicitly supported, you can organize rules logically:

```yaml
rules:
  # First validate required fields
  - name: "email_required"
    type: "required_field"
    field: "email"
    severity: "critical"
  
  # Then validate format (only meaningful if field exists)
  - name: "email_format"
    type: "regex_check"
    field: "email"
    parameters:
      pattern: "^[^@]+@[^@]+\\.[^@]+$"
    severity: "error"
```

## MCP Integration

### Overview

Model Context Protocol (MCP) integration allows loading validation rules from remote sources, enabling centralized rule management and dynamic rule updates.

### MCP Configuration

#### Basic MCP Setup

Configure MCP connection in your application:

```python
from src.policy_dq.mcp.client import MCPClient

mcp_config = {
    "server_url": "https://your-mcp-server.com/api/v1",
    "auth_token": "your-authentication-token",
    "timeout": 30,
    "retry_attempts": 3
}

client = MCPClient(mcp_config)
```

#### Environment Variables

Configure MCP using environment variables:

```bash
export MCP_SERVER_URL="https://your-mcp-server.com/api/v1"
export MCP_AUTH_TOKEN="your-token"
export MCP_TIMEOUT="30"
export MCP_RETRY_ATTEMPTS="3"
```

#### Configuration File

Create an MCP configuration file:

```yaml
# mcp_config.yaml
mcp:
  server_url: "https://your-mcp-server.com/api/v1"
  auth_token: "your-authentication-token"
  timeout: 30
  retry_attempts: 3
  cache_ttl: 3600                 # Cache rules for 1 hour
  fallback_rules: "local_rules.yaml"  # Fallback if MCP unavailable
```

### Using MCP Rules

#### CLI Usage

```bash
python -m src.policy_dq.cli.main validate \
  --input-file data.csv \
  --rules "mcp://customer_validation_rules" \
  --output-dir ./reports
```

#### Python API Usage

```python
from src.policy_dq.rules.mcp_loader import MCPRuleLoader
from src.policy_dq.engine import ValidationEngine

# Configure MCP loader
mcp_config = {
    "server_url": "https://your-mcp-server.com/api/v1",
    "auth_token": "your-token"
}

loader = MCPRuleLoader(mcp_config)
rules = await loader.load_rules("customer_validation_rules")

# Use with validation engine
engine = ValidationEngine()
report = engine.validate_data(data, rules)
```

### MCP Rule Format

MCP servers should return rules in the standard format:

```json
{
  "rule_set_id": "customer_validation_rules",
  "version": "1.2",
  "last_updated": "2024-01-15T10:30:00Z",
  "rules": [
    {
      "name": "email_required",
      "type": "required_field",
      "field": "email",
      "severity": "error",
      "description": "Email address is mandatory"
    }
  ]
}
```

### Error Handling

Configure fallback behavior for MCP failures:

```python
mcp_config = {
    "server_url": "https://your-mcp-server.com/api/v1",
    "auth_token": "your-token",
    "fallback_rules": "local_rules.yaml",    # Use local rules if MCP fails
    "fail_on_error": False,                  # Continue with fallback rules
    "cache_rules": True,                     # Cache rules locally
    "cache_duration": 3600                   # Cache for 1 hour
}
```

## Advanced Configuration

### Custom Rule Processors

Extend the system with custom validation logic:

```python
from src.policy_dq.validators.processors.base import BaseProcessor
from src.policy_dq.models import ValidationResult, ValidationSeverity

class CustomEmailProcessor(BaseProcessor):
    def process(self, rule, record, row_index):
        field_value = record.get(rule.field)
        
        # Custom validation logic
        if field_value and "@company.com" not in field_value:
            return ValidationResult(
                rule_name=rule.name,
                field=rule.field,
                row_index=row_index,
                severity=rule.severity,
                message=f"Email must be from company domain",
                passed=False
            )
        
        return ValidationResult(
            rule_name=rule.name,
            field=rule.field,
            row_index=row_index,
            severity=rule.severity,
            message="Email domain validation passed",
            passed=True
        )

# Register custom processor
from src.policy_dq.validators.core import DataValidator
DataValidator.register_processor("custom_email", CustomEmailProcessor)
```

### Configuration Profiles

Create configuration profiles for different environments:

```yaml
# config/development.yaml
validation:
  severity_threshold: "warning"
  output_formats: ["console", "json"]
  verbose: true

mcp:
  server_url: "https://dev-mcp-server.com/api/v1"
  cache_ttl: 300

# config/production.yaml
validation:
  severity_threshold: "error"
  output_formats: ["json", "markdown"]
  verbose: false

mcp:
  server_url: "https://prod-mcp-server.com/api/v1"
  cache_ttl: 3600
```

### Performance Tuning

Configure performance settings:

```yaml
performance:
  batch_size: 1000              # Process records in batches
  parallel_processing: true     # Enable parallel rule processing
  memory_limit: "2GB"          # Maximum memory usage
  cache_size: 10000            # Maximum cached rules
```

## Best Practices

### Rule Design

1. **Start Simple**: Begin with basic required field and type checks
2. **Layer Validation**: Apply rules in order of importance
3. **Use Appropriate Severity**: Reserve critical for system-breaking issues
4. **Provide Clear Messages**: Include helpful descriptions for each rule
5. **Test Thoroughly**: Validate rules against sample data

### Performance Optimization

1. **Rule Order**: Place most restrictive rules first
2. **Batch Processing**: Process large datasets in chunks
3. **Caching**: Cache frequently used rules
4. **Parallel Processing**: Enable for large datasets
5. **Memory Management**: Monitor memory usage with large files

### Maintenance

1. **Version Control**: Track rule changes over time
2. **Documentation**: Document rule business logic
3. **Testing**: Create test datasets for rule validation
4. **Monitoring**: Track validation success rates
5. **Regular Review**: Periodically review and update rules

### Security

1. **Authentication**: Secure MCP connections with proper authentication
2. **Input Validation**: Validate rule configurations before use
3. **Access Control**: Restrict rule modification permissions
4. **Audit Logging**: Log rule changes and validation results
5. **Data Privacy**: Ensure sensitive data is handled appropriately

## Troubleshooting

### Common Configuration Issues

**Invalid YAML syntax:**
```
Error: Failed to parse rules file
```
- Use a YAML validator
- Check indentation (use spaces, not tabs)
- Verify quote escaping in regex patterns

**Missing required fields:**
```
Error: Rule missing required field 'type'
```
- Verify all required rule fields are present
- Check field names for typos

**Invalid rule type:**
```
Error: Unknown rule type 'invalid_type'
```
- Use only supported rule types
- Check for typos in rule type names

**MCP connection failures:**
```
Error: Failed to connect to MCP server
```
- Verify server URL and authentication
- Check network connectivity
- Review MCP server logs

### Validation Issues

**Rules not applying:**
- Verify field names match data file columns exactly
- Check rule set names and structure
- Enable verbose logging for debugging

**Performance problems:**
- Reduce batch size for memory-constrained environments
- Disable parallel processing if causing issues
- Consider processing files in smaller chunks

**Unexpected results:**
- Review rule logic and parameters
- Test rules against known good/bad data
- Check data types and formats