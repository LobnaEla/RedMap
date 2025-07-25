"""
Test Runner for Extraction Module

This script runs all tests for the extraction classes.
Usage: python run_tests.py
"""

import sys
import os
import importlib.util

# Add the parent directory to the path to import the extraction modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

def run_all_tests():
    """Run all tests for the extraction module"""
    
    print("=" * 60)
    print("RUNNING ALL EXTRACTION MODULE TESTS")
    print("=" * 60)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'total': 0
    }
    
    # Test modules to run
    test_files = [
        'test_base_extraction',
        'test_pdf_extraction',
        'test_html_extraction',
        'test_json_extraction',
        'test_csv_extraction',
        'test_txt_extraction'
    ]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    for test_file in test_files:
        print(f"\n{'-' * 40}")
        print(f"Running {test_file}")
        print(f"{'-' * 40}")
        
        try:
            # Import the test module
            test_path = os.path.join(current_dir, f'{test_file}.py')
            spec = importlib.util.spec_from_file_location(test_file, test_path)
            test_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(test_module)
            
            # Run tests
            if hasattr(test_module, 'run_tests'):
                passed, failed = test_module.run_tests()
                test_results['passed'] += passed
                test_results['failed'] += failed
                test_results['total'] += (passed + failed)
            else:
                print(f"Warning: {test_file} does not have a run_tests function")
                
        except Exception as e:
            print(f"Error running {test_file}: {str(e)}")
            test_results['failed'] += 1
            test_results['total'] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
    else:
        print(f"\n❌ {test_results['failed']} tests failed")
    
    return test_results['failed'] == 0


def run_specific_test(test_name):
    """Run a specific test module"""
    
    print(f"Running {test_name}...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_path = os.path.join(current_dir, f'{test_name}.py')
    
    if not os.path.exists(test_path):
        print(f"Test file {test_name}.py not found")
        return False
    
    try:
        # Import the test module
        spec = importlib.util.spec_from_file_location(test_name, test_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Run tests
        if hasattr(test_module, 'run_tests'):
            passed, failed = test_module.run_tests()
            return failed == 0
        else:
            print(f"Warning: {test_name} does not have a run_tests function")
            return False
            
    except Exception as e:
        print(f"Error running {test_name}: {str(e)}")
        return False


def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) > 1:
        # Run specific test
        test_name = sys.argv[1]
        if not test_name.startswith('test_'):
            test_name = f'test_{test_name}'
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
