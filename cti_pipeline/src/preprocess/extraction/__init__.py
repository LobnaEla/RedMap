"""
Extraction Processors

This package contains text extraction components for various file formats.
"""

from .base import (
    BaseExtraction,
    ExtractionResult,
    extract_text_from_file,
    extract_with_result
)
from .pdf_extractor import PDFExtraction, extract_pdf_text
from .html_extractor import HTMLExtraction, extract_html_text
from .json_extractor import JSONExtraction, extract_json_text
from .csv_extractor import CSVExtraction, extract_csv_text
from .txt_extractor import TXTExtraction, extract_txt_text

__all__ = [
    'BaseExtraction',
    'PDFExtraction',
    'HTMLExtraction',
    'JSONExtraction',
    'CSVExtraction',
    'TXTExtraction',
    'ExtractionResult',
    'extract_text_from_file',
    'extract_with_result',
    'extract_pdf_text',
    'extract_html_text',
    'extract_json_text',
    'extract_csv_text',
    'extract_txt_text'
]
