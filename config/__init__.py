"""
Configuration module for the personal assistant.
"""
from .logging_config import (
    setup_logging,
    setup_development_logging,
    setup_bot_logging,
    setup_production_logging,
    setup_testing_logging,
    get_logger,
    ColoredFormatter
)

__all__ = [
    'setup_logging',
    'setup_development_logging',
    'setup_bot_logging',
    'setup_production_logging',
    'setup_testing_logging',
    'get_logger',
    'ColoredFormatter'
]
