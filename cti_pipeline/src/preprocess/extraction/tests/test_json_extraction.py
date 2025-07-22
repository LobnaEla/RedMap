"""
Tests for JSONExtraction class
"""

import sys
import os
import tempfile
import json

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from json_extractor import JSONExtraction, extract_json_text
    from base import ExtractionResult
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Import json_extractor
    json_path = os.path.join(parent_dir, 'json_extractor.py')
    spec = importlib.util.spec_from_file_location("json_extractor", json_path)
    json_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(json_module)
    JSONExtraction = json_module.JSONExtraction
    extract_json_text = json_module.extract_json_text
    
    # Import base
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ExtractionResult = base.ExtractionResult


class TestJSONExtraction:
    """Test cases for JSONExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = JSONExtraction()
    
    def test_initialization(self):
        """Test JSONExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert '.json' in self.extractor.supported_formats
        assert len(self.extractor.supported_formats) == 1
    
    def test_supported_formats(self):
        """Test that JSON extractor only supports JSON files"""
        assert self.extractor.supported_formats == {'.json'}
    
    def test_extract_from_simple_json(self):
        """Test extraction from simple JSON file"""
        json_content = {
            "name": "Test Object",
            "description": "This is a test JSON object",
            "values": [1, 2, 3, 4],
            "nested": {
                "key": "value",
                "number": 42
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as temp_file:
            json.dump(json_content, temp_file)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Test Object" in result.text
            assert "This is a test JSON object" in result.text
            assert result.file_format == ".json"
            assert result.metadata is not None
            assert "original_length" in result.metadata
            assert "file_size" in result.metadata
            
            # Verify the text is valid JSON
            parsed = json.loads(result.text)
            assert parsed["name"] == "Test Object"
            assert parsed["nested"]["number"] == 42
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_array_json(self):
        """Test extraction from JSON array"""
        json_content = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as temp_file:
            json.dump(json_content, temp_file)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Item 1" in result.text
            assert "Item 2" in result.text
            assert result.file_format == ".json"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_nonexistent_json(self):
        """Test extraction from non-existent JSON file"""
        result = self.extractor.extract_from_file("non_existent.json")
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
    
    def test_extract_from_invalid_json(self):
        """Test extraction from invalid JSON file"""
        invalid_json = '{"name": "Test", "incomplete": '
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(invalid_json)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == False
            assert "Extraction failed" in result.error_message
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_json_method(self):
        """Test _extract_json method directly"""
        json_content = {"test": "direct method"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as temp_file:
            json.dump(json_content, temp_file)
            temp_file_path = temp_file.name
        
        try:
            text = self.extractor._extract_json(temp_file_path)
            assert "direct method" in text
            assert isinstance(text, str)
            parsed = json.loads(text)
            assert parsed["test"] == "direct method"
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function(self):
        """Test convenience function extract_json_text"""
        json_content = {"message": "convenience function test"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False, encoding='utf-8') as temp_file:
            json.dump(json_content, temp_file)
            temp_file_path = temp_file.name
        
        try:
            text = extract_json_text(temp_file_path)
            assert "convenience function test" in text
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function_with_nonexistent_file(self):
        """Test convenience function with non-existent file"""
        result = extract_json_text("non_existent.json")
        assert result == ""


def run_tests():
    """Run all tests for JSONExtraction"""
    print("Testing JSONExtraction...")
    
    test_class = TestJSONExtraction()
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
    
    print(f"\nJSON Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
