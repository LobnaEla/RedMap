"""
Tests for HTMLExtraction class
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from html_extractor import HTMLExtraction, extract_html_text
    from base import ExtractionResult
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Import html_extractor
    html_path = os.path.join(parent_dir, 'html_extractor.py')
    spec = importlib.util.spec_from_file_location("html_extractor", html_path)
    html_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(html_module)
    HTMLExtraction = html_module.HTMLExtraction
    extract_html_text = html_module.extract_html_text
    
    # Import base
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ExtractionResult = base.ExtractionResult


class TestHTMLExtraction:
    """Test cases for HTMLExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = HTMLExtraction()
    
    def test_initialization(self):
        """Test HTMLExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert '.html' in self.extractor.supported_formats
        assert '.htm' in self.extractor.supported_formats
        assert len(self.extractor.supported_formats) == 2
    
    def test_supported_formats(self):
        """Test that HTML extractor supports HTML and HTM files"""
        assert self.extractor.supported_formats == {'.html', '.htm'}
    
    def test_extract_from_simple_html(self):
        """Test extraction from simple HTML file"""
        html_content = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Test Header</h1>
            <p>This is a test paragraph.</p>
            <div>Some content in a div.</div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Test Header" in result.text
            assert "This is a test paragraph." in result.text
            assert "Some content in a div." in result.text
            assert result.file_format == ".html"
            assert result.metadata is not None
            assert "original_length" in result.metadata
            assert "file_size" in result.metadata
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_htm_file(self):
        """Test extraction from HTM file"""
        html_content = "<html><body><p>HTM test content</p></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".htm", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "HTM test content" in result.text
            assert result.file_format == ".htm"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_nonexistent_html(self):
        """Test extraction from non-existent HTML file"""
        result = self.extractor.extract_from_file("non_existent.html")
        assert isinstance(result, ExtractionResult)
        assert result.success == False
        assert "File not found" in result.error_message
    
    def test_extract_from_unsupported_format(self):
        """Test extraction from unsupported file format"""
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
    
    def test_extract_html_method(self):
        """Test _extract_html method directly"""
        html_content = "<html><body><p>Direct method test</p></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        try:
            text = self.extractor._extract_html(temp_file_path)
            assert "Direct method test" in text
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function(self):
        """Test convenience function extract_html_text"""
        html_content = "<html><body><p>Convenience function test</p></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".html", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        try:
            text = extract_html_text(temp_file_path)
            assert "Convenience function test" in text
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function_with_nonexistent_file(self):
        """Test convenience function with non-existent file"""
        result = extract_html_text("non_existent.html")
        assert result == ""


def run_tests():
    """Run all tests for HTMLExtraction"""
    print("Testing HTMLExtraction...")
    
    test_class = TestHTMLExtraction()
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
    
    print(f"\nHTML Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
