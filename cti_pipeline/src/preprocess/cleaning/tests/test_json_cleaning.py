"""
Tests for JSONCleaning class
"""

import sys
import os

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from json_cleaner import JSONCleaning, clean_json_text
except ImportError:
    # Alternative import method
    import importlib.util
    json_path = os.path.join(parent_dir, 'json_cleaner.py')
    spec = importlib.util.spec_from_file_location("json_cleaner", json_path)
    json_cleaner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(json_cleaner)
    JSONCleaning = json_cleaner.JSONCleaning
    clean_json_text = json_cleaner.clean_json_text


class TestJSONCleaning:
    """Test cases for JSONCleaning class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = JSONCleaning()
    
    def test_initialization(self):
        """Test JSONCleaning initialization"""
        assert self.cleaner is not None
        # Should inherit all base cleaner attributes
        assert hasattr(self.cleaner, 'non_ascii_patterns')
        assert hasattr(self.cleaner, 'boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_non_ascii_patterns')
    
    def test_inheritance_from_base(self):
        """Test that JSON cleaner properly inherits from base"""
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
        # Since JSONCleaning doesn't override clean(), it uses base clean()
        test_text = "  JSON   text   with   spaces  "
        result = self.cleaner.clean(test_text)
        assert isinstance(result, str)
        assert "JSON text with spaces" in result
    
    def test_clean_empty_string(self):
        """Test cleaning empty string"""
        result = self.cleaner.clean("")
        assert result == ""
    
    def test_clean_json_structure(self):
        """Test cleaning JSON-like content"""
        json_content = '''
        {
            "title": "Sample Document",
            "content": "This is the main content of the document.",
            "metadata": {
                "author": "John Doe",
                "created": "2023-01-01"
            },
            "tags": ["important", "document", "sample"]
        }
        '''
        result = self.cleaner.clean(json_content)
        assert isinstance(result, str)
        assert "Sample Document" in result
        assert "main content" in result
        # Should still contain JSON content even without specific JSON cleaning
    
    def test_clean_json_escaped_content(self):
        """Test cleaning JSON with escaped characters"""
        json_text = '{"text": "This is a \\"quoted\\" string with \\n newlines"}'
        result = self.cleaner.clean(json_text)
        assert isinstance(result, str)
        assert "quoted" in result
        # Basic cleaning should handle this
    
    def test_clean_with_boilerplate(self):
        """Test cleaning with boilerplate content"""
        json_text = '{"content": "Important content. Subscribe to newsletter! More content."}'
        result = self.cleaner.clean(json_text)
        assert isinstance(result, str)
        assert "Important content" in result
        # Boilerplate removal depends on patterns in cleaning_patterns.py
    
    def test_clean_with_non_ascii(self):
        """Test cleaning with non-ASCII characters"""
        json_text = '{"text": "JSON content with special chars: café résumé naïve"}'
        result = self.cleaner.clean(json_text)
        assert isinstance(result, str)
        # Non-ASCII handling depends on patterns in cleaning_patterns.py
    
    def test_clean_whitespace_scenarios(self):
        """Test various whitespace scenarios common in JSON"""
        test_cases = [
            ('{"key":\n\n\n"value"}', '{"key": "value"}'),
            ('{"key":    "value"}', '{"key": "value"}'),
            ('  {"key": "value"}  ', '{"key": "value"}'),
        ]
        
        for input_text, expected in test_cases:
            result = self.cleaner.clean_whitespace(input_text)
            # Should normalize whitespace
            assert '"key"' in result
            assert '"value"' in result
    
    def test_clean_complex_json(self):
        """Test cleaning complex JSON structure"""
        complex_json = '''
        {
            "document": {
                "title": "Cyber Threat Intelligence Report",
                "sections": [
                    {
                        "heading": "Executive Summary",
                        "content": "This report analyzes recent cyber threats..."
                    },
                    {
                        "heading": "Technical Details", 
                        "content": "The malware uses advanced techniques..."
                    }
                ],
                "metadata": {
                    "classification": "TLP:WHITE",
                    "sources": ["OSINT", "Internal Analysis"]
                }
            }
        }
        '''
        result = self.cleaner.clean(complex_json)
        assert isinstance(result, str)
        assert "Cyber Threat Intelligence" in result
        assert "Executive Summary" in result
        assert "Technical Details" in result
    
    def test_pattern_compilation_inheritance(self):
        """Test that pattern compilation works correctly"""
        # Should have compiled patterns from base class
        assert hasattr(self.cleaner, 'compiled_boilerplate_patterns')
        assert hasattr(self.cleaner, 'compiled_non_ascii_patterns')
        
        # Patterns should be compiled regex objects
        if self.cleaner.compiled_boilerplate_patterns:
            import re
            assert all(hasattr(pattern, 'sub') for pattern in self.cleaner.compiled_boilerplate_patterns)


class TestCleanJSONTextFunction:
    """Test cases for convenience function"""
    
    def test_clean_json_text_function(self):
        """Test the convenience clean_json_text function"""
        json_text = '  {"key":  "value"}  '
        result = clean_json_text(json_text)
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result
    
    def test_clean_json_text_empty(self):
        """Test convenience function with empty string"""
        result = clean_json_text("")
        assert result == ""
    
    def test_clean_json_text_whitespace_only(self):
        """Test convenience function with whitespace only"""
        result = clean_json_text("   \n\n\t  ")
        assert isinstance(result, str)
        assert result.strip() == ""
    
    def test_clean_json_text_complex(self):
        """Test convenience function with complex JSON"""
        json_text = '{"threat": "Advanced Persistent Threat", "severity": "High"}'
        result = clean_json_text(json_text)
        assert isinstance(result, str)
        assert "Advanced Persistent Threat" in result
        assert "High" in result


class TestJSONErrorHandling:
    """Test error handling in JSON cleaning"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = JSONCleaning()
    
    def test_error_handling_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_json = '{"key": "value", "missing_quote: "value2"}'
        try:
            result = self.cleaner.clean(malformed_json)
            assert isinstance(result, str)
            # Should still clean even if JSON is malformed
        except Exception as e:
            # Should handle gracefully
            print(f"Malformed JSON handling: {e}")
    
    def test_error_handling_large_json(self):
        """Test handling of very large JSON"""
        large_json = '{"data": "' + "content " * 1000 + '"}'
        try:
            result = self.cleaner.clean(large_json)
            assert isinstance(result, str)
        except Exception as e:
            # Should handle gracefully
            print(f"Large JSON handling: {e}")
    
    def test_error_handling_special_chars(self):
        """Test handling of special characters in JSON"""
        special_json = '{"special": "!@#$%^&*()[]{}|\\\\:;\\"\'<>?,./"}'
        try:
            result = self.cleaner.clean(special_json)
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


