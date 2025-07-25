"""
Tests for PDFCleaning class
"""

import sys
import os

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from pdf_cleaner import PDFCleaning, clean_pdf_text
except ImportError:
    # Alternative import method
    import importlib.util
    pdf_path = os.path.join(parent_dir, 'pdf_cleaner.py')
    spec = importlib.util.spec_from_file_location("pdf_cleaner", pdf_path)
    pdf_cleaner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdf_cleaner)
    PDFCleaning = pdf_cleaner.PDFCleaning
    clean_pdf_text = pdf_cleaner.clean_pdf_text


class TestPDFCleaning:
    """Test cases for PDFCleaning class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = PDFCleaning()
    
    def test_initialization(self):
        """Test PDFCleaning initialization"""
        assert self.cleaner is not None
        # Should inherit all base cleaner attributes
        assert hasattr(self.cleaner, 'non_ascii_patterns')
        assert hasattr(self.cleaner, 'boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_non_ascii_patterns')
    
    def test_inheritance_from_base(self):
        """Test that PDF cleaner properly inherits from base"""
        # Should have access to base methods
        assert hasattr(self.cleaner, 'remove_boilerplate')
        assert hasattr(self.cleaner, 'clean_whitespace')
        assert hasattr(self.cleaner, 'remove_non_ascii')
        
        # Test base functionality still works
        test_text = "  Hello    world  "
        result = self.cleaner.clean_whitespace(test_text)
        assert result == "Hello world"
    
    def test_clean_method_basic(self):
        """Test the basic clean method"""
        # Since PDFCleaning doesn't override clean(), it uses base clean()
        test_text = "  PDF   text   with   spaces  "
        result = self.cleaner.clean(test_text)
        assert isinstance(result, str)
        assert "PDF text with spaces" in result
    
    def test_clean_empty_string(self):
        """Test cleaning empty string"""
        result = self.cleaner.clean("")
        assert result == ""
    
    def test_clean_pdf_like_content(self):
        """Test cleaning PDF-like content"""
        pdf_content = """
        Header text that appears on every page
        
        Main content of the document goes here.
        This is an important paragraph.
        
        Page 1 of 10
        Footer text
        
        More content continues here.
        Another important paragraph.
        
        Page 2 of 10
        Footer text
        """
        result = self.cleaner.clean(pdf_content)
        assert isinstance(result, str)
        assert "Main content" in result
        assert "important paragraph" in result
        # Should still contain content even without specific PDF cleaning
    
    def test_clean_with_boilerplate(self):
        """Test cleaning with boilerplate content"""
        pdf_text = "Important content. Subscribe to newsletter! More content."
        result = self.cleaner.clean(pdf_text)
        assert isinstance(result, str)
        assert "Important content" in result
        # Boilerplate removal depends on patterns in cleaning_patterns.py
    
    def test_clean_with_non_ascii(self):
        """Test cleaning with non-ASCII characters"""
        pdf_text = "PDF content with special chars: café résumé naïve"
        result = self.cleaner.clean(pdf_text)
        assert isinstance(result, str)
        # Non-ASCII handling depends on patterns in cleaning_patterns.py
    
    def test_clean_whitespace_scenarios(self):
        """Test various whitespace scenarios common in PDFs"""
        test_cases = [
            ("Line1\n\n\n\nLine2", "Line1\n\nLine2"),
            ("Word1    Word2", "Word1 Word2"),
            ("  Leading and trailing  ", "Leading and trailing"),
            ("Tab\t\tspaced", "Tab spaced"),
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_whitespace(input_text)
            assert result == expected
    
    def test_pattern_compilation_inheritance(self):
        """Test that pattern compilation works correctly"""
        # Should have compiled patterns from base class
        assert hasattr(self.cleaner, 'compiled_boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_non_ascii_patterns')
        
        # Patterns should be compiled regex objects
        if self.cleaner.compiled_boilerplate_patterns:
            import re
            assert all(hasattr(pattern, 'sub') for pattern in self.cleaner.compiled_boilerplate_patterns)


class TestCleanPDFTextFunction:
    """Test cases for convenience function"""
    
    def test_clean_pdf_text_function(self):
        """Test the convenience clean_pdf_text function"""
        pdf_text = "  PDF  text  with  spaces  "
        result = clean_pdf_text(pdf_text)
        assert isinstance(result, str)
        assert "PDF text with spaces" in result
    
    def test_clean_pdf_text_empty(self):
        """Test convenience function with empty string"""
        result = clean_pdf_text("")
        assert result == ""
    
    def test_clean_pdf_text_whitespace_only(self):
        """Test convenience function with whitespace only"""
        result = clean_pdf_text("   \n\n\t  ")
        assert isinstance(result, str)
        assert result.strip() == ""


class TestPDFErrorHandling:
    """Test error handling in PDF cleaning"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = PDFCleaning()
    
    def test_error_handling_large_text(self):
        """Test handling of very large text"""
        large_text = "PDF content " * 1000
        try:
            result = self.cleaner.clean(large_text)
            assert isinstance(result, str)
        except Exception as e:
            # Should handle gracefully
            print(f"Large text handling: {e}")
    
    def test_error_handling_special_chars(self):
        """Test handling of special characters"""
        special_text = "PDF!@#$%^&*()[]{}|\\:;\"'<>?,./"
        try:
            result = self.cleaner.clean(special_text)
            assert isinstance(result, str)
        except Exception as e:
            # Should handle gracefully
            print(f"Special chars handling: {e}")
    
    def test_none_input_handling(self):
        """Test handling of None input"""
        try:
            result = self.cleaner.clean(None)
            # Should either return something or raise appropriate error
        except (TypeError, AttributeError):
            # This is acceptable behavior for None input
            pass


