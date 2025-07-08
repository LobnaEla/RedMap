import nltk
import spacy
from typing import List, Dict, Any

class TextChunker:
    """Handles text chunking and IOC context extraction."""
    _nltk_warned = False

    def __init__(self):
        # Initialize spaCy for better text processing
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            # If model isn't downloaded, use NLTK as fallback
            self.nlp = None

    def tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into sentences. Always use English for NLTK, fallback to split if error."""
        if self.nlp:
            doc = self.nlp(text)
            return [str(sent) for sent in doc.sents]
        try:
            return nltk.sent_tokenize(text, language='english')
        except Exception as e:
            if not TextChunker._nltk_warned:
                print(f"[TextChunker] NLTK sentence tokenization failed: {e}\nUsing fallback split on period. To fix, run in Python: import nltk; nltk.download('punkt')")
                TextChunker._nltk_warned = True
            return [s.strip() for s in text.split('.') if s.strip()]

    def find_ioc_positions(self, sentences: List[str], ioc: str) -> List[int]:
        """Find all sentence indices where an IOC appears."""
        return [i for i, sent in enumerate(sentences) if ioc in sent]

    def extract_chunk_context(self, sentences: List[str], center_idx: int, window: int = 2) -> str:
        """Extract a window of sentences around a given index."""
        start_idx = max(0, center_idx - window)
        end_idx = min(len(sentences), center_idx + window + 1)
        return " ".join(sentences[start_idx:end_idx])

    def generate_chunks(self, text: str, ioc_data: List[Dict[str, str]], window: int = 2) -> List[Dict[str, Any]]:
        """
        For each IOC detected by the LLM, find all occurrences in the text, extract a window of sentences around each occurrence,
        and return a list of chunks, each tagged with the IOC(s) found in that chunk.
        Deduplicate chunks by their text and IOC set.
        """
        sentences = self.tokenize_text(text)
        chunks = []
        seen_chunks = set()

        # For each IOC, find all its occurrences and extract context
        for ioc_info in ioc_data:
            ioc = ioc_info["ioc"]
            ioc_type = ioc_info["type"]
            positions = self.find_ioc_positions(sentences, ioc)
            for pos in positions:
                chunk_text = self.extract_chunk_context(sentences, pos, window)
                # Use a tuple of chunk text and ioc to deduplicate
                chunk_key = (chunk_text, ioc)
                if chunk_key in seen_chunks:
                    continue
                seen_chunks.add(chunk_key)
                chunks.append({
                    "chunk": chunk_text,
                    "ioc": ioc,
                    "type": ioc_type
                })

        return chunks
