# GitHub Actions CI/CD Setup

## Overview

This project now includes a comprehensive GitHub Actions workflow that automatically runs on every push and pull request to ensure code quality and functionality.

## Workflow Components

### 🧪 **Test Pipeline** 
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing  
- **E2E Tests**: Complete user workflow testing
- **Coverage Reports**: Code coverage analysis with Codecov integration

### 🔍 **Code Quality Pipeline**
- **Ruff**: Fast Python linting
- **Black**: Code formatting validation
- **MyPy**: Optional type checking

### 🔒 **Security Pipeline**
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking

## Running Tests Locally

### Quick Test Commands
```bash
# Run all tests
uv run pytest

# Run only unit tests
uv run pytest tests/unit/ -m unit

# Run with coverage
uv run pytest --cov=. --cov-report=term-missing

# Run specific test categories
uv run pytest -m "not slow"  # Skip slow tests
uv run pytest -m integration  # Only integration tests
```

### Test Categories
- `@pytest.mark.unit` - Fast, isolated component tests
- `@pytest.mark.integration` - Component interaction tests
- `@pytest.mark.e2e` - Complete workflow tests
- `@pytest.mark.slow` - Tests that take longer to run

## Environment Variables

For local testing and CI/CD, these environment variables are used:

### Required for Full Testing
```bash
TESTING=true  # Enables test mode
```

### Optional (CI will use placeholders if missing)
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TODOIST_TOKEN=your_todoist_token
```

## GitHub Secrets Setup

For the CI to work with external APIs, add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:
   - `TELEGRAM_BOT_TOKEN` (optional - will use placeholder if missing)
   - `TODOIST_TOKEN` (optional - will use placeholder if missing)

## Workflow Triggers

The CI runs on:
- **Push** to `master`, `main`, or `develop` branches
- **Pull requests** to `master` or `main` branches

## Matrix Testing

Tests run on multiple Python versions:
- Python 3.11
- Python 3.12

## Coverage Reporting

- Coverage reports are automatically uploaded to [Codecov](https://codecov.io)
- Minimum coverage thresholds can be configured
- Coverage reports are also available in the GitHub Actions logs

## Adding New Tests

1. **Unit Tests**: Add to `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/`
3. **E2E Tests**: Add to `tests/e2e/`
4. **Mark your tests** with appropriate decorators:
   ```python
   @pytest.mark.unit
   class TestMyComponent:
       def test_functionality(self):
           pass
   ```

## Troubleshooting

### Local Test Failures
```bash
# Check test isolation
uv run pytest tests/unit/test_models.py -v

# Debug specific test
uv run pytest tests/unit/test_models.py::TestDatabaseModels::test_tag_creation -v -s
```

### CI Failures
- Check the GitHub Actions tab in your repository
- Look for specific error messages in the logs
- Ensure all dependencies are properly specified in `pyproject.toml`

## Configuration Files

- **Test Config**: `pyproject.toml` (replaces `pytest.ini`)
- **Coverage Config**: `pyproject.toml` (replaces `.coveragerc`)
- **CI Workflow**: `.github/workflows/test.yml`

The setup is now **production-ready** and will help maintain code quality as your project grows! 🚀