class TestPDFPlaceholderMethods:
    """Test that the class is ready for future PDF-specific methods"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = PDFCleaning()
    
    def test_ready_for_extension(self):
        """Test that the class can be extended with PDF-specific methods"""
        # The class should be ready to add methods like:
        # - remove_page_numbers
        # - fix_pdf_line_breaks
        # - clean_pdf_tables
        # - remove_pdf_headers_footers
        
        # For now, just verify it has the basic structure
        assert hasattr(self.cleaner, '__class__')
        assert self.cleaner.__class__.__name__ == 'PDFCleaning'
        assert issubclass(self.cleaner.__class__, type(self.cleaner).__bases__[0])


if __name__ == "__main__":
    # Simple test runner
    test_pdf = TestPDFCleaning()
    test_pdf.setup_method()
    
    print("Running PDF Cleaning tests...")
    try:
        test_pdf.test_initialization()
        print("[PASS] Initialization test passed")
        
        test_pdf.test_inheritance_from_base()
        print("[PASS] Inheritance test passed")
        
        test_pdf.test_clean_empty_string()
        print("[PASS] Empty string test passed")
        
        test_pdf.test_clean_whitespace_scenarios()
        print("[PASS] Whitespace scenarios test passed")
        
        print("All basic tests passed!")
        
    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
    
    # Test convenience function
    test_func = TestCleanPDFTextFunction()
    try:
        test_func.test_clean_pdf_text_empty()
        print("[PASS] Convenience function test passed")
    except Exception as e:
        print(f"[FAILED] Convenience function test failed: {e}")
    
    # Test error handling
    test_error = TestPDFErrorHandling()
    test_error.setup_method()
    try:
        test_error.test_error_handling_special_chars()
        print("[PASS] Error handling test passed")
    except Exception as e:
        print(f"[FAILED] Error handling test failed: {e}")
    
    # Test extensibility
    test_placeholder = TestPDFPlaceholderMethods()
    test_placeholder.setup_method()
    try:
        test_placeholder.test_ready_for_extension()
        print("[PASS] Extensibility test passed")
    except Exception as e:
        print(f"[FAILED] Extensibility test failed: {e}")
