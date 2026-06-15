#!/usr/bin/env python3
"""
Logging Configuration Module
Sets up consistent logging for the application
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = 'INFO',
    log_file: Optional[str] = 'replay_processor.log',
    console_output: bool = True
) -> None:
    """
    Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file or None to disable file logging
        console_output: Whether to output logs to console
    """
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Format for log messages
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        try:
            # Create directory if needed
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5  # Keep 5 backup files
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not create log file: {e}")
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized (level: {log_level})")
