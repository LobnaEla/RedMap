"""
Text Processor Module

This module provides text processing utilities for chunking operations.
"""

import re
from typing import List, Dict, Any, Set
from .config import ChunkingConfig

class TextProcessor:
    """Text processing utilities for chunking"""
    
    def __init__(self, config: ChunkingConfig):
        self.config = config
        self._nltk_warned = False
        self._spacy_warned = False
        self.nlp = None
        
        # Initialize spaCy if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
            print("[Chunker: text processor] spaCy model loaded successfully")
        except Exception as e:
            if not self._spacy_warned:
                print(f"[Chunker: text processor] spaCy model not available: {e}. Using NLTK fallback.")
                self._spacy_warned = True
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences"""
        # Clean and normalize text
        text = self._clean_text(text)
        
        # Try spaCy first
        if self.nlp:
            try:
                doc = self.nlp(text)
                sentences = [str(sent).strip() for sent in doc.sents if str(sent).strip()]
                print(f"[Chunker: text processor] spaCy tokenized {len(sentences)} sentences")
                return sentences
            except Exception as e:
                print(f"[Chunker: text processor] spaCy tokenization failed: {e}. Falling back to NLTK.")
        
        # Try NLTK
        try:
            import nltk
            sentences = nltk.sent_tokenize(text, language='english')
            sentences = [s.strip() for s in sentences if s.strip()]
            print(f"[Chunker: text processor] NLTK tokenized {len(sentences)} sentences")
            return sentences
        except Exception as e:
            if not self._nltk_warned:
                print(f"[Chunker: text processor] NLTK sentence tokenization failed: {e}. Using simple split fallback.")
                self._nltk_warned = True
            
            # Simple fallback: split on periods, exclamation marks, and question marks
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            print(f"[Chunker: text processor] Simple tokenization produced {len(sentences)} sentences")
            return sentences
    
    def find_ioc_positions(self, sentences: List[str], ioc: str) -> List[int]:
        """Find all sentence indices where an IOC appears"""
        positions = []
        ioc_lower = ioc.lower()
        
        for i, sentence in enumerate(sentences):
            if ioc_lower in sentence.lower():
                positions.append(i)
        
        print(f"[Chunker: text processor] IOC '{ioc}' found in {len(positions)} sentences")
        return positions
    
    def extract_context_window(self, sentences: List[str], center_idx: int, window: int = None) -> str:
        """Extract a window of sentences around a given index"""
        if window is None:
            window = self.config.window_size
            
        start_idx = max(0, center_idx - window)
        end_idx = min(len(sentences), center_idx + window + 1)
        chunk = " ".join(sentences[start_idx:end_idx])
        return chunk.strip()
    
    def generate_ioc_based_chunks(self, text: str, ioc_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Generate chunks based on IOC positions"""
        sentences = self.tokenize_sentences(text)
        if not sentences:
            print("[Chunker: text processor] No sentences found in text")
            return []
        
        chunks = []
        seen_chunks: Set[str] = set()
        
        print(f"[Chunker: text processor] Processing {len(ioc_data)} IOCs across {len(sentences)} sentences")
        
        # For each IOC, find all its occurrences and extract context
        for ioc_info in ioc_data:
            ioc = ioc_info.get("ioc", "").strip()
            ioc_type = ioc_info.get("type", "unknown").strip()
            
            if not ioc:
                continue
                
            positions = self.find_ioc_positions(sentences, ioc)
            
            for pos in positions:
                chunk_text = self.extract_context_window(sentences, pos, self.config.window_size)
                
                # Use normalized chunk text for deduplication if enabled
                if self.config.deduplicate_chunks:
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
                    "chunk_length": len(chunk_text),
                    "window_size": self.config.window_size
                })
        
        # Sort chunks by sentence position for consistent output
        chunks.sort(key=lambda x: x["sentence_position"])
        
        print(f"[Chunker: text processor] Generated {len(chunks)} unique chunks from {len(ioc_data)} IOCs")
        return chunks
    
    def generate_fixed_size_chunks(self, text: str) -> List[Dict[str, Any]]:
        """Generate fixed-size chunks"""
        sentences = self.tokenize_sentences(text)
        if not sentences:
            return []
        
        chunks = []
        chunk_size = self.config.fixed_chunk_size
        overlap = self.config.overlap
        step = max(1, chunk_size - overlap)
        
        for i in range(0, len(sentences), step):
            end_idx = min(i + chunk_size, len(sentences))
            chunk_text = " ".join(sentences[i:end_idx])
            
            chunks.append({
                "chunk": chunk_text,
                "start_sentence": i,
                "end_sentence": end_idx - 1,
                "chunk_length": len(chunk_text),
                "chunk_size": chunk_size
            })
            
            if end_idx >= len(sentences):
                break
        
        print(f"[Chunker: text processor] Generated {len(chunks)} fixed-size chunks")
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better processing"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Fix common encoding issues
        text = text.replace('\u00a0', ' ')  
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        return text.strip()
    
    def _normalize_chunk(self, chunk: str) -> str:
        """Normalize chunk text for deduplication"""
        # Remove extra whitespace and convert to lowercase
        normalized = re.sub(r'\s+', ' ', chunk.lower().strip())
        return normalized
