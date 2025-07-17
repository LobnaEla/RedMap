"""
Test script to verify API key loading and test the CTIChunker with a real API key.
"""
import os
import sys
from pathlib import Path

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    
    # Try to load from entity_based_chunking/.env
    env_path = os.path.join(project_root, "entity_based_chunking", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded .env from: {env_path}")
    else:
        print(f"✗ .env file not found at: {env_path}")
        
except ImportError:
    print("✗ python-dotenv not installed. Install with: pip install python-dotenv")
    print("Alternatively, set GROQ_API_KEY environment variable manually")

print("=" * 60)
print("       CTI CHUNKER TEST WITH REAL API KEY")
print("=" * 60)

# Check if API key is available
api_key = os.getenv('GROQ_API_KEY')
if api_key:
    print(f"✓ GROQ_API_KEY found: {api_key[:20]}...{api_key[-5:]}")
else:
    print("✗ GROQ_API_KEY not found in environment variables")
    print("Available environment variables:")
    for key in os.environ:
        if 'GROQ' in key.upper():
            print(f"  {key}: {os.environ[key][:20]}...")
    sys.exit(1)

print()

# Test importing the chunker
try:
    from cti_pipeline.scripts.preprocess.core.processors.chunking.chunker import CTIChunker
    print("✓ Successfully imported CTIChunker")
except Exception as e:
    print(f"✗ Failed to import CTIChunker: {e}")
    sys.exit(1)

# Test initializing the chunker
try:
    chunker = CTIChunker()
    print("✓ Successfully initialized CTIChunker")
except Exception as e:
    print(f"✗ Failed to initialize CTIChunker: {e}")
    sys.exit(1)

# Test with a simple text containing clear IOCs
test_text = """
THREAT INTELLIGENCE REPORT

Network Indicators:
- Malicious IP: 192.168.1.100
- C2 domain: malware.example.com
- Backup server: 10.0.0.1

File Indicators:
- Malware hash: d41d8cd98f00b204e9800998ecf8427e
- Trojan SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

Communication:
- Email: attacker@evil.com
- Phishing URL: https://phishing.badsite.com/login
"""

print(f"Testing with sample text ({len(test_text)} characters)")
print()

# Test IOC extraction
print("Testing IOC Extraction:")
try:
    iocs = chunker.extract_iocs_only(test_text)
    print(f"✓ IOC extraction completed: {len(iocs)} IOCs found")
    
    if iocs:
        print("Extracted IOCs:")
        for i, ioc in enumerate(iocs, 1):
            print(f"  {i}. {ioc.get('ioc', 'N/A')} ({ioc.get('type', 'unknown')})")
    else:
        print("No IOCs found (this might indicate an API issue)")
        
except Exception as e:
    print(f"✗ IOC extraction failed: {e}")

print()

# Test chunking
print("Testing Chunking:")
try:
    chunks = chunker.chunk(test_text, window=2)
    print(f"✓ Chunking completed: {len(chunks)} chunks generated")
    
    if chunks:
        print("Generated chunks:")
        for i, chunk in enumerate(chunks, 1):
            print(f"  Chunk {i}:")
            print(f"    IOC: {chunk.get('ioc', 'N/A')} ({chunk.get('type', 'unknown')})")
            chunk_text = chunk.get('chunk', '')
            print(f"    Text: {chunk_text[:100]}{'...' if len(chunk_text) > 100 else ''}")
            print()
    else:
        print("No chunks generated")
        
except Exception as e:
    print(f"✗ Chunking failed: {e}")

print("=" * 60)
print("                    TEST COMPLETE")
print("=" * 60)
