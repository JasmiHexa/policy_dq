# Policy Data Quality (policy-dq)

A comprehensive Python-based data validation system that validates structured data files (CSV and JSON) against configurable business and data-quality policies. The system provides flexible rule loading from local files or MCP sources, supports multiple validation rule types, and generates detailed reports in multiple formats.

## Features

- **Multi-format Support**: Validate CSV and JSON files with automatic format detection
- **Flexible Rule Loading**: Load validation rules from local YAML/JSON files or MCP sources
- **Comprehensive Validation**: Support for required fields, type checking, regex patterns, numeric ranges, uniqueness constraints, and cross-field validations
- **Multiple Report Formats**: Generate reports in console, JSON, and Markdown formats
- **CLI and API**: Both command-line interface and Python API for programmatic usage
- **MCP Integration**: Model Context Protocol support for centralized rule management
- **Performance Optimized**: Efficient processing of large datasets with streaming support

## Installation

### Prerequisites

- Python 3.11 or higher
- pip for dependency management

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd policy-dq

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Alternative: Using Poetry

```bash
# Install poetry if not already installed
pip install poetry

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

## Quick Start

### Basic CLI Usage

```bash
# Validate a CSV file with local rules
python -m policy_dq.cli.main validate --input-file sample_data/customers_with_issues.csv --rules sample_data/comprehensive_rules.yaml --output-dir ./reports

# Validate a JSON file
python -m policy_dq.cli.main validate --input-file sample_data/products.json --rules sample_data/product_rules.json --output-dir ./reports

# Summarize an existing validation report
python -m policy_dq.cli.main summarize --report-file ./reports/validation_report.json
```

### Python API Usage

```python
from policy_dq.engine import ValidationEngine
from policy_dq.config import ValidationConfig

# Create validation configuration
config = ValidationConfig(
    input_file="data.csv",
    rules_source="rules.yaml",
    output_dir="./reports"
)

# Initialize validation engine
engine = ValidationEngine(config)

# Run validation
report = engine.validate()

# Access results
print(f"Total records: {report.total_records}")
print(f"Failed validations: {report.failed_validations}")
```

## CLI Reference

### validate Command

Validate a data file against specified rules.

```bash
python -m policy_dq.cli.main validate [OPTIONS]
```

**Options:**
- `--input-file, -i`: Path to the input data file (CSV or JSON)
- `--rules, -r`: Path to rules file or MCP source identifier
- `--output-dir, -o`: Directory to save validation reports (default: current directory)
- `--severity-threshold`: Minimum severity level for exit code failure (info, warning, error, critical)
- `--format`: Output format for console display (console, json, markdown)
- `--verbose, -v`: Enable verbose output

**Examples:**
```bash
# Basic validation
python -m policy_dq.cli.main validate -i data.csv -r rules.yaml

# With custom output directory and severity threshold
python -m policy_dq.cli.main validate -i data.csv -r rules.yaml -o ./reports --severity-threshold error

# Using MCP source for rules
python -m policy_dq.cli.main validate -i data.csv -r mcp://validation-server/customer-rules
```

### summarize Command

Generate a summary from an existing JSON validation report.

```bash
python -m policy_dq.cli.main summarize [OPTIONS]
```

**Options:**
- `--report-file, -f`: Path to the JSON validation report file
- `--format`: Output format (console, markdown)

**Example:**
```bash
python -m policy_dq.cli.main summarize -f ./reports/validation_report.json --format markdown
```

## Rule Configuration

### Rule File Format

Rules can be defined in YAML or JSON format. Here's an example YAML configuration:

```yaml
version: "1.0"
rule_sets:
  - name: "customer_validation"
    rules:
      - name: "email_required"
        type: "required_field"
        field: "email"
        severity: "error"
      
      - name: "email_format"
        type: "regex_check"
        field: "email"
        parameters:
          pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        severity: "error"
      
      - name: "age_range"
        type: "numeric_range"
        field: "age"
        parameters:
          min: 18
          max: 99
        severity: "warning"
      
      - name: "customer_id_unique"
        type: "uniqueness"
        field: "customer_id"
        severity: "critical"
      
      - name: "date_consistency"
        type: "cross_field"
        field: "end_date"
        parameters:
          comparison: "greater_than_or_equal"
          compare_field: "start_date"
        severity: "error"
