# Design Document

## Overview

The data validation system is designed as a modular Python application that validates structured data files against configurable business and data-quality policies. The architecture follows a clean separation of concerns with distinct layers for CLI interface, business logic, data parsing, validation rules, and reporting.

The system supports multiple input formats (CSV, JSON), flexible rule loading (local files, MCP sources), comprehensive validation rule types, and multiple output formats (console, JSON, Markdown). It's built with Python 3.11+ using modern type hints and follows test-driven development practices.

## Architecture

The system follows a layered architecture pattern:

```
┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Python API     │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │   Business Logic     │
          │   (Orchestration)    │
          └──────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐    ┌───────▼────┐    ┌─────▼─────┐
│Parser │    │ Validator  │    │ Reporter  │
│Layer  │    │   Layer    │    │  Layer    │
└───────┘    └────────────┘    └───────────┘
                     │
              ┌──────▼──────┐
              │ Rules Layer │
              │ (Local/MCP) │
              └─────────────┘
```

## Components and Interfaces

### 1. Core Models (`models.py`)

```python
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union
from enum import Enum

class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class RuleType(Enum):
    REQUIRED_FIELD = "required_field"
    TYPE_CHECK = "type_check"
    REGEX_CHECK = "regex_check"
    NUMERIC_RANGE = "numeric_range"
    UNIQUENESS = "uniqueness"
    CROSS_FIELD = "cross_field"

@dataclass
class ValidationRule:
    name: str
    rule_type: RuleType
    field: str
    parameters: Dict[str, Any]
    severity: ValidationSeverity = ValidationSeverity.ERROR

@dataclass
class ValidationResult:
    rule_name: str
    field: str
    row_index: Optional[int]
    severity: ValidationSeverity
    message: str
    passed: bool

@dataclass
class ValidationReport:
    total_records: int
    total_rules: int
    passed_validations: int
    failed_validations: int
    results: List[ValidationResult]
    summary_by_severity: Dict[ValidationSeverity, int]
```

### 2. Parser Layer (`parsers/`)

