"""
Tests for BaseExtraction class
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from base import BaseExtraction, ExtractionResult, extract_text_from_file, extract_with_result
except ImportError:
    # Alternative import method
    import importlib.util
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    BaseExtraction = base.BaseExtraction
    ExtractionResult = base.ExtractionResult
    extract_text_from_file = base.extract_text_from_file
    extract_with_result = base.extract_with_result


class TestBaseExtraction:
    """Test cases for BaseExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = BaseExtraction()
    
    def test_initialization(self):
        """Test BaseExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert isinstance(self.extractor.supported_formats, set)
    
    def test_extract_from_file_not_found(self):
        """Test extraction from non-existent file"""
        result = self.extractor.extract_from_file("non_existent_file.txt")
        assert isinstance(result, ExtractionResult)
        assert result.success == False
        assert "File not found" in result.error_message
    
    def test_extract_from_file_unsupported_format(self):
        """Test extraction from unsupported file format"""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == False
            assert "Unsupported file format" in result.error_message
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_text_not_implemented(self):
        """Test that _extract_text raises NotImplementedError"""
        try:
            self.extractor._extract_text("dummy_path", ".txt")
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            assert True
    
    def test_extraction_result_dataclass(self):
        """Test ExtractionResult dataclass"""
        result = ExtractionResult(
            success=True,
            text="test text",
            file_path="/path/to/file.txt",
            file_format=".txt"
        )
        
        assert result.success == True
        assert result.text == "test text"
        assert result.file_path == "/path/to/file.txt"
        assert result.file_format == ".txt"
        assert result.error_message is None
        assert result.metadata is None
    
    def test_extraction_result_with_metadata(self):
        """Test ExtractionResult with metadata"""
        metadata = {"original_length": 100, "file_size": 1024}
        result = ExtractionResult(
            success=True,
            text="test text",
            file_path="/path/to/file.txt",
            file_format=".txt",
            metadata=metadata
        )
        
        assert result.metadata == metadata
        assert result.metadata["original_length"] == 100
        assert result.metadata["file_size"] == 1024


def run_tests():
    """Run all tests for BaseExtraction"""
    print("Testing BaseExtraction...")
    
    test_class = TestBaseExtraction()
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
    
    print(f"\nBase Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
