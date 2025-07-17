import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor
from cti_pipeline.src.llm.core.anthropic_client import AnthropicClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("llm_test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

if not API_KEY:
    logger.error("ANTHROPIC_API_KEY not found in .env file")
    exit(1)


def test_chunk_processor():
    """Test the complete chunk processing workflow"""
    logger.info("\n=== Testing ChunkProcessor ===")

    # Sample chunk data
    sample_chunk = {
        "chunk_id": "test_123",
        "text": "Attackers used PowerShell to download and execute malware",
        "iocs": ["192.168.1.100", "malware.ps1"],
    }

    # Initialize processor
    processor = ChunkProcessor()

    # Process the chunk
    result = processor.process_chunk(sample_chunk, "test_file.json")

    logger.info("Processing Result:")
    logger.info(f"Success: {result['success']}")
    if result["success"]:
        logger.info(f"MITRE Techniques: {result.get('mitre_techniques', [])}")
    else:
        logger.error(f"Error: {result.get('error', 'Unknown error')}")

    return result


def main():
    try:

        # Run tests
        test_chunk_processor()

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
    finally:
        logger.info("Test run completed")


if __name__ == "__main__":
    main()
