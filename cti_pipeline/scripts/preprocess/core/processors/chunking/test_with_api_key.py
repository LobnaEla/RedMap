import sys
import os

# Add the project root to sys.path to allow for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set a test API key
os.environ['GROQ_API_KEY'] = 'test_api_key_for_testing'

print("=== CTI Chunker Test with Mock API Key ===")
print(f"Project Root: {project_root}")
print(f"GROQ_API_KEY set: {'GROQ_API_KEY' in os.environ}")

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

# Test with simple text
test_text = """
THREAT INTELLIGENCE REPORT

A sophisticated APT group has been using IP address 192.168.1.100 for C2 communications.
The malicious domain malware.example.com was registered recently.
File hash: d41d8cd98f00b204e9800998ecf8427e (MD5)
SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Email: attacker@evil.com
URL: https://malicious.example.com/payload.php
"""

print(f"Testing with CTI text ({len(test_text)} characters)")

try:
    iocs = chunker.extract_iocs_only(test_text)
    print(f"✓ IOC extraction: {len(iocs)} IOCs found")
    for i, ioc in enumerate(iocs):
        print(f"  {i+1}. {ioc.get('ioc', 'N/A')} ({ioc.get('type', 'unknown')})")
except Exception as e:
    print(f"✗ IOC extraction failed: {e}")

print()

try:
    chunks = chunker.chunk(test_text, window=2)
    print(f"✓ Chunking: {len(chunks)} chunks generated")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}:")
        print(f"    IOC: {chunk.get('ioc', 'N/A')} ({chunk.get('type', 'unknown')})")
        print(f"    Text: {chunk.get('chunk', '')[:100]}...")
        print()
except Exception as e:
    print(f"✗ Chunking failed: {e}")

print("=== Test Complete ===")
