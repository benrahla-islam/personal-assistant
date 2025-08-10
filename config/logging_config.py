"""
Centralized logging configuration with colored output.
"""
import logging
import sys
from typing import Dict, Any


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    
    RESET = '\033[0m'  # Reset color
    BOLD = '\033[1m'   # Bold text
    
    def __init__(self, format_string: str = None, use_colors: bool = True):
        """
        Initialize the colored formatter.
        
        Args:
            format_string: Custom format string for log messages
            use_colors: Whether to use colors (disable for file logging)
        """
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        super().__init__(format_string)
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors."""
        if not self.use_colors:
            return super().format(record)
        
        # Get the base formatted message
        formatted_message = super().format(record)
        
        # Get color for this log level
        level_color = self.COLORS.get(record.levelname, '')
        
        # Apply color to the entire message
        if level_color:
            # Make the log level bold and colored
            level_name = f"{self.BOLD}{level_color}{record.levelname}{self.RESET}"
            # Replace the levelname in the formatted message
            colored_message = formatted_message.replace(
                record.levelname, 
                level_name
            )
            return colored_message
        
        return formatted_message


import threading

# Global lock for thread-safe logging setup
_logging_setup_lock = threading.Lock()
_logging_is_configured = False

def setup_logging(
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: str = "app.log",
    use_colors: bool = True,
    format_string: str = None
) -> None:
    """
    Set up centralized logging configuration with colors.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to also log to a file
        log_file_path: Path to the log file
        use_colors: Whether to use colored output for console
        format_string: Custom format string
    """
    global _logging_is_configured
    with _logging_setup_lock:
        if _logging_is_configured:
            return  # Already configured, skip reconfiguration

        # Convert string level to logging constant
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Default format
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        
        # Use colored formatter for console if colors are enabled
        console_formatter = ColoredFormatter(format_string, use_colors=use_colors)
        console_handler.setFormatter(console_formatter)
        
        # Add console handler
        root_logger.addHandler(console_handler)
        
        # File handler (without colors)
        if log_to_file:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(log_level)
            
            # Use plain formatter for file (no colors)
            file_formatter = ColoredFormatter(format_string, use_colors=False)
            file_handler.setFormatter(file_formatter)
            
            root_logger.addHandler(file_handler)
        
        # Set root logger level
        root_logger.setLevel(log_level)
        _logging_is_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Name for the logger (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Pre-configured setups for different environments
def setup_development_logging():
    """Set up logging for development environment."""
    setup_logging(
        level="DEBUG",
        log_to_file=True,
        log_file_path="development.log",
        use_colors=True
    )


def setup_production_logging():
    """Set up logging for production environment."""
    setup_logging(
        level="INFO",
        log_to_file=True,
        log_file_path="production.log",
        use_colors=False  # Disable colors in production for cleaner logs
    )


def setup_testing_logging():
    """Set up logging for testing environment."""
    setup_logging(
        level="WARNING",
        log_to_file=False,
        use_colors=True
    )


# Example usage and testing
if __name__ == "__main__":
    # Set up colored logging
    setup_development_logging()
    
    # Test all log levels
    logger = get_logger(__name__)
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("\nTesting without colors:")
    # Preserve previous settings but disable colors
    setup_logging(
        level="DEBUG",
        log_to_file=True,
        log_file_path="development.log",
        use_colors=False
    )
    
    logger = get_logger(__name__)
    logger.debug("This is a DEBUG message without colors")
    logger.info("This is an INFO message without colors")
    logger.warning("This is a WARNING message without colors")
    logger.error("This is an ERROR message without colors")
    logger.critical("This is a CRITICAL message without colors")
