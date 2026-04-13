# Policy DQ API Documentation

This document provides comprehensive documentation for the Policy DQ Python API.

## Overview

The Policy DQ API provides programmatic access to data validation functionality, allowing you to integrate validation into your Python applications without using the CLI.

## Core Components

### ValidationEngine

The main orchestrator for validation workflows.

```python
from src.policy_dq.engine import ValidationEngine
from src.policy_dq.config import ValidationConfig

# Create configuration
config = ValidationConfig(
    input_file="data.csv",
    rules_source="rules.yaml",
    output_dir="./reports"
)

# Initialize engine
engine = ValidationEngine(config)

# Run validation
report = engine.validate()
```

#### Methods

##### `validate() -> ValidationReport`

Executes the complete validation workflow and returns a detailed report.

**Returns:**
- `ValidationReport`: Complete validation results with summary and detailed findings

**Example:**
```python
report = engine.validate()
print(f"Success rate: {report.success_rate:.1f}%")
print(f"Critical issues: {report.summary_by_severity[ValidationSeverity.CRITICAL]}")
```

##### `validate_data(data: List[Dict[str, Any]], rules: List[ValidationRule]) -> ValidationReport`

Validates in-memory data against provided rules.

**Parameters:**
- `data`: List of dictionaries representing records
- `rules`: List of ValidationRule objects

**Returns:**
- `ValidationReport`: Validation results

**Example:**
```python
data = [
    {"name": "John", "age": 25, "email": "john@example.com"},
    {"name": "Jane", "age": 30, "email": "jane@example.com"}
]

rules = [
    ValidationRule(
        name="email_required",
        rule_type=RuleType.REQUIRED_FIELD,
        field="email",
        parameters={},
        severity=ValidationSeverity.ERROR
    )
]

report = engine.validate_data(data, rules)
```

### ValidationConfig

Configuration object for validation settings.

```python
from src.policy_dq.config import ValidationConfig

config = ValidationConfig(
    input_file="path/to/data.csv",
    rules_source="path/to/rules.yaml",
    output_dir="./reports",
    severity_threshold=ValidationSeverity.ERROR,
    output_formats=["console", "json", "markdown"]
)
```

#### Parameters

- `input_file` (str): Path to the data file to validate
- `rules_source` (str): Path to rules file or MCP source identifier
- `output_dir` (str, optional): Directory for output reports
- `severity_threshold` (ValidationSeverity, optional): Minimum severity for exit code determination
- `output_formats` (List[str], optional): List of output formats to generate
- `mcp_config` (Dict[str, Any], optional): MCP connection configuration

### Data Models

#### ValidationRule

Represents a single validation rule.

```python
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity

rule = ValidationRule(
    name="email_format",
    rule_type=RuleType.REGEX_CHECK,
    field="email",
    parameters={"pattern": r"^[^@]+@[^@]+\.[^@]+$"},
    severity=ValidationSeverity.ERROR
)
```

#### ValidationResult

Represents the result of applying a single rule to a single record.

```python
from src.policy_dq.models import ValidationResult, ValidationSeverity

result = ValidationResult(
    rule_name="email_format",
    field="email",
    row_index=5,
    severity=ValidationSeverity.ERROR,
    message="Invalid email format",
    passed=False
)
```

#### ValidationReport

Contains complete validation results and summary statistics.

```python
# Access report data
print(f"Total records: {report.total_records}")
print(f"Total rules: {report.total_rules}")
print(f"Passed validations: {report.passed_validations}")
print(f"Failed validations: {report.failed_validations}")

# Access results by severity
critical_count = report.summary_by_severity[ValidationSeverity.CRITICAL]
error_count = report.summary_by_severity[ValidationSeverity.ERROR]

# Iterate through individual results
for result in report.results:
    if not result.passed:
        print(f"Row {result.row_index}: {result.message}")
```

## Parsers

### DataParser Interface

Base interface for all data parsers.

```python
from src.policy_dq.parsers.base import DataParser

class CustomParser(DataParser):
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        # Implementation
        pass
    
    def validate_format(self, file_path: str) -> bool:
        # Implementation
        pass
```

### CSV Parser

```python
from src.policy_dq.parsers.csv_parser import CSVParser

parser = CSVParser()
data = parser.parse("data.csv")
```

### JSON Parser

```python
from src.policy_dq.parsers.json_parser import JSONParser

parser = JSONParser()
data = parser.parse("data.json")
```

### Parser Factory

Automatically selects the appropriate parser based on file extension.

```python
from src.policy_dq.parsers.factory import ParserFactory

parser = ParserFactory.create_parser("data.csv")  # Returns CSVParser
data = parser.parse("data.csv")
```

## Validators

### DataValidator

Core validation engine that applies rules to data.

```python
from src.policy_dq.validators.core import DataValidator

validator = DataValidator(rules)
report = validator.validate(data)
```

### Rule Processors

Individual processors for each rule type:

```python
from src.policy_dq.validators.processors.required_field import RequiredFieldProcessor
from src.policy_dq.validators.processors.type_check import TypeCheckProcessor
from src.policy_dq.validators.processors.regex import RegexProcessor
from src.policy_dq.validators.processors.numeric_range import NumericRangeProcessor
from src.policy_dq.validators.processors.uniqueness import UniquenessProcessor
from src.policy_dq.validators.processors.cross_field import CrossFieldProcessor

# Use individual processors
processor = RequiredFieldProcessor()
results = processor.process(rule, data, 0)  # rule, record, row_index
```

## Rule Loading

### File Rule Loader

Load rules from local YAML or JSON files.

```python
from src.policy_dq.rules.file_loader import FileRuleLoader

loader = FileRuleLoader()
rules = loader.load_rules("rules.yaml")
```

