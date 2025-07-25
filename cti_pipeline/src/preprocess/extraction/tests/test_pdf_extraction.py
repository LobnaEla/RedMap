"""
Tests for PDFExtraction class
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from pdf_extractor import PDFExtraction, extract_pdf_text
    from base import ExtractionResult
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Import pdf_extractor
    pdf_path = os.path.join(parent_dir, 'pdf_extractor.py')
    spec = importlib.util.spec_from_file_location("pdf_extractor", pdf_path)
    pdf_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdf_module)
    PDFExtraction = pdf_module.PDFExtraction
    extract_pdf_text = pdf_module.extract_pdf_text
    
    # Import base
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ExtractionResult = base.ExtractionResult


class TestPDFExtraction:
    """Test cases for PDFExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = PDFExtraction()
    
    def test_initialization(self):
        """Test PDFExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert '.pdf' in self.extractor.supported_formats
        assert len(self.extractor.supported_formats) == 1
    
    def test_supported_formats(self):
        """Test that PDF extractor only supports PDF files"""
        assert self.extractor.supported_formats == {'.pdf'}
    
    def test_extract_from_nonexistent_pdf(self):
        """Test extraction from non-existent PDF file"""
        result = self.extractor.extract_from_file("non_existent.pdf")
        assert isinstance(result, ExtractionResult)
        assert result.success == False
        assert "File not found" in result.error_message
        assert result.file_format == "unknown"
    
    def test_extract_from_unsupported_format(self):
        """Test extraction from unsupported file format"""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == False
            assert "Unsupported file format" in result.error_message
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_invalid_pdf(self):
        """Test extraction from invalid PDF file"""
        # Create a temporary file with PDF extension but invalid content
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"This is not a valid PDF file")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == False
            assert "Extraction failed" in result.error_message
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_pdf_method_with_invalid_file(self):
        """Test _extract_pdf method with invalid file"""
        try:
            self.extractor._extract_pdf("non_existent.pdf")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "PDF extraction error" in str(e)
    
    def test_convenience_function_with_nonexistent_file(self):
        """Test convenience function with non-existent file"""
        result = extract_pdf_text("non_existent.pdf")
        assert result == ""
    
    def test_extract_text_method(self):
        """Test _extract_text method calls _extract_pdf"""
        # This will fail since we're using a non-existent file, but we test the method exists
        try:
            self.extractor._extract_text("dummy.pdf", ".pdf")
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "PDF extraction error" in str(e)


def run_tests():
    """Run all tests for PDFExtraction"""
    print("Testing PDFExtraction...")
    
    test_class = TestPDFExtraction()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            test_class.setup_method()
            method = getattr(test_class, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {method_name}: {str(e)}")
            failed += 1
    
    print(f"\nPDF Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
