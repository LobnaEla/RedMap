"""
Test script for CTIChunker class.

This script tests the CTIChunker functionality by importing the chunker
and processing a sample CTI report.
"""
import os
import sys
import json
from pathlib import Path

# Add the project root to sys.path to allow for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=== CTI Chunker Test Script ===")
print(f"Project Root: {project_root}")
print(f"Python Path: {sys.path[:3]}...")  # Show first 3 paths
print()

# Test 1: Import the chunker
try:
    from cti_pipeline.scripts.preprocess.core.processors.chunking.chunker import CTIChunker
    print("✓ Successfully imported CTIChunker")
except ImportError as e:
    print(f"✗ Failed to import CTIChunker: {e}")
    sys.exit(1)

# Test 2: Load test data
test_file_path = os.path.join(project_root, "entity_based_chunking", "tests", "example_cti_report.txt")
print(f"Loading test file: {test_file_path}")

try:
    with open(test_file_path, 'r', encoding='utf-8') as f:
        test_text = f.read()
    print(f"✓ Successfully loaded test file ({len(test_text)} characters)")
except FileNotFoundError:
    print(f"✗ Test file not found: {test_file_path}")
    # Create a simple test text if file doesn't exist
    test_text = """
    THREAT INTELLIGENCE REPORT
    
    An advanced persistent threat (APT) group has been observed using the malicious IP address 192.168.1.100 
    to conduct reconnaissance activities. The threat actors have also been seen using the domain evil.com 
    for command and control communications.
    
    The malware sample with MD5 hash d41d8cd98f00b204e9800998ecf8427e was identified on multiple systems.
    Additionally, the file evil.exe with SHA256 hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 
    was discovered in the attack chain.
    
    The attackers have been using email addresses like attacker@evil.com and admin@malicious.org 
    for phishing campaigns. They have also been observed using the URL https://evil.com/payload.php 
    to deliver their payloads.
    
    Network indicators include connections to 10.0.0.1 and DNS queries to malicious.com.
    The registry key HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\Evil 
    was modified to ensure persistence.
    """
    print("✓ Using generated test text")
except Exception as e:
    print(f"✗ Error loading test file: {e}")
    sys.exit(1)

print()

# Test 3: Initialize chunker
try:
    chunker = CTIChunker()
    print("✓ Successfully initialized CTIChunker")
except Exception as e:
    print(f"✗ Failed to initialize CTIChunker: {e}")
    sys.exit(1)

print()

# Test 4: Test IOC extraction
print("--- Testing IOC Extraction ---")
try:
    iocs = chunker.extract_iocs_only(test_text)
    print(f"✓ IOC extraction completed")
    print(f"  Found {len(iocs)} IOCs")
    
    if iocs:
        print("  Sample IOCs:")
        for i, ioc in enumerate(iocs[:5]):  # Show first 5 IOCs
            print(f"    {i+1}. {ioc.get('ioc', 'N/A')} ({ioc.get('type', 'unknown')})")
    else:
        print("  No IOCs found")
        
except Exception as e:
    print(f"✗ IOC extraction failed: {e}")

print()

# Test 5: Test chunking
print("--- Testing IOC-Based Chunking ---")
try:
    chunks = chunker.chunk(test_text, window=2)
    print(f"✓ Chunking completed")
    print(f"  Generated {len(chunks)} chunks")
    
    if chunks:
        print("  Sample chunks:")
        for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
            chunk_text = chunk.get('chunk', '')
            ioc_info = chunk.get('ioc', 'N/A')
            ioc_type = chunk.get('type', 'unknown')
            print(f"    {i+1}. IOC: {ioc_info} ({ioc_type})")
            print(f"       Text: {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}")
            print()
    else:
        print("  No chunks generated")
        
except Exception as e:
    print(f"✗ Chunking failed: {e}")

print()

# Test 6: Test statistics
print("--- Testing Chunk Statistics ---")
try:
    chunks = chunker.chunk(test_text, window=2)
    stats = chunker.get_chunk_statistics(chunks)
    print("✓ Statistics calculated successfully")
    print("  Statistics:")
    print(f"    Total chunks: {stats['total_chunks']}")
    print(f"    Average length: {stats['average_length']:.2f}")
    print(f"    Total length: {stats['total_length']}")
    print(f"    IOC types: {stats['ioc_types']}")
    
except Exception as e:
    print(f"✗ Statistics calculation failed: {e}")

print()

# Test 7: Test error handling
print("--- Testing Error Handling ---")
try:
    # Test with empty text
    empty_chunks = chunker.chunk("")
    print(f"✓ Empty text handled correctly: {len(empty_chunks)} chunks")
    
    # Test with whitespace only
    whitespace_chunks = chunker.chunk("   \n\t   ")
    print(f"✓ Whitespace text handled correctly: {len(whitespace_chunks)} chunks")
    
    # Test with None (should handle gracefully)
    try:
        none_chunks = chunker.chunk(None)
        print(f"✓ None text handled correctly: {len(none_chunks)} chunks")
    except Exception as e:
        print(f"✓ None text properly rejected: {e}")
        
except Exception as e:
    print(f"✗ Error handling test failed: {e}")

print()

# Test 8: Test with different window sizes
print("--- Testing Different Window Sizes ---")
try:
    for window in [1, 2, 3, 5]:
        chunks = chunker.chunk(test_text, window=window)
        print(f"✓ Window size {window}: {len(chunks)} chunks")
        
except Exception as e:
    print(f"✗ Window size test failed: {e}")

print()
print("=== Test Complete ===")