### MCP Rule Loader

Load rules from Model Context Protocol sources.

```python
from src.policy_dq.rules.mcp_loader import MCPRuleLoader

loader = MCPRuleLoader({
    "server_url": "https://mcp-server.com",
    "auth_token": "token"
})
rules = await loader.load_rules("rule_set_id")
```

## Reporters

### Console Reporter

```python
from src.policy_dq.reporters.console import ConsoleReporter

reporter = ConsoleReporter()
reporter.generate_report(report, None)  # Prints to console
```

### JSON Reporter

```python
from src.policy_dq.reporters.json_reporter import JSONReporter

reporter = JSONReporter()
reporter.generate_report(report, "report.json")
```

### Markdown Reporter

```python
from src.policy_dq.reporters.markdown import MarkdownReporter

reporter = MarkdownReporter()
reporter.generate_report(report, "report.md")
```

## Error Handling

The API uses custom exception classes for different error scenarios:

```python
from src.policy_dq.exceptions import (
    ValidationError,
    RuleLoadingError,
    DataParsingError,
    ReportGenerationError
)

try:
    report = engine.validate()
except RuleLoadingError as e:
    print(f"Failed to load rules: {e}")
except DataParsingError as e:
    print(f"Failed to parse data: {e}")
except ValidationError as e:
    print(f"Validation error: {e}")
```

## Advanced Usage Examples

### Custom Validation Workflow

```python
from src.policy_dq.parsers.factory import ParserFactory
from src.policy_dq.rules.file_loader import FileRuleLoader
from src.policy_dq.validators.core import DataValidator
from src.policy_dq.reporters.json_reporter import JSONReporter

# Manual workflow
parser = ParserFactory.create_parser("data.csv")
data = parser.parse("data.csv")

rule_loader = FileRuleLoader()
rules = rule_loader.load_rules("rules.yaml")

validator = DataValidator(rules)
report = validator.validate(data)

reporter = JSONReporter()
reporter.generate_report(report, "custom_report.json")
```

### Batch Validation

```python
import os
from src.policy_dq.engine import ValidationEngine
from src.policy_dq.config import ValidationConfig

def validate_directory(data_dir: str, rules_file: str, output_dir: str):
    """Validate all CSV files in a directory"""
    results = {}
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            file_path = os.path.join(data_dir, filename)
            
            config = ValidationConfig(
                input_file=file_path,
                rules_source=rules_file,
                output_dir=output_dir
            )
            
            engine = ValidationEngine(config)
            report = engine.validate()
            
            results[filename] = {
                'success_rate': report.success_rate,
                'critical_issues': report.summary_by_severity.get(ValidationSeverity.CRITICAL, 0),
                'total_issues': report.failed_validations
            }
    
    return results

# Usage
results = validate_directory("./data", "rules.yaml", "./reports")
for file, stats in results.items():
    print(f"{file}: {stats['success_rate']:.1f}% success rate")
```

### Custom Rule Creation

```python
from src.policy_dq.models import ValidationRule, RuleType, ValidationSeverity

def create_email_rule(field_name: str) -> ValidationRule:
    """Create a standard email validation rule"""
    return ValidationRule(
        name=f"{field_name}_email_format",
        rule_type=RuleType.REGEX_CHECK,
        field=field_name,
        parameters={
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        },
        severity=ValidationSeverity.ERROR
    )

def create_age_rule(field_name: str, min_age: int = 0, max_age: int = 120) -> ValidationRule:
    """Create a standard age validation rule"""
    return ValidationRule(
        name=f"{field_name}_age_range",
        rule_type=RuleType.NUMERIC_RANGE,
        field=field_name,
        parameters={"min": min_age, "max": max_age},
        severity=ValidationSeverity.WARNING
    )

# Usage
rules = [
    create_email_rule("email"),
    create_email_rule("backup_email"),
    create_age_rule("age", 18, 65)
]
```

### Integration with Pandas

```python
import pandas as pd
from src.policy_dq.engine import ValidationEngine

def validate_dataframe(df: pd.DataFrame, rules_file: str) -> ValidationReport:
    """Validate a pandas DataFrame"""
    # Convert DataFrame to list of dictionaries
    data = df.to_dict('records')
    
    # Load rules
    from src.policy_dq.rules.file_loader import FileRuleLoader
    loader = FileRuleLoader()
    rules = loader.load_rules(rules_file)
    
    # Validate
    from src.policy_dq.validators.core import DataValidator
    validator = DataValidator(rules)
    return validator.validate(data)

# Usage
df = pd.read_csv("data.csv")
report = validate_dataframe(df, "rules.yaml")
print(f"Validation complete: {report.success_rate:.1f}% success rate")
```

## Type Hints

The API is fully typed. Import types for better IDE support:

```python
from typing import List, Dict, Any, Optional
from src.policy_dq.models import (
    ValidationRule,
    ValidationResult,
    ValidationReport,
    ValidationSeverity,
    RuleType
)
from src.policy_dq.config import ValidationConfig
from src.policy_dq.engine import ValidationEngine
```

## Performance Considerations

- **Large Files**: For files > 100MB, consider processing in chunks
- **Memory Usage**: The system loads entire datasets into memory
- **Rule Optimization**: Uniqueness rules require full dataset scanning
- **Caching**: Rule loading results are cached for repeated validations

```python
# Example: Chunked processing for large files
def validate_large_file(file_path: str, rules_file: str, chunk_size: int = 10000):
    """Validate large files in chunks"""
    import pandas as pd
    
    all_results = []
    chunk_reports = []
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        chunk_data = chunk.to_dict('records')
        report = validate_dataframe_data(chunk_data, rules_file)
        chunk_reports.append(report)
    
    # Combine results
    return combine_reports(chunk_reports)
```