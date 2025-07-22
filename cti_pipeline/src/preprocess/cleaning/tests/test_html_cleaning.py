"""
Tests for HTMLCleaning class
"""

import sys
import os

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from html_cleaner import HTMLCleaning, clean_html_text
except ImportError:
    # Alternative import method
    import importlib.util
    html_path = os.path.join(parent_dir, 'html_cleaner.py')
    spec = importlib.util.spec_from_file_location("html_cleaner", html_path)
    html_cleaner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(html_cleaner)
    HTMLCleaning = html_cleaner.HTMLCleaning
    clean_html_text = html_cleaner.clean_html_text


class TestHTMLCleaning:
    """Test cases for HTMLCleaning class"""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.cleaner = HTMLCleaning()
    
    def test_initialization(self):
        """Test HTMLCleaning initialization"""
        assert self.cleaner is not None
        # Should inherit all base cleaner attributes
        assert hasattr(self.cleaner, 'non_ascii_patterns')
        assert hasattr(self.cleaner, 'boilerplate_patterns')
    
    def test_remove_html_basic(self):
        """Test basic HTML tag removal"""
        test_cases = [
            ("<p>Hello world</p>", "Hello world"),
            ("<div><span>Text</span></div>", "Text"),
            ("<a href='link'>Click here</a>", "Click here"),
            ("No HTML here", "No HTML here"),
        ]
        
        for input_html, expected in test_cases:
            result = self.cleaner.remove_html(input_html)
            assert expected in result or result.strip() == expected.strip()
    
    def test_remove_html_complex(self):
        """Test complex HTML removal"""
        html_text = """
        <html>
            <head><title>Test</title></head>
            <body>
                <div class="content">
                    <h1>Main Title</h1>
                    <p>This is a <strong>paragraph</strong> with <em>formatting</em>.</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                    </ul>
                </div>
            </body>
        </html>
        """
        result = self.cleaner.remove_html(html_text)
        assert "Main Title" in result
        assert "paragraph" in result
        assert "Item 1" in result
        assert "<" not in result  # Should remove all HTML tags
    
    def test_remove_ads(self):
        """Test advertisement removal"""
        ad_text = "Important content. Advertisement: Buy now! More content."
        result = self.cleaner.remove_ads(ad_text)
        assert isinstance(result, str)
        # Exact behavior depends on ad patterns
    
    def test_remove_navigation(self):
        """Test navigation removal"""
        nav_text = "Content here. Home | About | Contact | Login. More content."
        result = self.cleaner.remove_navigation(nav_text)
        assert isinstance(result, str)
        # Should remove navigation elements
    
    def test_remove_buttons(self):
        """Test button removal"""
        button_text = "Content. Click here Subscribe now Download. More content."
        result = self.cleaner.remove_buttons(button_text)
        assert isinstance(result, str)
        # Should remove button-like text
    
    def test_clean_method_pipeline(self):
        """Test the complete HTML cleaning pipeline"""
        html_content = """
        <html>
            <body>
                <nav>Home | About | Contact</nav>
                <div class="content">
                    <h1>Article Title</h1>
                    <p>This is the main content of the article.</p>
                    <button>Subscribe</button>
                    <div class="ad">Advertisement content here</div>
                </div>
            </body>
        </html>
        """
        result = self.cleaner.clean(html_content)
        assert isinstance(result, str)
        assert "Article Title" in result
        assert "main content" in result
        # Should have removed HTML tags, nav, ads, and buttons
    
    def test_clean_empty_html(self):
        """Test cleaning empty HTML"""
        result = self.cleaner.clean("")
        assert result == ""
    
    def test_clean_malformed_html(self):
        """Test cleaning malformed HTML"""
        malformed_html = "<div><p>Unclosed tags <span>content</div>"
        result = self.cleaner.clean(malformed_html)
        assert isinstance(result, str)
        assert "content" in result
    
    def test_inheritance_from_base(self):
        """Test that HTML cleaner properly inherits from base"""
        # Should have access to base methods
        assert hasattr(self.cleaner, 'remove_boilerplate')
        assert hasattr(self.cleaner, 'clean_whitespace')
        assert hasattr(self.cleaner, 'remove_non_ascii')
        
        # Test base functionality still works
        test_text = "  Hello    world  "
        result = self.cleaner.clean_whitespace(test_text)
        assert result == "Hello world"


class TestCleanHTMLTextFunction:
    """Test cases for convenience function"""
    
    def test_clean_html_text_function(self):
        """Test the convenience clean_html_text function"""
        html_text = "<p>Hello <strong>world</strong></p>"
        result = clean_html_text(html_text)
        assert isinstance(result, str)
        assert "Hello" in result
        assert "world" in result
    
    def test_clean_html_text_empty(self):
        """Test convenience function with empty string"""
        result = clean_html_text("")
        assert result == ""


if __name__ == "__main__":
    # Simple test runner
    test_html = TestHTMLCleaning()
    test_html.setup_method()
    
    print("Running HTML Cleaning tests...")
    try:
        test_html.test_initialization()
        print("[PASS] Initialization test passed")
        
        test_html.test_clean_empty_html()
        print("[PASS] Empty HTML test passed")
        
        test_html.test_inheritance_from_base()
        print("[PASS] Inheritance test passed")
        
        print("All basic tests passed!")
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
    
    # Test convenience function
    test_func = TestCleanHTMLTextFunction()
    try:
        test_func.test_clean_html_text_empty()
        print("[PASS] Convenience function test passed")
    except Exception as e:
        print(f"[FAIL] Convenience function test failed: {e}")
