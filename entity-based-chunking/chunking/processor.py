from typing import List, Dict, Any, Optional
from .groq_client import GroqClient
from .text_chunker import TextChunker

class CTIProcessor:
    """Main class for processing CTI reports."""
    def __init__(self, api_key: Optional[str] = None, config: dict = None):
        self.groq_client = GroqClient(api_key, config)
        self.chunker = TextChunker()

    def process_report(self, text: str, window: int = 2) -> List[Dict[str, Any]]:
        """Process a CTI report and return chunks with their associated IOCs."""
        ioc_data = self.groq_client.extract_iocs(text)
        chunks = self.chunker.generate_chunks(text, ioc_data, window)
        return chunks