**Base Parser Interface:**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class DataParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse data file and return list of records"""
        pass
    
    @abstractmethod
    def validate_format(self, file_path: str) -> bool:
        """Validate if file format is supported"""
        pass
```

**CSV Parser (`parsers/csv_parser.py`):**
- Uses Python's `csv` module
- Handles encoding detection
- Supports custom delimiters
- Provides row-level error handling

**JSON Parser (`parsers/json_parser.py`):**
- Supports both single objects and arrays
- Handles nested JSON structures
- Provides line-level error reporting

### 3. Rules Layer (`rules/`)

**Rule Loader Interface:**
```python
from abc import ABC, abstractmethod
from typing import List

class RuleLoader(ABC):
    @abstractmethod
    def load_rules(self, source: str) -> List[ValidationRule]:
        """Load validation rules from source"""
        pass
```

**Local File Loader (`rules/file_loader.py`):**
- Supports YAML and JSON rule files
- Schema validation for rule definitions
- Caching mechanism for performance

**MCP Loader (`rules/mcp_loader.py`):**
- Integrates with Model Context Protocol
- Handles authentication and connection management
- Provides fallback mechanisms

### 4. Validator Layer (`validators/`)

**Core Validator (`validators/core.py`):**
```python
class DataValidator:
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules
        self.rule_processors = self._initialize_processors()
    
    def validate(self, data: List[Dict[str, Any]]) -> ValidationReport:
        """Execute all validation rules against data"""
        pass
    
    def validate_record(self, record: Dict[str, Any], index: int) -> List[ValidationResult]:
        """Validate single record against all applicable rules"""
        pass
```

**Rule Processors (`validators/processors/`):**
- `RequiredFieldProcessor`: Validates field presence and non-empty values
- `TypeCheckProcessor`: Validates data types (string, int, float, bool, date)
- `RegexProcessor`: Validates pattern matching
- `NumericRangeProcessor`: Validates min/max constraints
- `UniquenessProcessor`: Tracks and validates unique values
- `CrossFieldProcessor`: Validates relationships between fields

### 5. Reporter Layer (`reporters/`)

**Base Reporter Interface:**
```python
from abc import ABC, abstractmethod

class Reporter(ABC):
    @abstractmethod
    def generate_report(self, report: ValidationReport, output_path: str) -> None:
        """Generate report in specific format"""
        pass
```

**Console Reporter (`reporters/console.py`):**
- Colored output using `colorama`
- Progress indicators
- Summary statistics

**JSON Reporter (`reporters/json_reporter.py`):**
- Structured JSON output
- Machine-readable format
- Includes metadata and timestamps

**Markdown Reporter (`reporters/markdown.py`):**
- Human-readable format
- Tables for results summary
- Detailed error listings

### 6. MCP Integration (`mcp/`)

**MCP Client (`mcp/client.py`):**
```python
class MCPClient:
    def __init__(self, server_config: Dict[str, Any]):
        self.config = server_config
        self.connection = None
    
    async def connect(self) -> None:
        """Establish MCP connection"""
        pass
    
    async def fetch_rules(self, rule_set_id: str) -> List[Dict[str, Any]]:
        """Fetch validation rules from MCP server"""
        pass
```

## Data Models

### Rule Configuration Schema

```yaml
# Example YAML rule configuration
version: "1.0"
rule_sets:
  - name: "customer_validation"
    rules:
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

### Validation Report Schema

```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "input_file": "customers.csv",
    "rules_source": "rules.yaml",
    "total_records": 1000,
    "total_rules": 8
  },
  "summary": {
    "passed_validations": 7850,
    "failed_validations": 150,
    "by_severity": {
      "critical": 5,
      "error": 45,
      "warning": 100,
      "info": 0
    }
  },
  "results": [
    {
      "rule_name": "email_format",
      "field": "email",
      "row_index": 42,
      "severity": "error",
      "message": "Email format invalid: 'invalid-email'",
      "passed": false
    }
  ]
}
```

## Error Handling

### Error Categories

1. **Input Errors:**
   - File not found
   - Unsupported file format
   - Malformed data files
   - Encoding issues

2. **Rule Loading Errors:**
   - Invalid rule configuration
   - MCP connection failures
   - Schema validation errors

3. **Validation Errors:**
   - Rule processing failures
   - Data type conversion errors
   - Cross-field validation conflicts

4. **Output Errors:**
   - Output directory permissions
   - Disk space issues
   - Report generation failures

### Error Handling Strategy

```python
class ValidationError(Exception):
    """Base exception for validation errors"""
    pass

class RuleLoadingError(ValidationError):
    """Raised when rules cannot be loaded"""
    pass

class DataParsingError(ValidationError):
    """Raised when data cannot be parsed"""
    pass

class ReportGenerationError(ValidationError):
    """Raised when reports cannot be generated"""
    pass
```

- Use structured logging with different levels (DEBUG, INFO, WARNING, ERROR)
- Implement graceful degradation for non-critical failures
- Provide detailed error messages with context and suggestions
- Support partial validation when some rules fail to load

## Testing Strategy

### Unit Testing

1. **Parser Tests:**
   - Valid and invalid CSV/JSON files
   - Edge cases (empty files, malformed data)
   - Encoding variations

2. **Validator Tests:**
   - Each rule type with valid/invalid data
   - Cross-field validation scenarios
   - Performance with large datasets

3. **Rule Loading Tests:**
   - Local file loading (YAML/JSON)
   - MCP integration mocking
   - Error handling scenarios

4. **Reporter Tests:**
   - Output format validation
   - File system operations
   - Content accuracy

### Integration Testing

1. **End-to-End Workflows:**
   - Complete validation pipeline
   - CLI command execution
   - API usage scenarios

2. **MCP Integration:**
   - Real MCP server connections
   - Authentication flows
   - Network failure handling

3. **Performance Testing:**
   - Large file processing
   - Memory usage validation
   - Concurrent validation scenarios

### Test Data Strategy

- Sample CSV files with various data quality issues
- JSON files with nested structures
- Rule configuration files for different scenarios
- Expected output files for comparison testing

### Test Organization Structure

The test suite follows a structured organization with separate directories for different test types:

```
tests/
├── __init__.py
├── conftest.py             # Shared pytest fixtures
├── unit/                   # Unit tests directory
│   ├── __init__.py
│   ├── test_models.py      # Core model tests
│   ├── test_api/           # API layer unit tests
│   ├── test_cli/           # CLI unit tests
│   ├── test_parsers/       # Parser unit tests
│   ├── test_validators/    # Validation unit tests
│   ├── test_rules/         # Rule management unit tests
│   ├── test_reporters/     # Reporter unit tests
│   └── test_mcp/           # MCP unit tests
└── integration/            # Integration tests directory
    ├── __init__.py
    ├── test_end_to_end.py  # Complete workflow tests
    ├── test_performance.py # Performance tests
    └── test_mcp_integration.py # MCP integration tests
```

### Testing Tools

- `pytest` for test framework
- `pytest-asyncio` for async MCP testing
- `pytest-mock` for mocking external dependencies
- `pytest-cov` for coverage reporting
- `hypothesis` for property-based testing of validation rules