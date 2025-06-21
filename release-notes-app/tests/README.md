# Test Organization

This directory contains tests for the Release Notes Generator application, organized by test type and purpose.

## Directory Structure

```
tests/
├── __init__.py                          # Package initialization
├── test_refactored_app.py              # Unit tests (pytest framework)
├── integration/                         # Integration tests
│   ├── __init__.py
│   └── test_orchestration.py           # Azure Functions integration tests
└── manual/                             # Manual test scripts
    ├── __init__.py
    └── test_enhanced_logging.py        # Enhanced logging verification
```

## Test Types

### Unit Tests (`test_refactored_app.py`)
- **Framework**: pytest
- **Purpose**: Test individual components and functions
- **Coverage**: Data models, parsing service, configuration, validation
- **Run with**: `python -m pytest tests/test_refactored_app.py -v`
- **Status**: ✅ 17 tests, all passing

### Integration Tests (`integration/`)
- **Framework**: Direct HTTP requests + pytest compatible
- **Purpose**: Test complete Azure Functions workflows
- **Coverage**: HTTP triggers, orchestration flow, durable functions
- **Run with**: 
  - Direct: `python tests/integration/test_orchestration.py`
  - Pytest: `python -m pytest tests/integration/test_orchestration.py -v`
- **Requirements**: Azure Functions host running on http://localhost:7071

### Manual Tests (`manual/`)
- **Framework**: Direct Python scripts
- **Purpose**: Development verification and debugging
- **Coverage**: Enhanced logging, service integration, authentication
- **Run with**: `python tests/manual/test_enhanced_logging.py`
- **Requirements**: Azure CLI authentication, environment variables

## Running All Tests

### Quick Test (Unit Only)
```bash
python -m pytest tests/test_refactored_app.py -v
```

### Full Test Suite (Unit + Integration)
```bash
# Start Azure Functions host first
func host start

# In another terminal
python -m pytest tests/ -v
```

### Manual Verification
```bash
python tests/manual/test_enhanced_logging.py
```

## Test Requirements

- **Python 3.9+**
- **pytest** (for unit and integration tests)
- **requests** (for integration tests)
- **Azure Functions Core Tools** (for integration tests)
- **Azure CLI** (for manual tests with authentication)

## Test Data

All tests use standardized test payloads that match the expected Azure DevOps work item format:
- Work Item ID: 4349057
- Type: Task
- Includes Title, AreaPath, Comments fields
- Tests both single and bulk processing modes
