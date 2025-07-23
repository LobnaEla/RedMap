from .extraction import (
    PDFExtractor, HTMLExtractor, TxtExtractor, JsonExtractor
)
from .cleaning import (
    PDFCleaner, HTMLCleaner, OCRCleaner, JsonCleaner
)
from .normalizing.normalization import TextNormalizer
from .chunking.chunker import chunk_text

def route_pipeline(file_path: str) -> list:
    ext = file_path.split(".")[-1].lower()

    # === Extract & Clean ===
    if ext == "pdf":
        raw_text = PDFExtractor().extract(file_path)
        cleaned = PDFCleaner().clean(raw_text)
    elif ext == "html" or ext == "htm":
        raw_text = HTMLExtractor().extract(file_path)
        cleaned = HTMLCleaner().clean(raw_text)
    elif ext == "json" or ext == "jsonl":
        raw_text = JsonExtractor().extract(file_path)
        cleaned = JsonCleaner().clean(raw_text)
    elif ext == "txt":
        raw_text = TxtExtractor().extract(file_path)
        cleaned = OCRCleaner().clean(raw_text)
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    # === 2. Normalize ===
    normalized = TextNormalizer().normalize(cleaned)

    # === 3. Chunk ===
    return chunk_text(normalized)
