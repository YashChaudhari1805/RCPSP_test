import pandas as pd
from pathlib import Path
from typing import Optional
import logging

from .interfaces import IDataLoader
from .multi_sheet_parser import MultiSheetParser
from .single_sheet_parser import SingleSheetParser
from models import ProjectData
from config import ModelConfig

logger = logging.getLogger(__name__)


class ExcelDataLoader(IDataLoader):
    """Loads project data from Excel files."""
    
    def __init__(self, config: ModelConfig = None):
        # Fix: Accept and store config, pass it to sub-parsers
        self.config = config or ModelConfig()
        self.multi_parser = MultiSheetParser(self.config)
        self.single_parser = SingleSheetParser(self.config)
    
    def load(self, filepath: str) -> ProjectData:
        """
        Load project data from Excel file.
        
        Automatically detects format (multi-sheet or single-sheet).
        
        Args:
            filepath: Path to Excel file
            
        Returns:
            ProjectData instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        logger.info(f"Loading data from {filepath}")
        
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"Excel file not found: {filepath}")
        
        try:
            xls = pd.ExcelFile(filepath)
            sheet_names = {s.strip() for s in xls.sheet_names}
            
            # Detect format
            if self._is_multi_sheet_format(sheet_names):
                logger.info("Detected multi-sheet format")
                data = self.multi_parser.parse(filepath, sheet_names)
            else:
                logger.info("Detected single-sheet format")
                data = self.single_parser.parse(filepath)
            
            logger.info("Data loaded successfully")
            return data
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            raise ValueError(f"Failed to load Excel file: {e}")
    
    @staticmethod
    def _is_multi_sheet_format(sheet_names: set) -> bool:
        """Detect if Excel uses multi-sheet format."""
        required_sheets = {"Activities", "Precedence"}
        return required_sheets.issubset(sheet_names)