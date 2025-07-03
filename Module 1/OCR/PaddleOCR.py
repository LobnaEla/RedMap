from paddleocr import PaddleOCR
import os
import cv2
import re
import spacy

def preprocess_image(path):
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Image not found: {path}")
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize to improve OCR precision (especially small fonts)
    scale = 2  # e.g., upscale by 2x
    resized = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Denoising
    denoised = cv2.fastNlMeansDenoising(resized, h=30)
    
    # Thresholding
    _, thresh = cv2.threshold(denoised, 180, 255, cv2.THRESH_BINARY)
    
    # Convert back to a 3-channel image so paddleocr can process it
    thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    return thresh_bgr

def clean_ocr_output(text_lines):
    # Join lines into a single string, preserving some structure
    text = "\n".join(text_lines)

    # Rule-based corrections for common OCR errors
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # Fix camelCase like "wordWord"
    text = re.sub(r'\s*•\s*', '\n\n• ', text)      # Format bullet points
    text = re.sub(r'(\w),(\w)', r'\1, \2', text)     # Add space after comma
    text = re.sub(r' (\d{2}:\d{2})', r' \1\n', text) # Add newline after time
    
    # Use spaCy for more advanced word segmentation to fix merged words
    doc = nlp(text)
    corrected_words = []
    for token in doc:
        # Heuristic to split merged words based on typical English word length
        if len(token.text) > 15 and token.is_alpha:
            # This is a simple heuristic. A more advanced solution could use a dictionary.
            # For now, we just signal that a long word might be a problem.
            # A better approach is often to improve preprocessing.
            pass # No simple split implemented here to avoid incorrect splits.
        corrected_words.append(token.text_with_ws)
    
    text = "".join(corrected_words)

    # Add breaks before major headers
    text = re.sub(r'(?<=[a-z])(Executive Summary)', r'\n\n\1', text)
    text = re.sub(r'(?<=[a-z])(An overview of LNK file format)', r'\n\n\1', text)

    # Final cleanup of whitespace
    text = re.sub(r'\n{3,}', '\n\n', text) # Consolidate newlines
    text = re.sub(r' {2,}', ' ', text)      # Consolidate spaces
    
    return text.strip()

# Créer un lecteur PaddleOCR avec anglais
ocr = PaddleOCR(use_textline_orientation=True, lang='en')
nlp = spacy.load("en_core_web_sm")

# Chemin vers le dossier contenant les images
input_folder = "image"
output_folder = "ocr_output"
os.makedirs(output_folder, exist_ok=True)

# Boucle sur les fichiers image
for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        image_path = os.path.join(input_folder, filename)
        print(f"Traitement : {filename}")
        
        # Preprocess the image to improve OCR accuracy
        processed_img = preprocess_image(image_path)
        
        # Perform OCR on the processed image
        results = ocr.predict(processed_img)
        
        # Debug: Let's see what the actual structure looks like
        print(f"Results type: {type(results)}")
        print(f"Results length: {len(results) if results else 'None'}")
        if results:
            print(f"First element type: {type(results[0])}")
            print(f"First element: {results[0]}")
        
        # Try to extract text based on the actual structure
        text_lines = []
        if results:
            # Handle different possible result structures
            for result in results:
                if isinstance(result, dict):
                    # If it's a dictionary, look for text fields
                    if 'rec_texts' in result:
                        text_lines.extend(result['rec_texts'])
                    elif 'text' in result:
                        text_lines.append(result['text'])
                elif isinstance(result, list):
                    # If it's a list, process each item
                    for item in result:
                        if isinstance(item, list) and len(item) == 2:
                            bbox, text_info = item
                            if isinstance(text_info, tuple) and len(text_info) == 2:
                                text, confidence = text_info
                                if confidence > 0.5 and len(text.strip()) > 1:
                                    text_lines.append(text)
                        elif isinstance(item, str):
                            text_lines.append(item)
        
        # Post-process output
        clean_text = clean_ocr_output(text_lines)
        
        # Construct the correct output path
        txt_filename = os.path.join(output_folder, os.path.splitext(filename)[0] + ".txt")

        # Save the cleaned text
        with open(txt_filename, 'w', encoding='utf-8') as f:
            f.write(clean_text)

        print(f"Texte extrait : {txt_filename}")
