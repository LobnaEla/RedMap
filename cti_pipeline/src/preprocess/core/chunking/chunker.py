"""
CTI Chunker Module

Main chunking class that orchestrates IOC extraction and text chunking by
leveraging the entity-based-chunking system.
"""
import os
import sys
from typing import List, Dict, Any, Optional

# Add the project root to sys.path to allow for absolute imports
# This makes the import robust, regardless of where the script is run from
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    # Import functions from entity_based_chunking package
    from entity_based_chunking import process_cti_text, extract_iocs_only as extract_iocs_from_module
    from entity_based_chunking import load_config
    print("✓ Successfully imported entity_based_chunking functions")
except ImportError as e:
    print(f"Could not import from 'entity_based_chunking'. Ensure the path is correct. Error: {e}")
    # Define dummy functions to prevent application crash if the import fails
    def process_cti_text(*args, **kwargs):
        raise NotImplementedError("process_cti_text could not be imported.")
    def extract_iocs_from_module(*args, **kwargs):
        raise NotImplementedError("extract_iocs_only could not be imported.")
    def load_config(*args, **kwargs):
        return {}

class CTIChunker:
    """
    Main CTI chunking processor.
    This class acts as a simplified facade for the entity-based-chunking functions.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the chunker.
        
        Args:
            config_path: Optional path to a 'config.yaml' for the entity-based-chunking processor.
                         If None, will use the default config from entity_based_chunking.
        """
        try:
            # Load config from entity_based_chunking directory
            if config_path is None:
                # Use default config from entity_based_chunking
                entity_config_path = os.path.join(project_root, "entity_based_chunking", "config.yaml")
                self.config = load_config(entity_config_path)
            else:
                self.config = load_config(config_path)
            print(f"[Chunker] Config loaded successfully.")
        except Exception as e:
            print(f"[Chunker] Warning: Could not load config: {e}. Using None.")
            self.config = None  # Functions will handle None config
        
        print("[Chunker] CTIChunker initialized.")

    def _get_api_key_for_provider(self) -> Optional[str]:
        """
        Get the appropriate API key based on the configured provider.
        
        Returns:
            The API key for the current provider, or None if not found.
        """
        if not self.config or 'llm' not in self.config:
            print("[Chunker] Warning: No LLM config found, falling back to GROQ_API_KEY")
            return os.environ.get("GROQ_API_KEY")
        
        provider = self.config['llm'].get('provider', 'groq')
        provider_config = self.config['llm'].get(provider, {})
        api_key_env = provider_config.get('api_key_env', 'GROQ_API_KEY')
        
        api_key = os.environ.get(api_key_env)
        if not api_key:
            print(f"[Chunker] Warning: {api_key_env} not found in environment")
        else:
            print(f"[Chunker] Found API key for provider '{provider}': {api_key[:10]}...")
        
        return api_key

    def chunk(self, text: str, window: int = 2) -> List[Dict[str, Any]]:
        """
        Main chunking method that processes text and returns IOC-based chunks.
        
        Args:
            text: Input text to chunk.
            window: The context window size (number of sentences) around an IOC.
            
        Returns:
            A list of chunk dictionaries, where each chunk is centered around an IOC.
        """
        if not text or not text.strip():
            print("[Chunker] Empty or whitespace-only text provided.")
            return []
        
        print(f"[Chunker] Starting chunking with window size: {window}")
        
        try:
            # Get the correct API key based on configured provider
            api_key = self._get_api_key_for_provider()
            
            chunks = process_cti_text(text, config=self.config, window=window, api_key=api_key)
            print(f"[Chunker] Chunking completed. Found {len(chunks)} chunks.")
            return chunks
        except Exception as e:
            print(f"[Chunker] Chunking failed: {e}")
            return []

    def extract_iocs_only(self, text: str) -> List[Dict[str, str]]:
        """
        Extract only IOCs from the text without performing chunking.
        
        Args:
            text: The input text from which to extract IOCs.
            
        Returns:
            A list of dictionaries, each representing a found IOC.
        """
        try:
            # Get the correct API key based on configured provider
            api_key = self._get_api_key_for_provider()
            return extract_iocs_from_module(text, config=self.config, api_key=api_key)
        except Exception as e:
            print(f"[Chunker] IOC extraction failed: {e}")
            return []

    def get_chunk_statistics(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate and return statistics about the generated chunks.
        
        Args:
            chunks: A list of chunks as produced by the chunk() method.
            
        Returns:
            A dictionary containing statistics like total chunks, average length, and IOC type distribution.
        """
        if not chunks:
            return {"total_chunks": 0, "total_length": 0, "average_length": 0, "ioc_types": {}}
        
        total_chunks = len(chunks)
        total_length = sum(len(chunk.get("chunk", "")) for chunk in chunks)
        average_length = total_length / total_chunks if total_chunks > 0 else 0
        
        ioc_types = {}
        for chunk in chunks:
            ioc_type = chunk.get("type", "unknown")
            ioc_types[ioc_type] = ioc_types.get(ioc_type, 0) + 1
        
        return {
            "total_chunks": total_chunks,
            "total_length": total_length,
            "average_length": average_length,
            "ioc_types": ioc_types
        }
