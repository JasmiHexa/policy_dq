---
inclusion: always
---

# Quality Steering

## Code Quality Standards

### Error Handling
- **Explicit Exceptions**: Use specific exception types, not generic Exception
- **Error Context**: Include relevant context in error messages (file paths, line numbers, field names)
- **User-Friendly Messages**: CLI errors should provide actionable suggestions
- **Logging**: Log errors at appropriate levels with structured information
- **Graceful Degradation**: Handle partial failures gracefully when possible

### Performance Requirements
- **Memory Efficiency**: Process large files (100MB+) without loading entire content into memory
- **Streaming**: Use streaming parsers for CSV and JSON when file size exceeds 50MB
- **Lazy Loading**: Load rules and configuration only when needed
- **Caching**: Cache parsed rules and compiled regex patterns
- **Progress Indicators**: Show progress for operations taking >2 seconds

### Security Considerations
- **Input Validation**: Validate all external inputs (file paths, rule definitions, configuration)
- **Path Traversal**: Prevent directory traversal attacks in file operations
- **Resource Limits**: Implement limits on file size, memory usage, and processing time
- **Sanitization**: Sanitize user inputs in error messages and reports
- **Dependencies**: Regularly audit and update dependencies for security vulnerabilities

## Testing Quality

### Coverage Requirements
- **Minimum Coverage**: 90% line coverage across all modules
- **Critical Paths**: 100% coverage for error handling and security-related code
- **Edge Cases**: Test boundary conditions, empty inputs, and malformed data
- **Integration**: Test all public API endpoints and CLI commands
- **Performance**: Include performance regression tests for large datasets

### Test Quality Standards
- **Independence**: Each test must be completely independent
- **Deterministic**: Tests must produce consistent results across runs
- **Fast Execution**: Unit tests should complete in <100ms each
- **Clear Assertions**: Use descriptive assertion messages
- **Realistic Data**: Use representative test data, not minimal examples

### Test Categories
```python
# Unit Tests - Fast, isolated, no external dependencies
def test_validation_rule_parsing():
    """Test rule parsing logic in isolation."""

# Integration Tests - Test component interactions
def test_csv_parser_with_validation_engine():
    """Test CSV parser integration with validation engine."""

# End-to-End Tests - Full workflow testing
def test_cli_validate_command_complete_workflow():
    """Test complete CLI validation workflow."""

# Performance Tests - Validate performance requirements
def test_large_file_processing_performance():
    """Ensure large files process within time limits."""
```

## Documentation Quality

### Code Documentation
- **Docstrings**: All public functions, classes, and modules must have comprehensive docstrings
- **Type Information**: Include parameter and return types in docstrings
- **Examples**: Provide usage examples for complex functions
- **Error Conditions**: Document what exceptions can be raised and when

### API Documentation
- **Complete Coverage**: Document all public APIs with examples
- **Error Responses**: Document all possible error conditions and responses
- **Configuration**: Provide complete configuration reference
- **Migration Guides**: Document breaking changes and migration paths

### User Documentation
- **Getting Started**: Clear installation and basic usage instructions
- **Examples**: Real-world examples for common use cases
- **Troubleshooting**: Common issues and solutions
- **CLI Reference**: Complete command-line interface documentation

## Validation Quality

### Rule Definition Quality
- **Comprehensive**: Cover all common data validation scenarios
- **Extensible**: Design allows easy addition of new validation types
- **Composable**: Rules can be combined and nested logically
- **Performance**: Rules execute efficiently on large datasets
- **Clear Semantics**: Rule behavior is unambiguous and well-documented

### Report Quality
- **Actionable**: Reports provide specific, actionable information about failures
- **Structured**: Consistent format across all report types (JSON, Markdown, console)
- **Filterable**: Support filtering by severity, field, rule type
- **Summarizable**: Provide high-level summaries and detailed breakdowns
- **Machine Readable**: JSON reports suitable for automated processing

### Error Message Quality
```python
# Good: Specific, actionable error message
"Email validation failed for field 'customer_email' in row 42: 'invalid-email' does not match required pattern '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'"

# Bad: Vague, unhelpful error message
"Validation failed"
```

## Maintenance Quality

### Code Maintainability
- **Single Responsibility**: Each class and function has one clear purpose
- **Loose Coupling**: Minimize dependencies between modules
- **High Cohesion**: Related functionality grouped together
- **Consistent Patterns**: Use consistent patterns across the codebase
- **Refactoring**: Regular refactoring to improve code quality

### Dependency Management
- **Minimal Dependencies**: Only include necessary external dependencies
- **Version Pinning**: Pin dependency versions for reproducible builds
- **Security Updates**: Regular updates for security vulnerabilities
- **License Compatibility**: Ensure all dependencies have compatible licenses
- **Deprecation Handling**: Plan for deprecated dependency replacement

### Monitoring and Observability
- **Structured Logging**: Use structured logging with consistent format
- **Metrics**: Track key performance and usage metrics
- **Health Checks**: Implement health check endpoints for service monitoring
- **Error Tracking**: Comprehensive error tracking and alerting
- **Performance Monitoring**: Monitor performance trends and regressions