```

### Supported Rule Types

1. **required_field**: Validates that a field exists and is not empty
2. **type_check**: Validates data types (string, int, float, bool, date)
3. **regex_check**: Validates field values against regex patterns
4. **numeric_range**: Validates numeric values within min/max ranges
5. **uniqueness**: Ensures field values are unique across all records
6. **cross_field**: Validates relationships between multiple fields

### Severity Levels

- **info**: Informational messages
- **warning**: Non-critical issues
- **error**: Data quality problems
- **critical**: Severe data integrity issues

## MCP Configuration

### Setting up MCP Integration

The system supports Model Context Protocol (MCP) for centralized rule management. Configure MCP in your environment:

```python
# Example MCP configuration
mcp_config = {
    "server_url": "https://validation-server.example.com",
    "auth_token": "your-auth-token",
    "timeout": 30
}
```

### Using MCP Rules

```bash
# Validate using MCP-sourced rules
python -m policy_dq.cli.main validate -i data.csv -r mcp://server/ruleset-id
```

### MCP Fallback

The system includes fallback mechanisms for MCP failures:
- Local rule caching
- Graceful degradation to local rules
- Clear error messages for connection issues

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/policy_dq --cov-report=html

# Run specific test categories
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/   # Integration tests only

# Run performance tests
python -m pytest tests/integration/test_performance.py -v
```

### Test Organization

- `tests/unit/`: Fast, isolated unit tests
- `tests/integration/`: Component integration tests
- `tests/conftest.py`: Shared pytest fixtures

### Using the Test Runner

```bash
# Use the provided test runner script
python run_tests.py

# Run with specific options
python run_tests.py --unit-only
python run_tests.py --integration-only
python run_tests.py --coverage
```

## Sample Data

The project includes comprehensive sample data for testing and demonstration:

- `sample_data/customers_with_issues.csv`: CSV file with various data quality issues
- `sample_data/clean_customers.csv`: Clean CSV file for successful validation
- `sample_data/products.json`: JSON file with nested structures
- `sample_data/comprehensive_rules.yaml`: Complete rule set demonstrating all validation types
- `sample_data/product_rules.json`: JSON-format rules for product validation

### Running Sample Validations

```bash
# Validate sample CSV with issues
python -m policy_dq.cli.main validate -i sample_data/customers_with_issues.csv -r sample_data/comprehensive_rules.yaml -o ./sample_reports

# Validate clean CSV (should pass)
python -m policy_dq.cli.main validate -i sample_data/clean_customers.csv -r sample_data/comprehensive_rules.yaml -o ./sample_reports

# Validate JSON products
python -m policy_dq.cli.main validate -i sample_data/products.json -r sample_data/product_rules.json -o ./sample_reports
```

## Performance Considerations

### Large File Handling

- Files over 50MB use streaming parsers to minimize memory usage
- Progress indicators show validation progress for long-running operations
- Memory usage scales linearly with file size

### Optimization Tips

- Use appropriate severity thresholds to focus on critical issues
- Cache rule configurations for repeated validations
- Consider parallel processing for multiple file validation

## Exit Codes

The CLI uses standard exit codes for integration with CI/CD pipelines:

- `0`: Validation passed or no issues above severity threshold
- `1`: Validation failed above configured severity threshold
- `2`: System error (file not found, parsing error, etc.)
- `3`: Configuration error (invalid rules, missing parameters)

## Assumptions and Limitations

### Current Assumptions

1. **File Formats**: Only CSV and JSON files are supported
2. **Rule Sources**: Local files (YAML/JSON) and MCP sources only
3. **Memory**: Assumes sufficient memory for dataset processing (streaming used for large files)
4. **Encoding**: UTF-8 encoding assumed for text files
5. **Field Names**: Case-sensitive field name matching

### Known Limitations

1. **Nested JSON**: Limited support for deeply nested JSON structures (max 10 levels)
2. **CSV Dialects**: Limited CSV dialect detection (standard comma-separated format)
3. **Rule Complexity**: Cross-field validations limited to simple comparisons
4. **Concurrent Processing**: Single-threaded validation (parallel processing planned for future)
5. **Rule Caching**: Basic rule caching (advanced caching strategies planned)

### Future Enhancements

- Support for additional file formats (XML, Parquet, Excel)
- Advanced rule composition and conditional logic
- Real-time validation streaming
- Distributed validation for very large datasets
- Web-based rule configuration interface
- Integration with popular data pipeline tools

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Set up virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate.bat  # On Windows
   pip install -r requirements.txt
   pip install -e .
   ```
4. Run tests: `python -m pytest`
5. Submit a pull request

### Code Quality

- Maintain 90%+ test coverage
- Follow PEP 8 style guidelines
- Use type hints throughout
- Write comprehensive docstrings

## License

[License information to be added]

## Support

For issues, questions, or contributions, please [create an issue](repository-issues-url) in the project repository.