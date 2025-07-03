import os
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import re
import spacy

# Load models once to be efficient
nlp = spacy.load("en_core_web_sm")
model = ocr_predictor(pretrained=True)

def final_ocr_polish(text: str) -> str:
    """
    Cleans and polishes the raw text extracted by the OCR model.
    """
    # 1. Remove common footer artifacts like page numbers (e.g., "1/18")
    text = re.sub(r'\n\d+\/\d+\s*$', '', text, flags=re.MULTILINE)

    # 2. Fix missing space in common glued words (e.g., 'usedBy' → 'used By')
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

    # 3. Fix common misreads (e.g., capital "I" in "Ink" instead of "L")
    text = re.sub(r'\bInk\b', 'LNK', text)
    text = re.sub(r'lnk', 'LNK', text, flags=re.IGNORECASE)

    # 4. Use spaCy to intelligently fix spacing and token boundaries
    lines = []
    for line in text.split('\n'):
        doc = nlp(line.strip())
        fixed_line = ''.join([token.text_with_ws for token in doc]).strip()
        lines.append(fixed_line)
    
    text = '\n'.join(lines)

    # 5. Normalize multiple newlines to a maximum of two
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

def extract_text(image_path: str) -> str:
    """
    Extracts and cleans text from a single image file using DocTR.

    Args:
        image_path: The path to the image file.

    Returns:
        The cleaned, extracted text as a string.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")
        
    # Load the document and perform OCR
    doc = DocumentFile.from_images(image_path)
    result = model(doc)
    raw_text = result.render()
    
    # Clean the output
    cleaned_text = final_ocr_polish(raw_text)
    
    return cleaned_text
