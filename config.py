#!/usr/bin/env python3
"""
Configuration Management Module
Handles loading, saving, and managing application configuration from INI file
"""

import os
import configparser
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages application configuration with support for:
    - Loading/saving from config.ini
    - Default values
    - CLI argument overrides
    - Date filtering parameters
    """
    
    @staticmethod
    def _get_default_date_from():
        """Get default date_from (30 days ago)"""
        return (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    @staticmethod
    def _get_default_date_to():
        """Get default date_to (today)"""
        return datetime.now().strftime('%Y-%m-%d')
    
    # Default configuration values
    DEFAULTS = {
        'SETTINGS': {
            'input_folder': './input',
            'output_folder': './output',
            'parser_url': 'http://localhost:3000',
            'parser_dir': '',  # Optional path to the replay-parser node project (auto-detected if empty)
            'batch_size': '500',
            'parallel_threads': '8',
            'date_from': '',  # Will use last 30 days if empty
            'date_to': '',    # Will use today if empty
            'log_level': 'INFO',
            'dry_run': 'true',
            'skip_existing': 'true',
        }
    }
    
    def __init__(self, config_file: str = 'config.ini'):
        """
        Initialize ConfigManager
        
        Args:
            config_file: Path to config.ini file
        """
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file, create with defaults if missing"""
        if self.config_file.exists():
            logger.info(f"Loading config from: {self.config_file}")
            self.config.read(self.config_file)
            self._log_loaded_values()
        else:
            logger.info(f"Config file not found: {self.config_file}")
            self._create_default_config()
            logger.info(f"Created default config at: {self.config_file}")
    
    def _create_default_config(self) -> None:
        """Create config.ini with default values"""
        for section, values in self.DEFAULTS.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in values.items():
                self.config.set(section, key, value)
        self.save_config()
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        logger.info(f"Configuration saved to: {self.config_file}")
    
    def get(self, key: str, section: str = 'SETTINGS', default: Any = None) -> Any:
        """
        Get configuration value with fallback to default
        
        Args:
            key: Configuration key
            section: Config section (default: 'SETTINGS')
            default: Fallback value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if default is not None:
                return default
            return self.DEFAULTS.get(section, {}).get(key)
    
    def get_int(self, key: str, section: str = 'SETTINGS', default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key, section)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default
    
    def get_bool(self, key: str, section: str = 'SETTINGS', default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key, section)
        if isinstance(value, bool):
            return value
        return value.lower() in ('true', '1', 'yes', 'on') if isinstance(value, str) else default
    
    def set(self, key: str, value: Any, section: str = 'SETTINGS') -> None:
        """Set configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
    
    def get_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        Get configured date range for filtering
        
        Default behavior (empty values): Uses last 30 days (from 30 days ago to today)
        To disable: Set both to "none"
        Custom range: Set specific dates in YYYY-MM-DD format
        
        Returns:
            Tuple of (date_from, date_to) or (None, None) if explicitly disabled
            
        Raises:
            ValueError: If date format is invalid
        """
        date_from_str = self.get('date_from').strip().lower()
        date_to_str = self.get('date_to').strip().lower()
        
        # Check if explicitly disabled
        if date_from_str == 'none' and date_to_str == 'none':
            logger.info("Date filtering explicitly disabled")
            return None, None
        
        # If both are empty, use last 30 days as default
        if not date_from_str and not date_to_str:
            date_from_str = self._get_default_date_from()
            date_to_str = self._get_default_date_to()
            logger.info(f"Using default date range (last 30 days): {date_from_str} to {date_to_str}")
        
        date_from = None
        date_to = None
        
        if date_from_str and date_from_str != 'none':
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d')
                logger.info(f"Date filter from: {date_from.strftime('%Y-%m-%d')}")
            except ValueError as e:
                raise ValueError(f"Invalid date_from format: {date_from_str}. Use YYYY-MM-DD") from e
        
        if date_to_str and date_to_str != 'none':
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d')
                logger.info(f"Date filter to: {date_to.strftime('%Y-%m-%d')}")
            except ValueError as e:
                raise ValueError(f"Invalid date_to format: {date_to_str}. Use YYYY-MM-DD") from e
        
        return date_from, date_to
    
    def override_from_cli_args(self, args: Dict[str, Any]) -> None:
        """
        Override configuration with CLI arguments
        
        Args:
            args: Dictionary of CLI arguments (keys that exist in config)
        """
        for key, value in args.items():
            if value is not None:  # Only override if argument was provided
                self.set(key, value)
                logger.debug(f"CLI override: {key} = {value}")
    
    def _log_loaded_values(self) -> None:
        """Log all loaded configuration values"""
        logger.debug("Loaded configuration values:")
        for section in self.config.sections():
            for key, value in self.config.items(section):
                # Don't log sensitive values
                if 'password' not in key.lower():
                    logger.debug(f"  {section}.{key} = {value}")
    
    def __str__(self) -> str:
        """String representation of config"""
        output = "Current Configuration:\n"
        for section in self.config.sections():
            output += f"\n[{section}]\n"
            for key, value in self.config.items(section):
                output += f"  {key} = {value}\n"
        return output
