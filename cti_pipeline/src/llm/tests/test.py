import glob
import json
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
API_KEY = os.getenv("ANTHROPIC_API_KEY")

CHUNKS_DIR = "cti_pipeline/data/chunks"

if not API_KEY:
    logger.error("ANTHROPIC_API_KEY not found in .env file")
    exit(1)


def load_chunk_files(chunks_dir: str) -> list[str]:
    """Charge les fichiers de chunks depuis le répertoire"""
    try:
        chunk_files = glob.glob(os.path.join(chunks_dir, "chunks_*.json"))
        if not chunk_files:
            raise FileNotFoundError(f"No chunk files found in {chunks_dir}")
        return chunk_files

    except Exception as e:
        raise RuntimeError(f"Error loading chunk files: {str(e)}")


def test_chunk_processor(sample_chunk):
    """Test the complete chunk processing workflow"""
    logger.info("\n=== Testing ChunkProcessor ===")

    # Initialize processor
    processor = ChunkProcessor(api_key=API_KEY)

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
        # Sample chunk data
        sample_chunk = {
            "chunk_id": "test_123",
            "text": "Attackers used PowerShell to download and execute malware",
            "iocs": ["192.168.1.100", "malware.ps1"],
        }

        # Load chunk files
        chunk_files = load_chunk_files(CHUNKS_DIR)

        # Run tests

    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
    finally:
        logger.info("Test run completed")


if __name__ == "__main__":
    main()
