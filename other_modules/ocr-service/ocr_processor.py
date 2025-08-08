import os
import re
import spacy
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import logging

logger = logging.getLogger(__name__)

class OCRProcessor:
    """OCR processing class using DocTR and spaCy"""
    
    def __init__(self):
        """Initialize OCR models"""
        try:
            logger.info("🔄 Loading OCR models...")
            
            # Load DocTR OCR model
            self.model = ocr_predictor(pretrained=True)
            logger.info("✅ DocTR model loaded")
            
            # Load spaCy model for text processing
            try:
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ spaCy model loaded")
            except OSError:
                logger.warning("⚠️ spaCy model not found, downloading...")
                import subprocess
                subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
                self.nlp = spacy.load("en_core_web_sm")
                logger.info("✅ spaCy model downloaded and loaded")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize OCR models: {e}")
            raise
    
    def extract_text(self, image_path: str, polish: bool = True) -> str:
        """
        Extract and optionally clean text from image file using DocTR
        
        Args:
            image_path: Path to the image file
            polish: Whether to apply text cleaning/polishing
            
        Returns:
            Extracted text as string
        """
        try:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found at: {image_path}")
            
            logger.info(f"🔄 Processing image: {image_path}")
            
            # Load document and perform OCR
            doc = DocumentFile.from_images(image_path)
            result = self.model(doc)
            raw_text = result.render()
            
            if not raw_text.strip():
                logger.warning("⚠️ No text extracted from image")
                return ""
            
            # Apply text polishing if requested
            if polish:
                cleaned_text = self._polish_text(raw_text)
                logger.info(f"✅ Text extracted and polished: {len(cleaned_text)} chars")
                return cleaned_text
            else:
                logger.info(f"✅ Raw text extracted: {len(raw_text)} chars")
                return raw_text
                
        except Exception as e:
            logger.error(f"❌ OCR extraction failed for {image_path}: {e}")
            raise
    
    def _polish_text(self, text: str) -> str:
        """
        Clean and polish the raw text extracted by OCR
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Cleaned and polished text
        """
        if not text:
            return ""
        
        # 1. Remove common footer artifacts like page numbers (e.g., "1/18")
        text = re.sub(r'\n\d+\/\d+\s*$', '', text, flags=re.MULTILINE)
        
        # 2. Fix missing space in common glued words (e.g., 'usedBy' → 'used By')
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # 3. Fix common OCR misreads
        text = re.sub(r'\bInk\b', 'LNK', text)
        text = re.sub(r'lnk', 'LNK', text, flags=re.IGNORECASE)
        
        # 4. Use spaCy to intelligently fix spacing and token boundaries
        lines = []
        for line in text.split('\n'):
            if line.strip():
                try:
                    doc = self.nlp(line.strip())
                    fixed_line = ''.join([token.text_with_ws for token in doc]).strip()
                    lines.append(fixed_line)
                except:
                    # Fallback to original line if spaCy processing fails
                    lines.append(line.strip())
        
        text = '\n'.join(lines)
        
        # 5. Normalize multiple newlines to a maximum of two
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 6. Remove excessive whitespace
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
