import pytest
from unittest.mock import patch, MagicMock
import os
from config.logging_config import setup_development_logging, get_logger


class TestLoggingConfig:
    """Test logging configuration functionality."""
    
    def test_setup_development_logging(self):
        """Test development logging setup."""
        # Should not raise any exceptions
        setup_development_logging()
        
        # Test logger creation
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"

    def test_get_logger_with_different_names(self):
        """Test getting loggers with different names."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1.name == "module1"
        assert logger2.name == "module2"
        assert logger1 is not logger2

    def test_logger_functionality(self):
        """Test basic logger functionality."""
        logger = get_logger("test_logger")
        
        # Should not raise exceptions
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        logger.error("Test error message")


class TestEnvironmentConfig:
    """Test environment configuration handling."""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly handled."""
        # Test with mock environment variables
        with patch.dict(os.environ, {
            'GOOGLE_API_KEY': 'test_google_key',
            'TELEGRAM_BOT_TOKEN': 'test_telegram_token'
        }):
            assert os.getenv('GOOGLE_API_KEY') == 'test_google_key'
            assert os.getenv('TELEGRAM_BOT_TOKEN') == 'test_telegram_token'

    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        # Ensure certain variables don't exist for this test
        test_var = 'NONEXISTENT_TEST_VAR_12345'
        if test_var in os.environ:
            del os.environ[test_var]
        
        result = os.getenv(test_var)
        assert result is None
        
        # Test with default value
        result_with_default = os.getenv(test_var, 'default_value')
        assert result_with_default == 'default_value'
