import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CTIProcessor:
    """Enhanced main class for processing CTI reports with better configuration and error handling."""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[dict] = None):
        """
        Initialize CTI processor with configuration.
        
        Args:
            api_key: Optional API key (will use environment variable if not provided)
            config: Configuration dictionary
        """
        if config is None:
            raise ValueError("Configuration dictionary is required")
            
        # Import here to avoid circular imports and handle missing dependencies gracefully
        try:
            from .llm_client import LLMClient
            from .text_chunker import TextChunker
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            raise
        
        try:
            self.llm_client = LLMClient(api_key, config)
            logger.info("LLMClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLMClient: {e}")
            raise
        
        try:
            chunker_config = config.get("chunking", {})
            self.chunker = TextChunker()
            logger.info("TextChunker initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TextChunker: {e}")
            raise

    def process_report(self, text: str, window: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Process a CTI report and return IOC-based chunks.
        
        Args:
            text: Input CTI report text
            window: Context window size (uses config default if None)
            
        Returns:
            List of chunks with metadata
        """
        if not text or not text.strip():
            logger.warning("Empty or whitespace-only text provided")
            return []
        
        try:
            # Extract IOCs from the text
            logger.info("Extracting IOCs from text...")
            ioc_data = self.llm_client.extract_iocs(text)
            
            if not ioc_data:
                logger.warning("No IOCs extracted from text")
                return []
            
            # Generate IOC-based chunks
            window = window or 2
            logger.info(f"Generating IOC-based chunks with window size {window}")
            chunks = self.chunker.generate_chunks(text, ioc_data, window)
            
            logger.info(f"Generated {len(chunks)} chunks using IOC-based strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing report: {e}")
            # Return empty result instead of raising to allow graceful degradation
            return []

    def get_iocs_only(self, text: str) -> List[Dict[str, str]]:
        """Extract only IOCs without chunking."""
        try:
            return self.llm_client.extract_iocs(text)
        except Exception as e:
            logger.error(f"Error extracting IOCs: {e}")
            return []
