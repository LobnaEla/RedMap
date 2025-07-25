"""
Tests for CSVExtraction class
"""

import sys
import os
import tempfile
import csv

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from csv_extractor import CSVExtraction, extract_csv_text
    from base import ExtractionResult
except ImportError:
    # Alternative import method
    import importlib.util
    
    # Import csv_extractor
    csv_path = os.path.join(parent_dir, 'csv_extractor.py')
    spec = importlib.util.spec_from_file_location("csv_extractor", csv_path)
    csv_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(csv_module)
    CSVExtraction = csv_module.CSVExtraction
    extract_csv_text = csv_module.extract_csv_text
    
    # Import base
    base_path = os.path.join(parent_dir, 'base.py')
    spec = importlib.util.spec_from_file_location("base", base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    ExtractionResult = base.ExtractionResult


class TestCSVExtraction:
    """Test cases for CSVExtraction class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.extractor = CSVExtraction()
    
    def test_initialization(self):
        """Test CSVExtraction initialization"""
        assert self.extractor is not None
        assert hasattr(self.extractor, 'supported_formats')
        assert '.csv' in self.extractor.supported_formats
        assert len(self.extractor.supported_formats) == 1
    
    def test_supported_formats(self):
        """Test that CSV extractor only supports CSV files"""
        assert self.extractor.supported_formats == {'.csv'}
    
    def test_extract_from_simple_csv(self):
        """Test extraction from simple CSV file"""
        csv_data = [
            ["Name", "Age", "City"],
            ["John Doe", "30", "New York"],
            ["Jane Smith", "25", "Los Angeles"],
            ["Bob Johnson", "35", "Chicago"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8', newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(csv_data)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Name; Age; City" in result.text
            assert "John Doe; 30; New York" in result.text
            assert "Jane Smith; 25; Los Angeles" in result.text
            assert result.file_format == ".csv"
            assert result.metadata is not None
            assert "original_length" in result.metadata
            assert "file_size" in result.metadata
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_csv_with_quotes(self):
        """Test extraction from CSV file with quoted fields"""
        csv_content = '''Name,Description,Value
"Product A","High quality product, very useful","100.50"
"Product B","Another product with, comma in description","75.25"
"Product C","Simple product","50.00"'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8') as temp_file:
            temp_file.write(csv_content)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "Product A" in result.text
            assert "High quality product, very useful" in result.text
            assert result.file_format == ".csv"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_empty_csv(self):
        """Test extraction from empty CSV file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8') as temp_file:
            temp_file.write("")
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert result.text == ""
            assert result.file_format == ".csv"
        finally:
            os.unlink(temp_file_path)
    
    def test_extract_from_nonexistent_csv(self):
        """Test extraction from non-existent CSV file"""
        result = self.extractor.extract_from_file("non_existent.csv")
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
    
    def test_extract_csv_method(self):
        """Test _extract_csv method directly"""
        csv_data = [["Header1", "Header2"], ["Value1", "Value2"]]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8', newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(csv_data)
            temp_file_path = temp_file.name
        
        try:
            text = self.extractor._extract_csv(temp_file_path)
            assert "Header1; Header2" in text
            assert "Value1; Value2" in text
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function(self):
        """Test convenience function extract_csv_text"""
        csv_data = [["Test", "Data"], ["Row1", "Row2"]]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8', newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(csv_data)
            temp_file_path = temp_file.name
        
        try:
            text = extract_csv_text(temp_file_path)
            assert "Test; Data" in text
            assert "Row1; Row2" in text
            assert isinstance(text, str)
        finally:
            os.unlink(temp_file_path)
    
    def test_convenience_function_with_nonexistent_file(self):
        """Test convenience function with non-existent file"""
        result = extract_csv_text("non_existent.csv")
        assert result == ""
    
    def test_csv_with_special_characters(self):
        """Test CSV with special characters and different encodings"""
        csv_data = [
            ["Name", "Description"],
            ["Test Product", "Product with special chars: éàü"],
            ["Another Product", "Description with newline and comma, test"]
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, encoding='utf-8', newline='') as temp_file:
            writer = csv.writer(temp_file)
            writer.writerows(csv_data)
            temp_file_path = temp_file.name
        
        try:
            result = self.extractor.extract_from_file(temp_file_path)
            assert isinstance(result, ExtractionResult)
            assert result.success == True
            assert "éàü" in result.text
            assert result.file_format == ".csv"
        finally:
            os.unlink(temp_file_path)


def run_tests():
    """Run all tests for CSVExtraction"""
    print("Testing CSVExtraction...")
    
    test_class = TestCSVExtraction()
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
    
    print(f"\nCSV Extraction Tests: {passed} passed, {failed} failed")
    return passed, failed


if __name__ == "__main__":
    run_tests()
