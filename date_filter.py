#!/usr/bin/env python3
"""
Date Filtering Module
Handles date-based filtering for replay files
"""

import os
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class DateFilter:
    """
    Filters files based on date ranges with multiple date detection methods
    """
    
    # Date patterns that might appear in filenames
    DATE_PATTERNS = [
        r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
        r'(\d{2})-(\d{2})-(\d{4})',  # MM-DD-YYYY
        r'(\d{4})(\d{2})(\d{2})',    # YYYYMMDD
    ]
    
    def __init__(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None):
        """
        Initialize date filter
        
        Args:
            date_from: Start date (inclusive) or None for no lower bound
            date_to: End date (inclusive) or None for no upper bound
        """
        self.date_from = date_from
        self.date_to = date_to
        self.enabled = date_from is not None or date_to is not None
        
        if self.enabled:
            logger.info(f"Date filter enabled")
            if self.date_from:
                logger.info(f"  From: {self.date_from.strftime('%Y-%m-%d')}")
            if self.date_to:
                logger.info(f"  To: {self.date_to.strftime('%Y-%m-%d')}")
        else:
            logger.info("Date filter disabled (processing all files)")
    
    def should_process(self, file_path: Path) -> tuple[bool, str]:
        """
        Check if file should be processed based on date filter
        
        Args:
            file_path: Path to file
            
        Returns:
            Tuple of (should_process: bool, reason: str)
            - reason is empty if should process, otherwise explains why skipped
        """
        if not self.enabled:
            return True, ""
        
        file_date = self._get_file_date(file_path)
        
        if file_date is None:
            logger.warning(f"Could not determine date for: {file_path.name}")
            return False, "Could not determine file date"
        
        # Check lower bound
        if self.date_from and file_date < self.date_from:
            return False, f"Before date range ({file_date.strftime('%Y-%m-%d')})"
        
        # Check upper bound
        if self.date_to and file_date > self.date_to:
            return False, f"After date range ({file_date.strftime('%Y-%m-%d')})"
        
        return True, ""
    
    def _get_file_date(self, file_path: Path) -> Optional[datetime]:
        """
        Extract file date from filename or file metadata
        
        Priority:
        1. Try to parse date from filename
        2. Fall back to file modification timestamp
        
        Args:
            file_path: Path to file
            
        Returns:
            Datetime object or None if date cannot be determined
        """
        # Priority 1: Try to extract from filename
        filename_date = self._parse_date_from_filename(file_path.name)
        if filename_date:
            logger.debug(f"Found date in filename: {file_path.name} -> {filename_date.strftime('%Y-%m-%d')}")
            return filename_date
        
        # Priority 2: Use file modification timestamp
        try:
            mod_timestamp = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_timestamp)
            logger.debug(f"Using file mtime: {file_path.name} -> {mod_date.strftime('%Y-%m-%d')}")
            return mod_date
        except (OSError, ValueError) as e:
            logger.warning(f"Could not get file modification time for {file_path.name}: {e}")
            return None
    
    def _parse_date_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Try to extract a date from filename using known patterns
        
        Args:
            filename: The filename to parse
            
        Returns:
            Datetime object or None if no date found
        """
        # Remove extension for cleaner parsing
        name_without_ext = Path(filename).stem
        
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, name_without_ext)
            if matches:
                for match in matches:
                    try:
                        # Handle different pattern groups
                        if len(match) == 3:
                            year, month, day = match
                            
                            # Determine format based on year position and value
                            year_int = int(year)
                            
                            # YYYY-MM-DD or YYYY-MM-DD (year first, 4 digits)
                            if year_int > 1900:
                                return datetime(year_int, int(month), int(day))
                            # MM-DD-YYYY or DD-MM-YYYY (year last, 4 digits)
                            else:
                                try:
                                    return datetime(int(day), int(year), int(month))
                                except ValueError:
                                    return datetime(int(month), int(day), int(year))
                    except (ValueError, TypeError):
                        continue
        
        return None
