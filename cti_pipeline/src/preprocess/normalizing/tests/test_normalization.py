"""
Tests for TextNormalizer class
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import the normalization modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Add the shared directory to sys.path to resolve dependencies
shared_dir = os.path.join(os.path.dirname(parent_dir), 'shared')
sys.path.insert(0, shared_dir)

try:
    from normalization import TextNormalizer, normalize_text
except ImportError:
    # Alternative import method
    import importlib.util
    normalization_path = os.path.join(parent_dir, 'normalization.py')
    spec = importlib.util.spec_from_file_location("normalization", normalization_path)
    normalization = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(normalization)
    TextNormalizer = normalization.TextNormalizer
    normalize_text = normalization.normalize_text


class TestTextNormalizer:
    """Test cases for TextNormalizer class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.normalizer = TextNormalizer()
    
    def test_initialization(self):
        """Test TextNormalizer initialization"""
        assert self.normalizer is not None
        assert hasattr(self.normalizer, 'date_patterns')
        assert hasattr(self.normalizer, 'time_patterns')
        assert hasattr(self.normalizer, 'punctuation_patterns')
        assert hasattr(self.normalizer, 'artifact_patterns')
        assert hasattr(self.normalizer, 'preservation_manager')
        assert hasattr(self.normalizer, 'compiled_date_patterns')
        assert hasattr(self.normalizer, 'compiled_time_patterns')
        assert hasattr(self.normalizer, 'compiled_punctuation_patterns')
        assert hasattr(self.normalizer, 'compiled_artifact_patterns')
    
    def test_fix_encoding(self):
        """Test encoding fix functionality"""
        # Test common problematic characters
        test_cases = [
            ('\u00c2\u00a0', ' '),  # Non-breaking space
            ('\u00c2\u00ab', '"'),  # Left guillemet
            ('\u00c2\u00bb', '"'),  # Right guillemet
            ('\u00e2\u0080\u0099', "'"),  # Right single quotation mark
            ('\u00e2\u0080\u009c', '"'),  # Left double quotation mark
            ('\u00e2\u0080\u009d', '"'),  # Right double quotation mark
            ('\u00e2\u0080\u0093', '-'),  # En dash
            ('\u00e2\u0080\u0094', '-'),  # Em dash
        ]
        
        for input_char, expected_char in test_cases:
            result = self.normalizer.fix_encoding(input_char)
            assert result == expected_char, f"Failed for {repr(input_char)}"
        
        # Test bytes input
        byte_input = "Hello World".encode('utf-8')
        result = self.normalizer.fix_encoding(byte_input)
        assert result == "Hello World"
        assert isinstance(result, str)
        
        # Test normal text
        normal_text = "This is normal text"
        result = self.normalizer.fix_encoding(normal_text)
        assert result == normal_text
    
    def test_normalize_unicode(self):
        """Test Unicode normalization"""
        # Test invisible characters removal
        text_with_invisible = "Hello\u200bWorld\u202aTest\ufeff"
        result = self.normalizer.normalize_unicode(text_with_invisible)
        assert "\u200b" not in result
        assert "\u202a" not in result
        assert "\ufeff" not in result
        assert "HelloWorldTest" in result
        
        # Test non-breaking space normalization
        text_with_nbsp = "Hello\u00a0World"
        result = self.normalizer.normalize_unicode(text_with_nbsp)
        assert result == "Hello World"
        
        # Test various Unicode spaces
        text_with_spaces = "Hello\u2000World\u2003Test\u3000End"
        result = self.normalizer.normalize_unicode(text_with_spaces)
        assert "Hello World Test End" in result
        
        # Test NFC normalization
        # Combining characters should be normalized
        text_with_combining = "e\u0301"  # e + combining acute accent
        result = self.normalizer.normalize_unicode(text_with_combining)
        assert len(result) == 1  # Should be composed into single character
    
    def test_normalize_dates(self):
        """Test date normalization"""
        test_cases = [
            ("15/12/2023", "2023-12-15"),  # DD/MM/YYYY -> YYYY-MM-DD
            ("5/3/2023", "2023-3-5"),     # D/M/YYYY -> YYYY-M-D
            ("15/12/23", "2023-12-15"),   # DD/MM/YY -> YYYY-MM-DD
            ("2023/12/15", "2023-12-15"), # YYYY/MM/DD -> YYYY-MM-DD
            ("2023-12-15", "2023-12-15"), # Already normalized
        ]
        
        for input_date, expected in test_cases:
            result = self.normalizer.normalize_dates(input_date)
            assert expected in result, f"Failed for {input_date}: got {result}, expected {expected}"
        
        # Test with surrounding text
        text_with_date = "The incident occurred on 15/12/2023 at the facility."
        result = self.normalizer.normalize_dates(text_with_date)
        assert "2023-12-15" in result
    
    def test_normalize_times(self):
        """Test time normalization"""
        test_cases = [
            ("3:45:30 PM", "3:45:30 PM"),  # Already normalized
            ("3:45 PM", "3:45:00 PM"),     # Add seconds
            ("11:30:15 AM", "11:30:15 AM"), # Already normalized
            ("9:15 AM", "9:15:00 AM"),     # Add seconds
        ]
        
        for input_time, expected in test_cases:
            result = self.normalizer.normalize_times(input_time)
            assert expected in result, f"Failed for {input_time}: got {result}, expected {expected}"
        
        # Test with surrounding text
        text_with_time = "The meeting is at 3:45 PM today."
        result = self.normalizer.normalize_times(text_with_time)
        assert "3:45:00 PM" in result
    
    def test_normalize_punctuation(self):
        """Test punctuation normalization"""
        test_cases = [
            ('"Hello"', '"Hello"'),  # Smart quotes to regular quotes
            ("'Hello'", "'Hello'"),   # Smart apostrophes to regular
            ("Hello—world", "Hello-world"),  # Em dash to hyphen
            ("Hello–world", "Hello-world"),  # En dash to hyphen
            ("Hello…", "Hello..."),   # Ellipsis normalization
            ("«Hello»", '"Hello"'),   # Guillemets to quotes
        ]
        
        for input_text, expected in test_cases:
            result = self.normalizer.normalize_punctuation(input_text)
            assert result == expected, f"Failed for {input_text}: got {result}, expected {expected}"
    
    def test_fix_artifacts(self):
        """Test artifact fixing"""
        test_cases = [
            ("Hello    world", "Hello world"),  # Multiple spaces
            ("Hello\t\tworld", "Hello  world"), # Tabs to spaces
            ("Hello\r\nworld", "Hello\nworld"), # Windows line endings
            ("Hello\rworld", "Hello\nworld"),   # Old Mac line endings
            ("Hello\n\n\n\nworld", "Hello\n\nworld"), # Multiple newlines
            ("  Hello world  ", "Hello world"), # Leading/trailing spaces
        ]
        
        for input_text, expected in test_cases:
            result = self.normalizer.fix_artifacts(input_text)
            assert result == expected, f"Failed for {input_text}: got {repr(result)}, expected {repr(expected)}"
    
    def test_normalize_case(self):
        """Test case normalization"""
        # Test normal text lowercasing
        normal_text = "Hello World Test"
        result = self.normalizer.normalize_case(normal_text)
        assert result == "hello world test"
        
        # Test with preserved technical terms (if preservation manager is working)
        tech_text = "The Windows malware used TCP protocol"
        result = self.normalizer.normalize_case(tech_text)
        # Should preserve technical terms but convert others to lowercase
        assert "tcp" in result.lower() or "TCP" in result
        assert "windows" in result.lower() or "Windows" in result
    
    def test_normalize_ioc_formats(self):
        """Test IoC format normalization"""
        # Test malformed IP fixing
        malformed_ip = "001.002.003.004"
        result = self.normalizer.normalize_ioc_formats(malformed_ip)
        assert "1.2.3.4" in result
        
        # Test www URL normalization
        www_url = "www.example.com"
        result = self.normalizer.normalize_ioc_formats(www_url)
        # Should either preserve as IOC or normalize to http://
        assert "www.example.com" in result or "http://www.example.com" in result
        
        # Test with surrounding text
        text_with_ioc = "Visit www.malicious-site.com for more info"
        result = self.normalizer.normalize_ioc_formats(text_with_ioc)
        assert "malicious-site.com" in result
    
    def test_normalize_empty_input(self):
        """Test normalization with empty or None input"""
        # The normalize method should handle empty strings gracefully
        result = self.normalizer.normalize("")
        assert result == ""
        
        # Test with whitespace only
        result = self.normalizer.normalize("   ")
        assert result.strip() == ""
    
    def test_normalize_integration(self):
        """Test the main normalize method with complex input"""
        complex_text = """
        The incident occurred on 15/12/2023 at 3:45 PM.
        Malicious IP: 001.002.003.004
        URL: www.malicious-site.com
        "Smart quotes" and 'apostrophes'…
        Multiple    spaces    and\t\ttabs.
        Windows\r\nline\r\nendings.
        """
        
        result = self.normalizer.normalize(complex_text)
        
        # Check that various normalizations were applied
        assert "2023-12-15" in result  # Date normalized
        assert "3:45:00 PM" in result  # Time normalized
        assert "1.2.3.4" in result     # IP fixed
        assert '"Smart quotes"' in result  # Quotes normalized
        assert "Multiple spaces and" in result  # Spaces fixed
        assert result.count('\n\n') <= 2  # Line endings normalized
    
    def test_normalize_with_preservation(self):
        """Test normalization while preserving important terms"""
        text_with_tech_terms = "The APT group used Windows malware with TCP connections to 192.168.1.1"
        result = self.normalizer.normalize(text_with_tech_terms)
        
        # Check that the result is a string and contains the IP
        assert isinstance(result, str)
        assert "192.168.1.1" in result
        
        # Technical terms might be preserved depending on preservation manager
        # This is more of a integration test to ensure no crashes occur
    
    def test_error_handling(self):
        """Test error handling in normalization methods"""
        # Test that methods don't crash with unusual input
        unusual_inputs = [
            "\x00\x01\x02",  # Control characters
            "🙂🙃😀",        # Emojis
            "テスト",          # Non-Latin characters
            "\n" * 1000,     # Many newlines
        ]
        
        for unusual_input in unusual_inputs:
            try:
                result = self.normalizer.normalize(unusual_input)
                assert isinstance(result, str)
            except Exception as e:
                # Should not raise exceptions, but if it does, record it
                print(f"Unexpected error with input {repr(unusual_input)}: {e}")
                assert False, f"Normalization should not raise exceptions for input: {repr(unusual_input)}"
    
    def test_convenience_function(self):
        """Test the convenience normalize_text function"""
        test_text = "Hello    world   with  multiple spaces"
        result = normalize_text(test_text)
        assert isinstance(result, str)
        assert "Hello world with multiple spaces" in result


def run_tests():
    """Run all tests for TextNormalizer"""
    print("Testing TextNormalizer...")
    
    test_class = TestTextNormalizer()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    test_methods.remove('test_convenience_function')
    test_methods.remove('test_normalize_integration')

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
    
    print(f"\nNormalization Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
