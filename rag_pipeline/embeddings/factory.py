"""
Embedder factory for creating embedder instances
"""
from typing import Optional

from .base import BaseEmbedder
from .huggingface_embedder import HuggingFaceEmbedder


class EmbedderFactory:
    """Factory for creating embedder instances"""
    
    @staticmethod
    def create_embedder(
        embedder_type: str = "huggingface",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        **kwargs
    ) -> BaseEmbedder:
        """
        Create an embedder instance
        
        Args:
            embedder_type: Type of embedder ("huggingface")
            model_name: Name of the model to use
            **kwargs: Additional arguments passed to the embedder
            
        Returns:
            BaseEmbedder instance
            
        Raises:
            ValueError: If embedder_type is not supported
        """
        if embedder_type.lower() == "huggingface":
            return HuggingFaceEmbedder(model_name=model_name, **kwargs)
        else:
            raise ValueError(f"Unsupported embedder type: {embedder_type}")
    
    @staticmethod
    def get_available_embedders() -> list:
        """Get list of available embedder types"""
        return ["huggingface"]