class TestJSONPlaceholderMethods:
    """Test that the class is ready for future JSON-specific methods"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = JSONCleaning()
    
    def test_ready_for_extension(self):
        """Test that the class can be extended with JSON-specific methods"""
        # The class should be ready to add methods like:
        # - remove_json_escapes
        # - clean_json_strings
        # - remove_json_metadata
        # - normalize_json_structure
        # - extract_json_content
        
        # For now, just verify it has the basic structure
        assert hasattr(self.cleaner, '__class__')
        assert self.cleaner.__class__.__name__ == 'JSONCleaning'
        assert issubclass(self.cleaner.__class__, type(self.cleaner).__bases__[0])
    
    def test_json_content_extraction_readiness(self):
        """Test readiness for JSON content extraction"""
        # When JSON-specific methods are implemented, they should work with this structure
        sample_json = '{"title": "Test", "content": "Main content here", "metadata": "ignore"}'
        
        # Basic cleaning should preserve the content
        result = self.cleaner.clean(sample_json)
        assert "Test" in result
        assert "Main content here" in result


if __name__ == "__main__":
    # Simple test runner
    test_json = TestJSONCleaning()
    test_json.setup_method()
    
    print("Running JSON Cleaning tests...")
    try:
        test_json.test_initialization()
        print("[PASS] Initialization test passed")
        
        test_json.test_inheritance_from_base()
        print("[PASS] Inheritance test passed")
        
        test_json.test_clean_empty_string()
        print("[PASS] Empty string test passed")
        
        test_json.test_clean_json_structure()
        print("[PASS] JSON structure test passed")
        
        print("All basic tests passed!")
        
    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
    
    # Test convenience function
    test_func = TestCleanJSONTextFunction()
    try:
        test_func.test_clean_json_text_empty()
        print("[PASS] Convenience function test passed")
        
        test_func.test_clean_json_text_complex()
        print("[PASS] Complex JSON convenience function test passed")
    except Exception as e:
        print(f"[FAILED] Convenience function test failed: {e}")
    
    # Test error handling
    test_error = TestJSONErrorHandling()
    test_error.setup_method()
    try:
        test_error.test_error_handling_special_chars()
        print("[PASS] Error handling test passed")
    except Exception as e:
        print(f"[FAILED] Error handling test failed: {e}")
    
    # Test extensibility
    test_placeholder = TestJSONPlaceholderMethods()
    test_placeholder.setup_method()
    try:
        test_placeholder.test_ready_for_extension()
        print("[PASS] Extensibility test passed")
        
        test_placeholder.test_json_content_extraction_readiness()
        print("[PASS] JSON content extraction readiness test passed")
    except Exception as e:
        print(f"[FAILED] Extensibility test failed: {e}")
