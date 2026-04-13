# CLI Usage Guide

This guide provides comprehensive documentation for using the Policy DQ command-line interface.

## Installation

Ensure you have Python 3.11+ installed and have set up the project:

```bash
git clone <repository-url>
cd policy-dq
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Basic Commands

The CLI provides two main commands: `validate` and `summarize`.

### Validate Command

The `validate` command processes data files against validation rules and generates reports.

#### Basic Syntax

```bash
python -m src.policy_dq.cli.main validate [OPTIONS]
```

#### Required Arguments

- `--input-file` / `-i`: Path to the data file to validate (CSV or JSON)
- `--rules` / `-r`: Path to rules file (YAML or JSON) or MCP source identifier

#### Optional Arguments

- `--output-dir` / `-o`: Directory to save reports (default: current directory)
- `--severity-threshold` / `-s`: Minimum severity level for non-zero exit codes (default: error)
- `--output-formats` / `-f`: Output formats to generate (default: console,json,markdown)
- `--verbose` / `-v`: Enable verbose logging
- `--quiet` / `-q`: Suppress console output except errors

#### Examples

**Basic validation:**
```bash
python -m src.policy_dq.cli.main validate \
  --input-file sample_data/customers_with_issues.csv \
  --rules sample_data/comprehensive_rules.yaml
```

**Specify output directory:**
```bash
python -m src.policy_dq.cli.main validate \
  -i sample_data/products.json \
  -r sample_data/product_rules.json \
  -o ./validation_reports
```

**Set severity threshold:**
```bash
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --severity-threshold critical
```

**Generate only JSON report:**
```bash
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --output-formats json
```

**Verbose output:**
```bash
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --verbose
```

### Summarize Command

The `summarize` command processes existing JSON validation reports and displays summary information.

#### Basic Syntax

```bash
python -m src.policy_dq.cli.main summarize [OPTIONS]
```

#### Required Arguments

- `--report-file` / `-r`: Path to the JSON validation report file

#### Optional Arguments

- `--format` / `-f`: Output format (console, json, markdown) (default: console)
- `--output-file` / `-o`: Output file path (for json/markdown formats)

#### Examples

**Basic summary:**
```bash
python -m src.policy_dq.cli.main summarize \
  --report-file ./reports/validation_report.json
```

**Generate markdown summary:**
```bash
python -m src.policy_dq.cli.main summarize \
  -r ./reports/validation_report.json \
  --format markdown \
  --output-file summary.md
```

## Exit Codes

The CLI uses specific exit codes to indicate validation results:

- **0**: Success (no issues above severity threshold)
- **1**: Validation issues found above severity threshold
- **2**: System error (file not found, parsing error, etc.)

### Severity Thresholds

You can configure which severity levels trigger non-zero exit codes:

- `info`: Exit code 1 for any validation issue
- `warning`: Exit code 1 for warnings, errors, or critical issues
- `error`: Exit code 1 for errors or critical issues (default)
- `critical`: Exit code 1 only for critical issues

```bash
# Only exit with error code for critical issues
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --severity-threshold critical

# Exit with error code for any issue
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --severity-threshold info
```

## Output Formats

### Console Output

The default console output provides:
- Real-time validation progress
- Color-coded severity levels
- Summary statistics
- Top issues by severity

Example console output:
```
Data Validation Report
======================

Input File: customers_with_issues.csv
Rules Source: comprehensive_rules.yaml
Validation Date: 2024-01-15 10:30:00

Summary:
--------
Total Records: 20
Total Rules Applied: 14
Total Validations: 280

Results by Severity:
- CRITICAL: 2 failures
- ERROR: 15 failures  
- WARNING: 8 failures
- INFO: 0 failures

Passed Validations: 255 (91.1%)
Failed Validations: 25 (8.9%)

Critical Issues:
---------------
Row 11: customer_id_unique - Duplicate customer ID 'CUST001' found
Row 16: customer_id_required - Customer ID is missing
```

### JSON Output

Structured JSON output suitable for programmatic processing:

```bash
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --output-formats json \
  -o ./reports
```

Creates `validation_report.json` with complete validation results.

### Markdown Output

Human-readable markdown report with tables and formatting:

```bash
python -m src.policy_dq.cli.main validate \
  -i data.csv \
  -r rules.yaml \
  --output-formats markdown \
  -o ./reports
```

Creates `validation_report.md` with formatted tables and recommendations.

## Advanced Usage

### Batch Processing

Process multiple files using shell scripting:

```bash
#!/bin/bash
# validate_all.sh

