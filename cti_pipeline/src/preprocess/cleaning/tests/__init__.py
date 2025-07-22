"""
Test suite for cleaning modules
"""

# Import all test modules
from . import test_base_cleaning
from . import test_html_cleaning
from . import test_ocr_cleaning
from . import test_pdf_cleaning
from . import test_json_cleaning

__all__ = [
    'test_base_cleaning',
    'test_html_cleaning', 
    'test_ocr_cleaning',
    'test_pdf_cleaning',
    'test_json_cleaning'
]
