"""
Tests for TXTExtraction class
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from txt_extractor import TXTExtraction, extract_txt_text
    from base import ExtractionResult
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Import txt_extractor
    txt_path = os.path.join(parent_dir, 'txt_extractor.py')
    spec = importlib.util.spec_from_file_location("txt_extractor", txt_path)
    txt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(txt_module)
    TXTExtraction = txt_module.TXTExtraction
    extract_txt_text = txt_module.extract_txt_text
    
    # Import base
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ExtractionResult = base.ExtractionResult


class TestTXTExtraction:
    """Test cases for TXTExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = TXTExtraction()
    
    def test_initialization(self):
        """Test TXTExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert '.txt' in self.extractor.supported_formats
        assert len(self.extractor.supported_formats) == 1
    
    def test_supported_formats(self):
        """Test that TXT extractor only supports TXT files"""
        assert self.extractor.supported_formats == {'.txt'}
    
    def test_extract_from_simple_txt(self):
        """Test extraction from simple text file"""
        text_content = """This is a simple text file.
It contains multiple lines.
Each line has different content.
This is for testing purposes."""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "This is a simple text file." in result.text
            assert "multiple lines" in result.text
            assert "testing purposes" in result.text
            assert result.file_format == ".txt"
            assert result.metadata is not None
            assert "original_length" in result.metadata
            assert "file_size" in result.metadata
            assert result.text == text_content
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_empty_txt(self):
        """Test extraction from empty text file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert result.text == ""
            assert result.file_format == ".txt"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_txt_with_special_characters(self):
        """Test extraction from text file with special characters"""
        text_content = """Text with special characters: éàüñç
Emojis and symbols: 😀 ★ ♥ ©
Mathematical symbols: ∑ ∆ π ∞
Currency symbols: $ € £ ¥"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "éàüñç" in result.text
            assert "😀" in result.text
            assert "∑ ∆ π ∞" in result.text
            assert result.text == text_content
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_large_txt(self):
        """Test extraction from larger text file"""
        lines = []
        for i in range(1000):
            lines.append(f"Line {i}: This is content for line number {i}")
        text_content = "\n".join(lines)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Line 0:" in result.text
            assert "Line 999:" in result.text
            assert len(result.text) > 10000  # Should be a substantial amount of text
            assert result.text == text_content
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_nonexistent_txt(self):
        """Test extraction from non-existent text file"""
        result = self.extractor.extract_from_file("non_existent.txt")
        assert isinstance(result, ExtractionResult)
        assert result.success == False
        assert "File not found" in result.error_message
    
    def test_extract_from_unsupported_format(self):
        """Test extraction from unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == False
            assert "Unsupported file format" in result.error_message
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_txt_method(self):
        """Test _extract_txt method directly"""
        text_content = "Direct method test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            text = self.extractor._extract_txt(temp_file_path)
            assert text == text_content
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function(self):
        """Test convenience function extract_txt_text"""
        text_content = "Convenience function test content"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(text_content)
            temp_file_path = temp_file.name
        
        try:
            text = extract_txt_text(temp_file_path)
            assert text == text_content
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function_with_nonexistent_file(self):
        """Test convenience function with non-existent file"""
        result = extract_txt_text("non_existent.txt")
        assert result == ""
    
    def test_extract_txt_with_different_line_endings(self):
        """Test extraction from text file with different line endings"""
        # Test with Windows line endings
        text_content = "Line 1\r\nLine 2\r\nLine 3"
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix=".txt", delete=False) as temp_file:
            temp_file.write(text_content.encode('utf-8'))
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Line 1" in result.text
            assert "Line 2" in result.text
            assert "Line 3" in result.text
        finally:
            os.unlink(temp_file_path)


def run_tests():
    """Run all tests for TXTExtraction"""
    print("Testing TXTExtraction...")
    
    test_class = TestTXTExtraction()
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
    
    print(f"\nTXT Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
