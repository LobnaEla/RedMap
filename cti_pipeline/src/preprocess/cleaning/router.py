from .pdf_cleaner import clean_pdf_text
from .html_cleaner import clean_html_text
from .json_cleaner import clean_json_text
from .ocr_cleaner import clean_ocr_text
import os

def _read_file(file_path: str) -> str:
    """Read text content from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"[Clean] Error reading file {file_path}: {e}")
        return ""

def clean_text(file_path: str) -> str:
    """
    Clean text from extracted files, determining the original file type
    from the filename pattern for proper cleaning method selection.
    """
    
    # Read the text content from file
    text_content = _read_file(file_path)
    
    # Check if this is an extracted file (has "extracted_" prefix)
    filename = os.path.basename(file_path)
    
    if filename.startswith("extracted_") and filename.endswith(".txt"):
        # Extract the original filename from extracted_originalname.txt
        original_name = filename[10:-4]  # Remove "extracted_" prefix and ".txt" suffix
        
        # Determine original file extension
        if "." in original_name:
            original_ext = original_name.split(".")[-1].lower()
        else:
            original_ext = "txt"
        
        # Route to appropriate cleaner based on original file type
        if original_ext == "pdf":
            return clean_pdf_text(text_content)
        elif original_ext in ["html", "htm"]:
            return clean_html_text(text_content)
        elif original_ext in ["json", "jsonl"]:
            return clean_json_text(text_content)
        else:
            return clean_ocr_text(text_content)
    
    else:
        # Handle direct file processing (not extracted files)
        ext = file_path.split(".")[-1].lower()
        if ext == "pdf":
            return clean_pdf_text(text_content)
        elif ext in ["html", "htm"]:
            return clean_html_text(text_content)
        elif ext in ["json", "jsonl"]:
            return clean_json_text(text_content)
        elif ext == "txt":
            return clean_ocr_text(text_content)
        else:
            raise ValueError(f"Unsupported extension: {ext}")