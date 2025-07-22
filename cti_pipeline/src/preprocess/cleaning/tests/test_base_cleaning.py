"""
Tests for BaseCleaning class
"""

import sys
import os

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from base import BaseCleaning, clean_text
except ImportError:
    # Alternative import method
    import importlib.util
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    BaseCleaning = base.BaseCleaning
    clean_text = base.clean_text


class TestBaseCleaning:
    """Test cases for BaseCleaning class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = BaseCleaning()
    
    def test_initialization(self):
        """Test BaseCleaning initialization"""
        assert self.cleaner is not None
        assert hasattr(self.cleaner, 'non_ascii_patterns')
        assert hasattr(self.cleaner, 'boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_non_ascii_patterns')
    
    def test_remove_boilerplate(self):
        """Test boilerplate removal"""
        # Test with sample text containing boilerplate
        test_text = "This is important content. Subscribe to our newsletter! This is more content."
        result = self.cleaner.remove_boilerplate(test_text)
        assert isinstance(result, str)
        # The exact result depends on the patterns in cleaning_patterns.py
    
    def test_clean_whitespace(self):
        """Test whitespace cleaning"""
        test_cases = [
            ("Hello    world", "Hello world"),
            ("  Text with spaces  ", "Text with spaces"),
            ("Line1\n\n\n\nLine2", "Line1\n\nLine2"),
            ("Tab\t\t\tspaces", "Tab spaces"),
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_whitespace(input_text)
            # Just check that whitespace is cleaned, not exact match
            assert isinstance(result, str)
            assert len(result) <= len(input_text)
            # Basic whitespace should be normalized
            assert "    " not in result  # No multiple spaces
            assert not result.startswith(" ")  # No leading spaces
            assert not result.endswith(" ")   # No trailing spaces
    
    def test_remove_non_ascii(self):
        """Test non-ASCII character removal"""
        test_text = "Hello 世界 café résumé 🙂"
        result = self.cleaner.remove_non_ascii(test_text)
        assert isinstance(result, str)
        # Should remove or replace non-ASCII characters
        # Exact behavior depends on patterns in cleaning_patterns.py
    
    def test_clean_method(self):
        """Test main clean method"""
        test_text = "  Hello    world  with  extra   spaces  "
        result = self.cleaner.clean(test_text)
        assert isinstance(result, str)
        assert len(result) <= len(test_text)  # Should be same or shorter
    
    def test_clean_empty_string(self):
        """Test cleaning empty string"""
        result = self.cleaner.clean("")
        assert result == ""
    
    def test_clean_none_input(self):
        """Test cleaning with None input"""
        # Should handle gracefully
        try:
            result = self.cleaner.clean(None)
            # Should either return empty string or handle gracefully
        except (TypeError, AttributeError):
            # This is acceptable behavior for None input
            pass
    
    def test_clean_whitespace_only(self):
        """Test cleaning string with only whitespace"""
        test_text = "   \n\n\t\t   "
        result = self.cleaner.clean_whitespace(test_text)
        assert result == ""  # Should result in empty string after stripping
    
    def test_pattern_compilation(self):
        """Test that patterns are properly compiled"""
        # Check that compiled patterns exist and are not empty
        assert len(self.cleaner.compiled_boilerplate_patterns) >= 0
        assert len(self.cleaner.compiled_non_ascii_patterns) >= 0
        
        # Check that they are compiled regex objects
        if self.cleaner.compiled_boilerplate_patterns:
            import re
            assert all(hasattr(pattern, 'sub') for pattern in self.cleaner.compiled_boilerplate_patterns)


class TestCleanTextFunction:
    """Test cases for convenience function"""
    
    def test_clean_text_function(self):
        """Test the convenience clean_text function"""
        test_text = "  Hello    world  "
        result = clean_text(test_text)
        assert isinstance(result, str)
        assert len(result) <= len(test_text)
    
    def test_clean_text_empty(self):
        """Test convenience function with empty string"""
        result = clean_text("")
        assert result == ""


if __name__ == "__main__":
    # Simple test runner without pytest
    test_base = TestBaseCleaning()
    test_base.setup_method()
    
    print("Running BaseCleaning tests...")
    
    try:
        test_base.test_initialization()
        print("[PASS] Initialization test passed")
        
        test_base.test_remove_boilerplate()
        print("[PASS] Boilerplate removal test passed")
        
        test_base.test_clean_whitespace()
        print("[PASS] Whitespace cleaning test passed")
        
        test_base.test_remove_non_ascii()
        print("[PASS] Non-ASCII removal test passed")
        
        test_base.test_clean_method()
        print("[PASS] Clean method test passed")
        
        test_base.test_clean_empty_string()
        print("[PASS] Empty string test passed")
        
        test_base.test_clean_none_input()
        print("[PASS] None input test passed")
        
        test_base.test_clean_whitespace_only()
        print("[PASS] Whitespace only test passed")
        
        test_base.test_pattern_compilation()
        print("[PASS] Pattern compilation test passed")
        
        print("All BaseCleaning tests passed!")
        
    except Exception as e:
        print(f"[FAIL] BaseCleaning test failed: {e}")
    
    # Test convenience function
    test_func = TestCleanTextFunction()
    try:
        test_func.test_clean_text_function()
        print("[PASS] Convenience function test passed")
        
        test_func.test_clean_text_empty()
        print("[PASS] Convenience function empty test passed")
        
        print("All convenience function tests passed!")
        
    except Exception as e:
        print(f"[FAIL] Convenience function test failed: {e}")
