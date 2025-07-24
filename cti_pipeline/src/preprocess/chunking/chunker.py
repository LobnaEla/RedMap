import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FixedSizeChunker:
    """
    Fixed-size text chunking for CTI reports.
    """
    
    _nltk_warned = False
    _spacy_warned = False

    def __init__(self, chunk_size: int = 10, overlap: int = 2):
        """
        Initialize TextChunker for fixed-size chunking.
        
        Args:
            chunk_size: Number of sentences per chunk (default: 10)
            overlap: Number of overlapping sentences between chunks (default: 2)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
        # Try to initialize spaCy for better text processing
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            logger.debug("spaCy model loaded successfully")
        except Exception as e:
            if not FixedSizeChunker._spacy_warned:
                logger.warning(f"spaCy model not available: {e}. Using simple fallback.")
                FixedSizeChunker._spacy_warned = True

    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into sentences with improved error handling."""
        # Clean and normalize text
        text = self._clean_text(text)
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                sentences = [str(sent).strip() for sent in doc.sents if str(sent).strip()]
                logger.debug(f"spaCy tokenized {len(sentences)} sentences")
                return sentences
            except Exception as e:
                logger.warning(f"spaCy tokenization failed: {e}. Falling back to NLTK.")
        
        try:
            import nltk
            sentences = nltk.sent_tokenize(text, language='english')
            sentences = [s.strip() for s in sentences if s.strip()]
            logger.debug(f"NLTK tokenized {len(sentences)} sentences")
            return sentences
        except Exception as e:
            if not FixedSizeChunker._nltk_warned:
                logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split fallback.")
                FixedSizeChunker._nltk_warned = True
            
            # Simple fallback: split on periods, exclamation marks, and question marks
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            logger.debug(f"Simple tokenization produced {len(sentences)} sentences")
            return sentences

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better processing."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Fix common encoding issues
        text = text.replace('\u00a0', ' ')  
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        return text.strip()

    def generate_chunks(self, text: str, chunk_size: Optional[int] = None, overlap: Optional[int] = None, 
                       print_stats: bool = True) -> List[Dict[str, Any]]:
        """
        Generate fixed-size chunks with comprehensive statistics.
        
        Args:
            text: Input text to chunk
            chunk_size: Number of sentences per chunk (uses instance default if None)
            overlap: Number of overlapping sentences (uses instance default if None)
            print_stats: Whether to print detailed statistics
            
        Returns:
            List of text chunks with metadata
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap
        
        # Validate parameters
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and less than chunk_size")
        
        sentences = self.tokenize_text(text)
        if not sentences:
            logger.warning("No sentences found in text")
            return []
        
        # Calculate statistics
        original_text_length = len(text)
        total_sentences = len(sentences)
        
        chunks = []
        step = max(1, chunk_size - overlap)
        
        for i in range(0, len(sentences), step):
            end_idx = min(i + chunk_size, len(sentences))
            chunk_sentences = sentences[i:end_idx]
            chunk_text = " ".join(chunk_sentences)
            
            chunks.append({
                "chunk": chunk_text,
                "chunk_id": len(chunks),
                "start_sentence": i,
                "end_sentence": end_idx - 1,
                "sentence_count": len(chunk_sentences),
                "chunk_length": len(chunk_text),
                "character_start": sum(len(s) + 1 for s in sentences[:i]),  # Approximate
                "character_end": sum(len(s) + 1 for s in sentences[:end_idx]) - 1
            })
            
            if end_idx >= len(sentences):
                break
        
        # Print comprehensive statistics
        if print_stats:
            self._print_chunking_statistics(text, sentences, chunks, chunk_size, overlap)
        
        logger.info(f"Generated {len(chunks)} fixed-size chunks from {total_sentences} sentences")
        return chunks

    def _print_chunking_statistics(self, text: str, sentences: List[str], chunks: List[Dict[str, Any]], 
                                 chunk_size: int, overlap: int) -> None:
        """Print comprehensive chunking statistics."""
        original_text_length = len(text)
        total_sentences = len(sentences)
        total_chunks = len(chunks)
        
        # Calculate chunk lengths
        chunk_lengths = [chunk["chunk_length"] for chunk in chunks]
        total_chunked_length = sum(chunk_lengths)
        
        print("\n" + "="*60)
        print("CHUNKING STATISTICS")
        print("="*60)
        print(f"Original document length: {original_text_length:,} characters")
        print(f"Total sentences: {total_sentences}")
        print(f"Chunk size (sentences): {chunk_size}")
        print(f"Overlap (sentences): {overlap}")
        print(f"Total chunks generated: {total_chunks}")
        print()
        
        print("CHUNK DETAILS:")
        print("-" * 40)
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1:2d}: {chunk['chunk_length']:,} chars | "
                  f"Sentences {chunk['start_sentence']+1}-{chunk['end_sentence']+1} | "
                  f"Count: {chunk['sentence_count']}")
        
        print("-" * 40)
        print(f"Total chunked length: {total_chunked_length:,} characters")
        print(f"Average chunk length: {total_chunked_length // total_chunks:,} characters")
        print(f"Min chunk length: {min(chunk_lengths):,} characters")
        print(f"Max chunk length: {max(chunk_lengths):,} characters")
        
        # Coverage analysis
        coverage_ratio = total_chunked_length / original_text_length if original_text_length > 0 else 0
        print(f"\nCOVERAGE ANALYSIS:")
        print(f"Coverage ratio: {coverage_ratio:.2%}")
        
        if coverage_ratio > 1.0:
            print(f"Note: Coverage > 100% due to overlapping chunks")
            overlap_chars = total_chunked_length - original_text_length
            print(f"Overlapping content: ~{overlap_chars:,} characters")
        elif coverage_ratio < 0.95:
            print("WARNING: Coverage < 95%. Some content may be missing!")
        else:
            print("Good coverage - most content is included")
        
        print("="*60)

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """Get basic statistics about the text."""
        sentences = self.tokenize_text(text)
        words = text.split()
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "average_sentence_length": len(text) // len(sentences) if sentences else 0,
            "average_words_per_sentence": len(words) // len(sentences) if sentences else 0
        }
