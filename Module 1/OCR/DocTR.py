import os
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import re
import spacy

# Load lightweight NLP pipeline once
nlp = spacy.load("en_core_web_sm")

def final_ocr_polish(text):
    # 1. Remove common footer artifacts
    text = re.sub(r'\n\d+\/\d+\s*$', '', text)  # Remove trailing page markers like 1/18

    # 2. Fix missing space in common glued words
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # e.g. removethe → remove the

    # 3. Fix common misreads (capital I vs lowercase l)
    text = re.sub(r'\bInk\b', 'LNK', text)  # capital "I" instead of "L"
    text = re.sub(r'lnk', 'LNK', text, flags=re.IGNORECASE)

    # 4. Fix spacing and token boundaries using spaCy
    lines = []
    for line in text.split('\n'):
        doc = nlp(line.strip())
        fixed = ''.join([token.text_with_ws for token in doc]).strip()
        lines.append(fixed)

    # 5. Normalize line breaks
    text = '\n'.join(lines)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# ========== CONFIG ==========
input_folder = "image"
output_folder = "doctr_output"
os.makedirs(output_folder, exist_ok=True)

# Load the OCR model (with Torch backend)
model = ocr_predictor(pretrained=True)

# Process each image in folder
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
        image_path = os.path.join(input_folder, filename)
        print(f"🔍 Processing: {filename}")

        # Load image as a document
        doc = DocumentFile.from_images(image_path)

        # Perform OCR
        result = model(doc)

        # Export plain text (DocTR handles layout automatically)
        raw_text = result.render()

        # Clean the extracted text
        cleaned_text = final_ocr_polish(raw_text)

        # Save result to .txt
        base_name = os.path.splitext(filename)[0]
        output_path = os.path.join(output_folder, f"{base_name}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        print(f"✅ Text saved to: {output_path}")
