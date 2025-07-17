import sys
import os

# Add the project root to sys.path to allow for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=== Simple CTI Chunker Test ===")
print(f"Project Root: {project_root}")

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
test_text = "This is a test with IP address 192.168.1.1 and domain example.com"
print(f"Testing with text: {test_text}")

try:
    iocs = chunker.extract_iocs_only(test_text)
    print(f"✓ IOC extraction: {len(iocs)} IOCs found")
    for ioc in iocs:
        print(f"  - {ioc}")
except Exception as e:
    print(f"✗ IOC extraction failed: {e}")

try:
    chunks = chunker.chunk(test_text)
    print(f"✓ Chunking: {len(chunks)} chunks generated")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}: {chunk}")
except Exception as e:
    print(f"✗ Chunking failed: {e}")

print("=== Test Complete ===")