for file in data/*.csv; do
    echo "Validating $file..."
    python -m src.policy_dq.cli.main validate \
      --input-file "$file" \
      --rules rules/customer_rules.yaml \
      --output-dir "reports/$(basename "$file" .csv)" \
      --quiet
    
    if [ $? -eq 0 ]; then
        echo "✓ $file passed validation"
    else
        echo "✗ $file failed validation"
    fi
done
```

### CI/CD Integration

Use in continuous integration pipelines:

```yaml
# .github/workflows/data-validation.yml
name: Data Validation

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Validate data files
      run: |
        python -m src.policy_dq.cli.main validate \
          --input-file data/production_data.csv \
          --rules rules/production_rules.yaml \
          --severity-threshold error \
          --output-formats json \
          --output-dir ./validation-results
    
    - name: Upload validation results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: validation-results
        path: ./validation-results/
```

### Docker Usage

Create a Dockerfile for containerized validation:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY sample_data/ ./sample_data/

ENTRYPOINT ["python", "-m", "src.policy_dq.cli.main"]
```

Build and run:

```bash
docker build -t policy-dq .

docker run -v $(pwd)/data:/data -v $(pwd)/reports:/reports policy-dq \
  validate \
  --input-file /data/customers.csv \
  --rules /app/sample_data/comprehensive_rules.yaml \
  --output-dir /reports
```

### Environment Variables

Configure common settings using environment variables:

```bash
export POLICY_DQ_OUTPUT_DIR="./reports"
export POLICY_DQ_SEVERITY_THRESHOLD="error"
export POLICY_DQ_OUTPUT_FORMATS="console,json"

python -m src.policy_dq.cli.main validate \
  --input-file data.csv \
  --rules rules.yaml
```

## Troubleshooting

### Common Issues

**File not found:**
```bash
Error: Input file 'data.csv' not found
```
- Verify the file path is correct
- Check file permissions
- Use absolute paths if needed

**Invalid rules file:**
```bash
Error: Failed to parse rules file 'rules.yaml'
```
- Validate YAML/JSON syntax
- Check rule schema compliance
- Review sample rule files for correct format

**Memory issues with large files:**
```bash
Error: Memory allocation failed
```
- Process files in smaller chunks
- Increase available memory
- Consider using streaming validation for very large files

**Permission denied:**
```bash
Error: Permission denied writing to output directory
```
- Check directory permissions
- Create output directory manually
- Use a different output location

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
python -m src.policy_dq.cli.main validate \
  --input-file data.csv \
  --rules rules.yaml \
  --verbose
```

This provides detailed information about:
- File parsing progress
- Rule loading and validation
- Individual validation results
- Performance metrics

### Getting Help

Display help information:

```bash
# General help
python -m src.policy_dq.cli.main --help

# Command-specific help
python -m src.policy_dq.cli.main validate --help
python -m src.policy_dq.cli.main summarize --help
```

## Performance Tips

1. **Rule Optimization**: Place most restrictive rules first
2. **File Format**: CSV parsing is generally faster than JSON
3. **Output Formats**: Console-only output is fastest
4. **Batch Processing**: Process multiple small files rather than one large file
5. **Memory Management**: Monitor memory usage with large datasets

## Integration Examples

### With Make

```makefile
# Makefile
.PHONY: validate-data validate-products validate-all

validate-data:
	python -m src.policy_dq.cli.main validate \
		--input-file data/customers.csv \
		--rules rules/customer_rules.yaml \
		--output-dir reports/customers

validate-products:
	python -m src.policy_dq.cli.main validate \
		--input-file data/products.json \
		--rules rules/product_rules.json \
		--output-dir reports/products

validate-all: validate-data validate-products
	@echo "All validations complete"
```

### With Python Scripts

```python
#!/usr/bin/env python3
# validate_pipeline.py

import subprocess
import sys
import os

def run_validation(input_file, rules_file, output_dir):
    """Run validation and return exit code"""
    cmd = [
        sys.executable, "-m", "src.policy_dq.cli.main", "validate",
        "--input-file", input_file,
        "--rules", rules_file,
        "--output-dir", output_dir,
        "--quiet"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    validations = [
        ("data/customers.csv", "rules/customer_rules.yaml", "reports/customers"),
        ("data/products.json", "rules/product_rules.json", "reports/products"),
    ]
    
    all_passed = True
    
    for input_file, rules_file, output_dir in validations:
        print(f"Validating {input_file}...")
        
        exit_code, stdout, stderr = run_validation(input_file, rules_file, output_dir)
        
        if exit_code == 0:
            print(f"✓ {input_file} passed validation")
        else:
            print(f"✗ {input_file} failed validation")
            if stderr:
                print(f"Error: {stderr}")
            all_passed = False
    
    if all_passed:
        print("All validations passed!")
        sys.exit(0)
    else:
        print("Some validations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
```