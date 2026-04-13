# Kiro Hooks for Policy Data Quality

This directory contains Kiro hooks that automate quality checks, security enforcement, and development workflow assistance for the Policy Data Quality project.

## Available Hooks

### 1. Test After Task Completion (`test-after-task.json`)
**Purpose**: Automatically run tests after completing implementation tasks to ensure code quality.

**Triggers**: When tasks containing "implement", "create", "add", "fix", or "update" are completed and Python files in `src/` are modified.

**Actions**:
- Runs full test suite with verbose output
- Checks code coverage and enforces 90% minimum threshold
- Provides clear feedback on test failures

**Benefits**: Catches regressions immediately and ensures new code meets quality standards.

### 2. Code Quality Lint Check (`lint-check.json`)
**Purpose**: Maintain consistent code quality and formatting standards.

**Triggers**: When Python files are saved (excluding cache and compiled files).

**Actions**:
- Runs Ruff linter with auto-fix for common issues
- Checks code formatting with Black
- Performs static type checking with MyPy in strict mode

**Benefits**: Prevents code quality issues from accumulating and maintains consistent style.

### 3. Security and Safety Check (`security-check.json`)
**Purpose**: Block potentially dangerous shell commands to prevent accidental system damage.

**Triggers**: When potentially dangerous commands are executed (rm -rf, sudo rm, chmod 777, etc.).

**Actions**:
- Blocks execution of dangerous commands
- Provides security warnings and safer alternatives
- Logs security incidents for review

**Benefits**: Prevents accidental data loss and security vulnerabilities.

### 4. Test Coverage Reminder (`test-coverage-reminder.json`)
**Purpose**: Encourage comprehensive test coverage for new code.

**Triggers**: When new Python modules are created (excluding test files and __init__.py).

**Actions**:
- Checks if corresponding test files exist
- Analyzes code complexity (number of public functions/classes)
- Provides reminders and suggestions for test creation

**Benefits**: Maintains high test coverage and prevents untested code accumulation.

### 5. Documentation Quality Check (`documentation-check.json`)
**Purpose**: Ensure code is properly documented with comprehensive docstrings.

**Triggers**: When Python source files in `src/` are saved.

**Actions**:
- Checks for missing docstrings on public functions and classes
- Identifies TODO and FIXME comments for follow-up
- Provides documentation improvement suggestions

**Benefits**: Maintains code documentation quality and identifies technical debt.

## Hook Configuration

### Auto-Approval Settings
- **Security hooks**: Always require manual approval for safety
- **Lint checks**: Auto-approved for faster development workflow
- **Test reminders**: Require approval to ensure developer awareness

### Environment-Specific Behavior
- **Development**: All hooks enabled with helpful reminders
- **CI/CD**: All hooks enabled with failure enforcement
- **Production**: Security hooks only for safety

## Usage Guidelines

### Enabling/Disabling Hooks
Hooks can be enabled or disabled by modifying the `enabled` field in each hook file or through the Kiro interface.

### Customizing Hook Behavior
- Modify trigger conditions to change when hooks activate
- Adjust timeout values for different system performance
- Update severity levels based on team preferences

### Adding New Hooks
1. Create a new JSON file in this directory
2. Follow the existing hook structure and naming conventions
3. Test the hook thoroughly before enabling in production
4. Update this README with hook documentation

## Troubleshooting

### Common Issues
- **Hook timeouts**: Increase timeout values for slower systems
- **False positives**: Adjust trigger conditions or exclude patterns
- **Performance impact**: Consider disabling resource-intensive hooks during heavy development

### Hook Debugging
- Check hook execution logs in Kiro interface
- Verify command paths and working directories
- Test hook commands manually to isolate issues

## Best Practices

1. **Keep hooks focused**: Each hook should have a single, clear purpose
2. **Provide helpful feedback**: Include actionable suggestions in hook messages
3. **Consider performance**: Avoid hooks that significantly slow development
4. **Test thoroughly**: Verify hooks work correctly before team deployment
5. **Document changes**: Update this README when modifying hooks