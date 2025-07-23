from .pdf_extractor import extract_pdf_from_file
from .html_extractor import extract_html_from_file    
from .json_extractor import extract_json_from_file
from .txt_extractor import extract_text_from_file

def extract_text(file_path: str) -> str:
    ext = file_path.split(".")[-1].lower()
    if ext == "pdf":
        return extract_pdf_from_file(file_path)
    elif ext in ["html", "htm"]:
        return extract_html_from_file(file_path)
    elif ext in ["json", "jsonl"]:
        return extract_json_from_file(file_path)
    elif ext == "txt":
        return extract_text_from_file(file_path)
    else:
        raise ValueError(f"Unsupported extension: {ext}")
