---
inclusion: always
---

# Product Steering

## Product Purpose

Policy Data Quality (policy-dq) is a comprehensive data validation system designed to validate structured data files (CSV and JSON) against configurable business and data-quality policies. The system provides flexible rule loading from local files or MCP (Model Context Protocol) sources and generates detailed reports in multiple formats.

## Target User

- **Data Engineers**: Validating data pipelines and ETL processes
- **Data Analysts**: Ensuring data quality before analysis
- **DevOps Engineers**: Integrating data validation into CI/CD pipelines
- **Business Analysts**: Validating business rule compliance in datasets
- **Quality Assurance Teams**: Automated data quality testing

## Primary Use Cases

1. **Data Pipeline Validation**: Validate incoming data files against business rules before processing
2. **ETL Quality Gates**: Ensure data quality at each stage of transformation pipelines
3. **Compliance Checking**: Verify data meets regulatory and business policy requirements
4. **Automated Testing**: Include data validation as part of automated test suites
5. **Data Monitoring**: Continuous monitoring of data quality in production systems

## Success Criteria

### Functional Success
- Successfully validate CSV and JSON files with configurable rules
- Generate comprehensive reports in JSON, Markdown, and console formats
- Support both local file-based rules and MCP-sourced rules
- Provide clear, actionable error messages for validation failures
- Handle large datasets efficiently (>100k records)

### Quality Success
- 95%+ test coverage across all modules
- Zero critical security vulnerabilities
- Sub-second validation for files under 10MB
- Memory usage scales linearly with file size
- CLI exit codes properly indicate validation status

### User Experience Success
- Intuitive CLI interface with helpful error messages
- Comprehensive documentation with examples
- Easy integration into existing workflows
- Clear separation between validation logic and reporting
- Extensible architecture for custom validation rules

### Integration Success
- Seamless MCP integration for remote rule sources
- Compatible with common CI/CD platforms
- Easy installation via pip/poetry
- Docker container support for containerized environments
- API suitable for programmatic usage