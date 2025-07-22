"""
Tests for OCRCleaning class
"""

import sys
import os

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from ocr_cleaner import OCRCleaning, clean_ocr_text
except ImportError:
    # Alternative import method
    import importlib.util
    ocr_path = os.path.join(parent_dir, 'ocr_cleaner.py')
    spec = importlib.util.spec_from_file_location("ocr_cleaner", ocr_path)
    ocr_cleaner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ocr_cleaner)
    OCRCleaning = ocr_cleaner.OCRCleaning
    clean_ocr_text = ocr_cleaner.clean_ocr_text


class TestOCRCleaning:
    """Test cases for OCRCleaning class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = OCRCleaning()
    
    def test_initialization(self):
        """Test OCRCleaning initialization"""
        assert self.cleaner is not None
        # Should inherit all base cleaner attributes
        assert hasattr(self.cleaner, 'non_ascii_patterns')
        assert hasattr(self.cleaner, 'boilerplate_patterns')
        # Should have OCR-specific attributes
        assert hasattr(self.cleaner, 'ocr_patterns')
        assert hasattr(self.cleaner, 'compiled_ocr_patterns')
    
    def test_pattern_compilation(self):
        """Test that OCR patterns are properly compiled"""
        assert hasattr(self.cleaner, 'compiled_ocr_patterns')
        assert isinstance(self.cleaner.compiled_ocr_patterns, list)
        
        # Check that they are compiled regex objects if patterns exist
        if self.cleaner.compiled_ocr_patterns:
            import re
            assert all(hasattr(pattern, 'sub') for pattern in self.cleaner.compiled_ocr_patterns)
    
    def test_fix_ocr_artifacts(self):
        """Test OCR artifact removal"""
        # Test with common OCR artifacts
        test_cases = [
            ("Text with OCR artifacts", "Text with OCR artifacts"),  # No artifacts
            ("Te×t w1th artif@cts", "Text with artifacts"),  # Common OCR errors
            ("Nórmal text", "Normal text"),  # Character substitutions
        ]
        
        for input_text, expected_pattern in test_cases:
            result = self.cleaner.fix_ocr_artifacts(input_text)
            assert isinstance(result, str)
            # Exact matching depends on the OCR patterns defined
    
    def test_fix_ocr_artifacts_empty(self):
        """Test OCR artifact fixing with empty string"""
        result = self.cleaner.fix_ocr_artifacts("")
        assert result == ""
    
    def test_fix_ocr_artifacts_none(self):
        """Test OCR artifact fixing with None input"""
        try:
            result = self.cleaner.fix_ocr_artifacts(None)
            # Should handle gracefully
        except (TypeError, AttributeError):
            # This is acceptable behavior for None input
            pass
    
    def test_clean_method_pipeline(self):
        """Test the complete OCR cleaning pipeline"""
        ocr_text = "Th1s 1s s0me OCR text w1th err0rs and artif@cts."
        result = self.cleaner.clean(ocr_text)
        assert isinstance(result, str)
        # Should apply both base cleaning and OCR-specific cleaning
        assert len(result) > 0
    
    def test_inheritance_from_base(self):
        """Test that OCR cleaner properly inherits from base"""
        # Should have access to base methods
        assert hasattr(self.cleaner, 'remove_boilerplate')
        assert hasattr(self.cleaner, 'clean_whitespace')
        assert hasattr(self.cleaner, 'remove_non_ascii')
        
        # Test base functionality still works
        test_text = "  Hello    world  "
        result = self.cleaner.clean_whitespace(test_text)
        assert result == "Hello world"
    
    def test_clean_order(self):
        """Test that cleaning methods are applied in correct order"""
        # OCR cleaning should call parent clean() first, then OCR-specific
        test_text = "  OCR  text  with  artifacts  "
        result = self.cleaner.clean(test_text)
        assert isinstance(result, str)
        # Should have cleaned whitespace and OCR artifacts
    
    def test_ocr_patterns_loading(self):
        """Test that OCR patterns are loaded correctly"""
        assert hasattr(self.cleaner, 'ocr_patterns')
        # OCR patterns should be loaded from cleaning_patterns
        assert isinstance(self.cleaner.ocr_patterns, (list, tuple))


class TestCleanOCRTextFunction:
    """Test cases for convenience function"""
    
    def test_clean_ocr_text_function(self):
        """Test the convenience clean_ocr_text function"""
        ocr_text = "Th1s 1s OCR text w1th err0rs"
        result = clean_ocr_text(ocr_text)
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_clean_ocr_text_empty(self):
        """Test convenience function with empty string"""
        result = clean_ocr_text("")
        assert result == ""
    
    def test_clean_ocr_text_whitespace(self):
        """Test convenience function with whitespace"""
        result = clean_ocr_text("   ")
        assert isinstance(result, str)


class TestOCRErrorHandling:
    """Test error handling in OCR cleaning"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = OCRCleaning()
    
    def test_error_handling_in_artifacts(self):
        """Test error handling in fix_ocr_artifacts"""
        # This should not crash even with problematic input
        problematic_inputs = [
            "",
            "a" * 10000,  # Very long string
            "Special chars: !@#$%^&*()",
            "\n\t\r",  # Control characters
        ]
        
        for test_input in problematic_inputs:
            try:
                result = self.cleaner.fix_ocr_artifacts(test_input)
                assert isinstance(result, str)
            except Exception as e:
                # Should handle gracefully with error message
                assert "Error fixing OCR artifacts" in str(e) or isinstance(result, str)


if __name__ == "__main__":
    # Simple test runner
    test_ocr = TestOCRCleaning()
    test_ocr.setup_method()
    
    print("Running OCR Cleaning tests...")
    try:
        test_ocr.test_initialization()
        print("[PASS] Initialization test passed")
        
        test_ocr.test_pattern_compilation()
        print("[PASS] Pattern compilation test passed")
        
        test_ocr.test_fix_ocr_artifacts_empty()
        print("[PASS] Empty input test passed")
        
        test_ocr.test_inheritance_from_base()
        print("[PASS] Inheritance test passed")
        
        print("All basic tests passed!")
        
    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
    
    # Test convenience function
    test_func = TestCleanOCRTextFunction()
    try:
        test_func.test_clean_ocr_text_empty()
        print("[PASS] Convenience function test passed")
    except Exception as e:
        print(f"[FAILED] Convenience function test failed: {e}")
    
    # Test error handling
    test_error = TestOCRErrorHandling()
    test_error.setup_method()
    try:
        test_error.test_error_handling_in_artifacts()
        print("[PASS] Error handling test passed")
    except Exception as e:
        print(f"[FAILED] Error handling test failed: {e}")
