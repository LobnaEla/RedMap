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
from .pdf_extractor import PDFExtraction, extract_pdf_from_file
from .html_extractor import HTMLExtraction, extract_html_from_file
from .json_extractor import JSONExtraction, extract_json_from_file
from .csv_extractor import CSVExtraction, extract_csv_from_file
from .txt_extractor import TXTExtraction, extract_text_from_file
from .router import extract_text

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
    'extract_pdf_from_file',
    'extract_html_from_file',
    'extract_json_from_file',
    'extract_csv_from_file',
    'extract_text_from_file',
    'extract_text'
]
