---
inclusion: always
---

# Project Structure Steering

## Folder Structure

### Source Code Organization
```
src/policy_dq/
├── __init__.py              # Package initialization and version
├── models.py                # Core data models and types
├── api/                     # Public API layer
│   ├── __init__.py
│   ├── engine.py           # Main validation engine
│   ├── config.py           # Configuration management
│   ├── exceptions.py       # API-specific exceptions
│   └── utils.py            # API utility functions
├── cli/                     # Command-line interface
│   ├── __init__.py
│   └── main.py             # CLI commands and entry points
├── parsers/                 # Data file parsers
│   ├── __init__.py
│   ├── base.py             # Abstract parser interface
│   ├── csv_parser.py       # CSV file parsing
│   ├── json_parser.py      # JSON file parsing
│   └── factory.py          # Parser factory
├── validators/              # Validation logic
│   ├── __init__.py
│   ├── core.py             # Core validation engine
│   └── processors/         # Individual validation processors
│       ├── __init__.py
│       ├── base.py         # Base processor interface
│       ├── required_field.py
│       ├── type_check.py
│       ├── regex.py
│       ├── numeric_range.py
│       ├── uniqueness.py
│       └── cross_field.py
├── rules/                   # Rule management
│   ├── __init__.py
│   ├── base.py             # Rule base classes
│   ├── file_loader.py      # File-based rule loading
│   └── manager.py          # Rule management coordination
├── reporters/               # Report generation
│   ├── __init__.py
│   ├── console.py          # Console output reporter
│   ├── json_reporter.py    # JSON report generation
│   └── markdown.py         # Markdown report generation
└── mcp/                     # MCP integration
    ├── __init__.py
    ├── client.py           # MCP client implementation
    └── rule_loader.py      # MCP-based rule loading
```

### Test Structure
```
tests/
├── __init__.py
├── conftest.py             # Shared pytest fixtures
├── test_models.py          # Core model tests
├── test_api/               # API layer tests
├── test_cli/               # CLI tests
├── test_parsers/           # Parser tests
├── test_validators/        # Validation tests
├── test_rules/             # Rule management tests
├── test_reporters/         # Reporter tests
├── test_mcp/               # MCP integration tests
└── test_integration/       # End-to-end integration tests
```

## Module Boundaries

### API Layer (`api/`)
- **Purpose**: Public interface for programmatic usage
- **Dependencies**: Can import from all other modules except CLI
- **Exports**: Main classes and functions for external use
- **Restrictions**: No CLI-specific code, no direct file I/O

### CLI Layer (`cli/`)
- **Purpose**: Command-line interface implementation
- **Dependencies**: Only imports from API layer
- **Exports**: CLI commands and entry points
- **Restrictions**: No business logic, delegates to API layer

### Core Logic Modules
- **Parsers**: Handle file format parsing, no validation logic
- **Validators**: Pure validation logic, no I/O or reporting
- **Rules**: Rule definition and loading, no validation execution
- **Reporters**: Output formatting, no validation logic

### Integration Modules
- **MCP**: External service integration, isolated from core logic
- **Models**: Shared data structures, no business logic

## Naming Rules

### File and Directory Names
- **Snake Case**: All file and directory names use snake_case
- **Descriptive**: Names should clearly indicate purpose (e.g., `json_parser.py`, not `json.py`)
- **Consistent Suffixes**: Use consistent suffixes for similar functionality
  - `*_parser.py` for parsers
  - `*_reporter.py` for reporters
  - `test_*.py` for test files

### Class Names
- **PascalCase**: All class names use PascalCase
- **Descriptive**: Names should indicate purpose and type
  - `ValidationEngine` not `Engine`
  - `CSVParser` not `CSV`
  - `JSONReporter` not `JSON`

### Function and Variable Names
- **Snake Case**: All functions and variables use snake_case
- **Verb-Noun**: Functions should start with verbs (`validate_file`, `load_rules`)
- **Clear Intent**: Names should indicate what the function does or what the variable contains

### Constants
- **UPPER_SNAKE_CASE**: All constants use UPPER_SNAKE_CASE
- **Module Level**: Define constants at module level when possible
- **Grouped**: Related constants should be grouped together

### Private Members
- **Single Underscore**: Use single underscore prefix for internal use (`_internal_method`)
- **Double Underscore**: Use double underscore only for name mangling when necessary
- **Consistent**: Apply privacy conventions consistently within modules

## Test Layout Expectations

### Test File Organization
- **Mirror Structure**: Test directory structure mirrors source structure
- **One-to-One**: Each source module has a corresponding test module
- **Integration Tests**: Separate directory for cross-module integration tests

### Test Class Organization
```python
class TestClassName:
    """Test class for ClassName functionality."""
    
    def test_method_name_success_case(self):
        """Test successful execution of method_name."""
        
    def test_method_name_error_case(self):
        """Test error handling in method_name."""
        
    def test_method_name_edge_case(self):
        """Test edge cases for method_name."""
```

### Test Naming Conventions
- **Descriptive**: Test names should describe what is being tested
- **Pattern**: `test_[method]_[scenario]_[expected_result]`
- **Examples**: 
  - `test_validate_file_with_valid_csv_returns_success`
  - `test_parse_json_with_invalid_format_raises_error`

### Fixture Organization
- **Shared Fixtures**: Common fixtures in `conftest.py`
- **Module Fixtures**: Module-specific fixtures in test files
- **Scope**: Use appropriate fixture scope (function, class, module, session)
- **Cleanup**: Ensure fixtures clean up resources properly

### Test Data Management
- **Sample Data**: Store test data in `tests/data/` directory
- **Factories**: Use factory functions for creating test objects
- **Isolation**: Each test should be independent and not rely on other tests
- **Realistic**: Test data should represent realistic use cases