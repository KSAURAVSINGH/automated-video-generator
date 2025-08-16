"""
Centralized logging configuration for the Automated Video Generator.
"""

import logging
import logging.handlers
from pathlib import Path
from .settings import LOG_LEVEL, LOG_FILE

def setup_logging(name: str = None, level: str = None) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        name: Logger name (defaults to root logger)
        level: Logging level (defaults to LOG_LEVEL from settings)
    
    Returns:
        Configured logger instance
    """
    # Get logger
    logger = logging.getLogger(name)
    
    # Set level
    log_level = getattr(logging, level or LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    if LOG_FILE:
        # Ensure log directory exists
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = LOG_FILE.parent / 'error.log' if LOG_FILE else None
    if error_log_file:
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        logger.addHandler(error_handler)
    
    return logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (defaults to root logger)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

# Set up root logger
root_logger = setup_logging()
