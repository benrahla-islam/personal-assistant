# Testing Guide

## Running Tests

To run the tests in this project, use the following command:

```bash
# From the project root directory
PYTHONPATH=. uv run pytest tests/test_tools.py -v
```

Or if you prefer using pytest directly:

```bash
# Ensure you're in the project root and have the virtual environment activated
pytest tests/test_tools.py -v
```

## Test Structure

The test file `tests/test_tools.py` contains comprehensive tests for all tools in the `agent/tools/` directory:

### TestTaskScheduler
- Tests task scheduling functionality
- Tests datetime validation
- Tests task listing and cancellation
- Includes proper setup/teardown for clean state

### TestTelegramScraper  
- Tests message fetching with proper mocking
- Tests error handling scenarios
- Tests client start failures

### TestExtraTools
- Tests web search functionality
- Tests Wikipedia search functionality
- Tests exception handling

## Test Configuration

- `pytest.ini` - Contains pytest configuration including Python path setup
- Tests use mocking to avoid external API calls during testing
- Environment variables are mocked for security

## Test Coverage

The tests cover:
- ✅ Task scheduling and validation
- ✅ Task listing and cancellation  
- ✅ Telegram message fetching
- ✅ Web and Wikipedia search
- ✅ Error handling and edge cases
- ✅ Proper mocking of external dependencies

## Known Issues

- Some deprecation warnings from Pydantic V1 syntax (to be fixed in tools)
- RuntimeWarning for async coroutines in telegram tests (cosmetic only)
