"""
Test suite for extraction modules
"""

# Import all test modules
from . import test_base_extraction
from . import test_html_extraction
from . import test_pdf_extraction
from . import test_json_extraction
from . import test_csv_extraction
from . import test_txt_extraction

__all__ = [
    'test_base_extraction',
    'test_html_extraction', 
    'test_pdf_extraction',
    'test_json_extraction',
    'test_csv_extraction',
    'test_txt_extraction'
]
