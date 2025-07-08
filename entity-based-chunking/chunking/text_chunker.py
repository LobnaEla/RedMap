import nltk
import spacy
import re
import logging
from typing import List, Dict, Any, Set

logger = logging.getLogger(__name__)

class TextChunker:
    """Enhanced text chunking and IOC context extraction with improved matching."""
    
    _nltk_warned = False
    _spacy_warned = False

    def __init__(self):
        """
        Initialize TextChunker for IOC-based processing.
        """
        # Initialize spaCy for better text processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.debug("spaCy model loaded successfully")
        except Exception as e:
            if not TextChunker._spacy_warned:
                logger.warning(f"spaCy model not available: {e}. Using NLTK fallback.")
                TextChunker._spacy_warned = True
            self.nlp = None

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
            sentences = nltk.sent_tokenize(text, language='english')
            sentences = [s.strip() for s in sentences if s.strip()]
            logger.debug(f"NLTK tokenized {len(sentences)} sentences")
            return sentences
        except Exception as e:
            if not TextChunker._nltk_warned:
                logger.warning(f"NLTK sentence tokenization failed: {e}. Using simple split fallback.")
                TextChunker._nltk_warned = True
            
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

    def find_ioc_positions(self, sentences: List[str], ioc: str) -> List[int]:
        """Find all sentence indices where an IOC appears with case-insensitive matching."""
        positions = []
        ioc_lower = ioc.lower()
        
        for i, sentence in enumerate(sentences):
            if ioc_lower in sentence.lower():
                positions.append(i)
        
        logger.debug(f"IOC '{ioc}' found in {len(positions)} sentences")
        return positions

    def extract_chunk_context(self, sentences: List[str], center_idx: int, window: int = 2) -> str:
        """Extract a window of sentences around a given index."""
        start_idx = max(0, center_idx - window)
        end_idx = min(len(sentences), center_idx + window + 1)
        chunk = " ".join(sentences[start_idx:end_idx])
        return chunk.strip()

    def generate_chunks(self, text: str, ioc_data: List[Dict[str, str]], window: int = 2) -> List[Dict[str, Any]]:
        """
        Generate chunks with improved deduplication and context extraction.
        
        Args:
            text: Input text to chunk
            ioc_data: List of IOCs with their types
            window: Context window size around each IOC
            
        Returns:
            List of chunks with associated IOCs
        """
        sentences = self.tokenize_text(text)
        if not sentences:
            logger.warning("No sentences found in text")
            return []
        
        chunks = []
        seen_chunks: Set[str] = set()
        
        logger.debug(f"Processing {len(ioc_data)} IOCs across {len(sentences)} sentences")
        
        # For each IOC, find all its occurrences and extract context
        for ioc_info in ioc_data:
            ioc = ioc_info.get("ioc", "").strip()
            ioc_type = ioc_info.get("type", "unknown").strip()
            
            if not ioc:
                continue
                
            positions = self.find_ioc_positions(sentences, ioc)
            
            for pos in positions:
                chunk_text = self.extract_chunk_context(sentences, pos, window)
                
                # Use normalized chunk text for deduplication
                chunk_normalized = self._normalize_chunk(chunk_text)
                chunk_key = f"{chunk_normalized}|{ioc.lower()}"
                
                if chunk_key in seen_chunks:
                    continue
                    
                seen_chunks.add(chunk_key)
                chunks.append({
                    "chunk": chunk_text,
                    "ioc": ioc,
                    "type": ioc_type,
                    "sentence_position": pos,
                    "chunk_length": len(chunk_text)
                })
        
        # Sort chunks by sentence position for consistent output
        chunks.sort(key=lambda x: x["sentence_position"])
        
        logger.info(f"Generated {len(chunks)} unique chunks from {len(ioc_data)} IOCs")
        return chunks

    def generate_fixed_chunks(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
        """
        Generate fixed-size chunks regardless of IOCs.
        
        Args:
            text: Input text to chunk
            chunk_size: Number of sentences per chunk (uses instance default if None)
            overlap: Number of overlapping sentences (uses instance default if None)
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap
        
        sentences = self.tokenize_text(text)
        if not sentences:
            return []
        
        chunks = []
        step = max(1, chunk_size - overlap)
        
        for i in range(0, len(sentences), step):
            end_idx = min(i + chunk_size, len(sentences))
            chunk_text = " ".join(sentences[i:end_idx])
            
            chunks.append({
                "chunk": chunk_text,
                "start_sentence": i,
                "end_sentence": end_idx - 1,
                "chunk_length": len(chunk_text)
            })
            
            if end_idx >= len(sentences):
                break
        
        logger.info(f"Generated {len(chunks)} fixed-size chunks")
        return chunks

    def _normalize_chunk(self, chunk: str) -> str:
        """Normalize chunk text for deduplication."""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', chunk.lower().strip())
        return normalized
