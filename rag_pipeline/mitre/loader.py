"""
MITRE ATT&CK CSV loader
"""
import csv
import logging
from pathlib import Path
from typing import List, Iterator

from .document import MitreDocument

logger = logging.getLogger(__name__)


class MitreLoader:
    """Loads MITRE ATT&CK techniques from CSV file"""
    
    def __init__(self, csv_path: str):
        """
        Initialize loader with path to MITRE ATT&CK CSV file
        
        Args:
            csv_path: Path to the enterprise-attack.csv file
        """
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"MITRE CSV file not found: {csv_path}")
    
    def load_techniques(self) -> List[MitreDocument]:
        """
        Load all techniques from CSV file
        
        Returns:
            List of MitreDocument objects
        """
        techniques = []
        
        logger.info(f"Loading MITRE techniques from {self.csv_path}")
        
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    technique = self._row_to_document(row)
                    techniques.append(technique)
                except Exception as e:
                    logger.warning(f"Failed to parse row {row.get('id', 'unknown')}: {e}")
                    continue
        
        logger.info(f"Loaded {len(techniques)} MITRE techniques")
        return techniques
    
    def load_techniques_iter(self) -> Iterator[MitreDocument]:
        """
        Load techniques as an iterator (memory efficient)
        
        Yields:
            MitreDocument objects one by one
        """
        logger.info(f"Loading MITRE techniques from {self.csv_path} (iterator)")
        
        with open(self.csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    technique = self._row_to_document(row)
                    yield technique
                except Exception as e:
                    logger.warning(f"Failed to parse row {row.get('id', 'unknown')}: {e}")
                    continue
    
    def _row_to_document(self, row: dict) -> MitreDocument:
        """
        Convert CSV row to MitreDocument
        
        Args:
            row: Dictionary from CSV reader
            
        Returns:
            MitreDocument object
        """
        return MitreDocument(
            id=row['id'].strip(),
            name=row['name'].strip(),
            description=row['description'].strip(),
            url=row['url'].strip(),
            platforms=row['platforms'].strip(),
            kill_chain_phases=row['kill chain phases'].strip(),
            data_sources=row['data sources'].strip(),
            detection=row['detection'].strip()
        )
