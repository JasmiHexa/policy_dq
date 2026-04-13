---
inclusion: always
---

# Technical Steering

## Python Version

- **Target Version**: Python 3.9+
- **Rationale**: Provides modern type hints, dataclasses, and async features while maintaining compatibility with most production environments
- **Testing**: All code must be tested against Python 3.9, 3.10, 3.11, and 3.12

## Package and Tooling Choices

### Dependency Management
- **Poetry**: Primary dependency management and packaging tool
- **Requirements**: Keep dependencies minimal and well-justified
- **Version Pinning**: Use semantic versioning constraints (^1.0.0) for flexibility

### Core Dependencies
- **Click**: CLI framework for user-friendly command-line interface
- **Pydantic**: Data validation and settings management with type safety
- **PyYAML**: YAML parsing for configuration files
- **Rich**: Enhanced console output and progress indicators

### Development Dependencies
- **pytest**: Primary testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities for tests
- **black**: Code formatting
- **ruff**: Fast linting and import sorting
- **mypy**: Static type checking

## Linting and Formatting Tools

### Code Formatting
- **Black**: Automatic code formatting with default settings
- **Line Length**: 88 characters (Black default)
- **String Quotes**: Double quotes preferred
- **Import Sorting**: Handled by ruff

### Linting
- **Ruff**: Primary linter replacing flake8, isort, and other tools
- **Configuration**: Defined in pyproject.toml
- **Rules**: Enable most rules except overly pedantic ones
- **Ignore**: E501 (line length handled by black), W503 (line break before binary operator)

### Pre-commit Hooks
- Black formatting
- Ruff linting
- MyPy type checking
- Trailing whitespace removal
- End-of-file fixing

## Testing Tools

### Framework
- **pytest**: Primary testing framework
- **Test Discovery**: Automatic discovery of test_*.py files
- **Fixtures**: Use pytest fixtures for test setup and teardown
- **Parametrization**: Use pytest.mark.parametrize for multiple test cases

### Coverage
- **Target**: Minimum 90% code coverage
- **Reporting**: Generate both terminal and HTML coverage reports
- **Exclusions**: Only exclude truly untestable code (defensive assertions, etc.)

### Test Categories
- **Unit Tests**: Fast, isolated tests for individual functions/classes
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Full CLI and API workflow tests
- **Performance Tests**: Validate performance requirements

### Mocking
- **pytest-mock**: Preferred mocking library
- **Strategy**: Mock external dependencies (file I/O, network calls)
- **Avoid**: Over-mocking internal logic

## Typing Expectations

### Type Annotations
- **Required**: All public functions and methods must have type annotations
- **Return Types**: Always specify return types, including None
- **Complex Types**: Use Union, Optional, List, Dict from typing module
- **Generics**: Use TypeVar for generic functions when appropriate

### MyPy Configuration
- **Strict Mode**: Enable strict mode for maximum type safety
- **No Implicit Optional**: Require explicit Optional[] for nullable types
- **Warn Unused Ignores**: Prevent accumulation of unnecessary type: ignore comments
- **Check Untyped Defs**: Require type annotations on all function definitions

### Type Checking Standards
- **Zero MyPy Errors**: All code must pass MyPy strict checking
- **Type Stubs**: Create .pyi files for complex external libraries if needed
- **Runtime Validation**: Use Pydantic for runtime type validation where appropriate

### Documentation Types
- **Docstrings**: Include type information in docstrings for complex types
- **Examples**: Provide type examples in docstrings for non-obvious types
- **Protocols**: Use typing.Protocol for structural typing when appropriate