"""Debug script for normalization tests"""

import sys
import os

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

print("=" * 50)
print("DEBUGGING FAILING TESTS")
print("=" * 50)

print("\n1. Testing convenience function:")
test_text = "Hello    world   with  multiple spaces"
try:
    result = normalize_text(test_text)
    print(f"Input: {repr(test_text)}")
    print(f"Output: {repr(result)}")
    print(f"Expected substring: 'Hello world with multiple spaces'")
    print(f"Contains expected: {'Hello world with multiple spaces' in result}")
    print(f"Type: {type(result)}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing integration:")
complex_text = """
        The incident occurred on 15/12/2023 at 3:45 PM.
        Malicious IP: 001.002.003.004
        URL: www.malicious-site.com
        "Smart quotes" and 'apostrophes'…
        Multiple    spaces    and\t\ttabs.
        Windows\r\nline\r\nendings.
        """

try:
    normalizer = TextNormalizer()
    result = normalizer.normalize(complex_text)
    print(f"Input length: {len(complex_text)}")
    print(f"Output length: {len(result)}")
    print(f"Contains '2023-12-15': {'2023-12-15' in result}")
    print(f"Contains '3:45:00 PM': {'3:45:00 PM' in result}")
    print(f"Contains '1.2.3.4': {'1.2.3.4' in result}")
    print(f"Contains 'Smart quotes': {'Smart quotes' in result}")
    print(f"Contains 'Multiple spaces and': {'Multiple spaces and' in result}")
    print(f"Newline count: {result.count('\\n\\n')}")
    print("\nFirst 200 chars of result:")
    print(repr(result[:200]))
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
