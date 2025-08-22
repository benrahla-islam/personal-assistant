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

The test suite contains comprehensive tests for all components:

### Core Component Tests

#### TestTaskScheduler (`tests/test_tools.py`)
- Tests task scheduling functionality
- Tests datetime validation
- Tests task listing and cancellation
- Includes proper setup/teardown for clean state

#### TestTelegramScraper (`tests/test_tools.py`)  
- Tests message fetching with proper mocking
- Tests error handling scenarios
- Tests client start failures

#### TestExtraTools (`tests/test_tools.py`)
- Tests web search functionality
- Tests Wikipedia search functionality
- Tests exception handling

### Main Agent Tests (`tests/test_main_agent.py`)
- Tests agent executor initialization and configuration
- Tests tool loading and availability
- Tests conversation memory functionality
- Tests custom JSON parser
- Tests tool registry functionality
- Tests agent integration with different tools

### Configuration Tests (`tests/test_config.py`)
- Tests logging configuration setup
- Tests environment variable handling
- Tests logger creation and functionality

### Telegram Components Tests (`tests/test_telegram_components.py`)
- Tests TelethonChannelCollector class
- Tests message retrieval and formatting
- Tests connection handling
- Tests telegram bot handlers (if implemented)

### Integration Tests (`tests/test_integration.py`)
- Tests complete end-to-end workflows
- Tests conversation memory across interactions
- Tests multi-tool workflows
- Tests error recovery and resilience
- Tests system behavior with edge cases

## Test Configuration

- `pytest.ini` - Contains pytest configuration including Python path setup
- Tests use mocking to avoid external API calls during testing
- Environment variables are mocked for security

## Test Coverage Summary

**Total Tests: 50 tests across 4 test files**

The comprehensive test suite now includes:

### ✅ **Core Tools Coverage (15 tests)**
- **Task Scheduler**: 7 tests covering scheduling, validation, listing, cancellation
- **Telegram Scraper**: 4 tests covering message fetching, error handling, client management  
- **Extra Tools**: 4 tests covering web search, Wikipedia search, exception handling

### ✅ **Main Agent Coverage (13 tests)**
- **Agent Executor**: Initialization, configuration, tool loading
- **Custom Parser**: JSON parsing, ReAct format, error handling
- **Tool Registry**: Category-based tool registration
- **Agent Integration**: Tool usage, memory, error handling

### ✅ **Configuration Coverage (5 tests)**
- **Logging**: Setup, logger creation, functionality
- **Environment**: Variable handling, missing variable management

### ✅ **Telegram Components Coverage (8 tests)**
- **TelethonChannelCollector**: Client management, message retrieval
- **Bot Handlers**: Import tests, module structure validation

### ✅ **Integration Coverage (9 tests)**
- **End-to-End Workflows**: Search, scheduling, memory, error recovery
- **System Resilience**: Invalid inputs, edge cases, long inputs

## Additional Tests Still Needed

### **High Priority (Recommended for Production)**

1. **Specialized Agents Tests** (if using sub_agents)
   - Test SpecializedAgent base class
   - Test ResearchAgent, PlanningAgent, etc.
   - Test agent delegation and context passing

2. **Performance Tests**
   - Response time benchmarks
   - Memory usage monitoring  
   - Concurrent request handling

3. **Security Tests**
   - Input sanitization validation
   - API key protection tests
   - Rate limiting tests

### **Medium Priority**

4. **Database/Persistence Tests** (if applicable)
   - Task persistence across restarts
   - Conversation history storage
   - Configuration persistence

5. **Real API Integration Tests** (optional)
   - End-to-end tests with real APIs (marked as integration)
   - Rate limiting behavior
   - Network failure recovery

6. **User Interface Tests** (if applicable)
   - Telegram bot UI interactions
   - Command handling
   - Error message formatting

## Running All Tests

To run the complete test suite:

```bash
# Run all tests
PYTHONPATH=. uv run pytest tests/ -v

# Run specific test files
PYTHONPATH=. uv run pytest tests/test_tools.py -v
PYTHONPATH=. uv run pytest tests/test_main_agent.py -v
PYTHONPATH=. uv run pytest tests/test_integration.py -v

# Run with coverage report
PYTHONPATH=. uv run pytest tests/ --cov=agent --cov-report=html
```

## Known Issues

- Some deprecation warnings from Pydantic V1 syntax (to be fixed in tools)
- RuntimeWarning for async coroutines in telegram tests (cosmetic only)
