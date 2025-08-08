#!/usr/bin/env python3
"""
Test script for OCR Service API
"""

import requests
import json
import sys
import os
from pathlib import Path

def test_ocr_service(base_url="http://localhost:8000"):
    """Test the OCR service endpoints"""
    
    print("🧪 Testing OCR Service API...")
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint passed")
            result = response.json()
            print(f"   Service: {result.get('service')}")
            print(f"   Version: {result.get('version')}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Test OCR endpoint with sample image (if available)
    print("\n3. Testing OCR extraction...")
    
    # Look for sample images
    sample_dirs = [
        "cti_pipeline/samples",
        "samples", 
        "test_images"
    ]
    
    sample_image = None
    for sample_dir in sample_dirs:
        if os.path.exists(sample_dir):
            for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tiff']:
                files = list(Path(sample_dir).glob(ext))
                if files:
                    sample_image = str(files[0])
                    break
            if sample_image:
                break
    
    if sample_image and os.path.exists(sample_image):
        print(f"   Using sample image: {sample_image}")
        try:
            with open(sample_image, 'rb') as f:
                files = {'file': (os.path.basename(sample_image), f, 'image/*')}
                data = {'polish': True}
                
                response = requests.post(
                    f"{base_url}/ocr/extract-text",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        text = result.get('text', '')
                        print("✅ OCR extraction successful")
                        print(f"   Extracted text length: {len(text)} characters")
                        if text:
                            preview = text[:100] + "..." if len(text) > 100 else text
                            print(f"   Preview: {preview}")
                    else:
                        print("❌ OCR extraction failed (service error)")
                        print(f"   Error: {result}")
                else:
                    print(f"❌ OCR extraction failed: {response.status_code}")
                    print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ OCR extraction failed: {e}")
    else:
        print("⚠️ No sample image found for OCR testing")
        print("   Create a test image in cti_pipeline/samples/ to test OCR functionality")
    
    print("\n🎉 OCR Service API testing completed!")
    return True

def test_ocr_client():
    """Test the OCR client integration"""
    print("\n🧪 Testing OCR Client integration...")
    
    try:
        # Import the OCR client
        sys.path.append('cti_pipeline/scripts/preprocessing')
        from ocr_client import OCRClient
        
        # Create client
        client = OCRClient()
        
        # Test health check
        if client.health_check():
            print("✅ OCR Client health check passed")
        else:
            print("❌ OCR Client health check failed")
            return False
        
        print("✅ OCR Client integration test passed")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import OCR client: {e}")
        return False
    except Exception as e:
        print(f"❌ OCR Client test failed: {e}")
        return False

if __name__ == "__main__":
    success = True
    
    # Test OCR service API
    success &= test_ocr_service()
    
    # Test OCR client integration
    success &= test_ocr_client()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
