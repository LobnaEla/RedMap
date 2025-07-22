"""
Test Runner for Cleaning Module

This script runs all tests for the cleaning classes.
Usage: python run_tests.py
"""

import sys
import os
import importlib.util

# Add the parent directory to the path to import the cleaning modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def run_all_tests():
    """Run all tests for the cleaning module"""
    
    print("=" * 60)
    print("RUNNING ALL CLEANING MODULE TESTS")
    print("=" * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # Test modules to run
    test_files = [
        'test_base_cleaning.py',
        'test_html_cleaning.py',
        'test_ocr_cleaning.py', 
        'test_pdf_cleaning.py',
        'test_json_cleaning.py'
    ]
    
    for test_file in test_files:
        module_name = test_file.replace('.py', '').upper()
        print(f"\n{'='*20} {module_name} {'='*20}")
        
        try:
            # Execute the test file directly
            test_file_path = os.path.join(os.path.dirname(__file__), test_file)
            
            if os.path.exists(test_file_path):
                # Redirect stdout to capture test output
                import subprocess
                result = subprocess.run([sys.executable, test_file_path], 
                                      capture_output=True, text=True, cwd=os.path.dirname(__file__))
                
                if result.returncode == 0:
                    print(result.stdout)
                    test_results['passed'] += 1
                else:
                    print(f"[FAILED] {test_file} failed:")
                    print(result.stdout)
                    if result.stderr:
                        print("Errors:")
                        print(result.stderr)
                    test_results['failed'] += 1
            else:
                print(f"[FAILED] Test file {test_file} not found")
                test_results['failed'] += 1
                
        except Exception as e:
            print(f"[FAILED] Error running {test_file}: {e}")
            test_results['failed'] += 1
        
        test_results['total'] += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    if test_results['failed'] == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {test_results['failed']} test(s) failed")
    
    return test_results['failed'] == 0


def run_specific_test(test_name):
    """Run a specific test module"""
    
    print(f"Running {test_name}...")
    
    test_file = f'test_{test_name}_cleaning.py'
    test_file_path = os.path.join(os.path.dirname(__file__), test_file)
    
    try:
        if os.path.exists(test_file_path):
            import subprocess
            result = subprocess.run([sys.executable, test_file_path], 
                                  capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            print(result.stdout)
            if result.stderr:
                print("Errors:")
                print(result.stderr)
            
            return result.returncode == 0
        else:
            print(f"[FAILED] Test file {test_file} not found")
            return False
            
    except Exception as e:
        print(f"[FAILED] Error running {test_file}: {e}")
        return False


def test_imports():
    """Test that all cleaning modules can be imported"""
    
    print("Testing module imports...")
    
    modules = [
        ('base.py', 'BaseCleaning'),
        ('html_cleaner.py', 'HTMLCleaning'),
        ('ocr_cleaner.py', 'OCRCleaning'),
        ('pdf_cleaner.py', 'PDFCleaning'), 
        ('json_cleaner.py', 'JSONCleaning')
    ]
    
    for module_file, class_name in modules:
        try:
            module_path = os.path.join(parent_dir, module_file)
            if os.path.exists(module_path):
                # Try to import using importlib
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_file.replace('.py', ''), module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if the class exists
                if hasattr(module, class_name):
                    print(f"[PASS] {module_file} ({class_name}) imported successfully")
                else:
                    print(f"[FAILED] {class_name} not found in {module_file}")
                    return False
            else:
                print(f"[FAILED] Module file {module_file} not found")
                return False
        except Exception as e:
            print(f"[FAILED] Error importing {module_file}: {e}")
            return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run cleaning module tests')
    parser.add_argument('--test', type=str, help='Run specific test (base, html, ocr, pdf, json)')
    parser.add_argument('--imports', action='store_true', help='Test imports only')
    
    args = parser.parse_args()
    
    if args.imports:
        success = test_imports()
    elif args.test:
        success = run_specific_test(args.test)
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
