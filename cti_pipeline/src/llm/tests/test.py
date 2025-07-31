import glob
import json
import os
import logging
from pathlib import Path
import time
from dotenv import load_dotenv
from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor
from cti_pipeline.src.llm.core.gemini_client import AnthropicClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("llm_test.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
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


def test_chunk_processor(sample_chunk, filename):
    """Test the complete chunk processing workflow"""
    logger.info("\n=== Testing ChunkProcessor ===")
    logger.debug(f"Processing chunk with ID: {sample_chunk.get('chunk_id')}")
    logger.debug(f"Text length: {len(sample_chunk.get('text', ''))}")
    # Updated to handle IOCs as string
    logger.debug(f"IOCs content: {sample_chunk.get('iocs', '')}")

    # Initialize processor
    processor = ChunkProcessor(api_key=API_KEY)
    logger.debug("ChunkProcessor initialized successfully")

    # Process the chunk
    result = processor.process_chunk(sample_chunk, filename)
    logger.debug("Chunk processing completed")

    logger.info("Processing Result:")
    logger.info(f"Success: {result['success']}")
    if result["success"]:
        techniques = result.get("mitre_techniques", [])
        logger.info(f"MITRE Techniques found: {len(techniques)}")
        logger.debug(f"Techniques: {techniques}")
        logger.debug("✅ Chunk processed successfully")
    else:
        logger.error(f"❌ Error: {result.get('error', 'Unknown error')}")

    return result


def main():
    start_time = time.time()
    try:
        logger.info("🚀 Starting test execution...")
        # Sample chunk data - Updated IOCs to string
        sample_chunk = {
            "chunk_id": "test_123",
            "text": "Attackers used PowerShell to download and execute malware",
            "iocs": "192.168.1.100, malware.ps1",
        }

        # Load chunk files
        chunk_files = load_chunk_files(CHUNKS_DIR)
        logger.debug(f"✅ Successfully loaded {len(chunk_files)} chunk files")
        chunk_file = chunk_files[0]

        logger.debug(f"Selected chunk file: {chunk_file}")

        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
                logger.debug("✅ Successfully loaded chunk data")

            filename = os.path.basename(chunk_file)
            # Get only the first chunk
            chunk = chunk_data.get("chunks", [])[0]
            chunk_id = chunk.get("chunk_id", "unknown")

            # Detailed chunk logging
            logger.debug("\n" + "=" * 50)
            logger.debug("Processing single chunk:")
            logger.debug(f"  ID: {chunk_id}")
            logger.debug(f"  Text: {chunk.get('text', '')[:500]}...")
            logger.debug(f"  IOCs: {chunk.get('iocs', '')}")
            logger.debug(f"  Length: {len(chunk.get('text', ''))} characters")
            logger.debug("=" * 50 + "\n")

            # Process the chunk
            logger.debug(f"🔄 Sending chunk to LLM processor")
            mapping = test_chunk_processor(chunk, filename)

            if mapping["success"]:
                techniques = mapping.get("mitre_techniques", [])
                processing_time = time.time() - start_time
                logger.info(
                    f"✅ Found {len(techniques)} MITRE techniques in {processing_time:.2f}s"
                )
                logger.info(f"🎯 Techniques: {techniques}")
            else:
                logger.error(
                    f"❌ Processing failed: {mapping.get('error', 'Unknown error')}"
                )

        except Exception as e:
            logger.error(f"❌ Error processing chunk: {str(e)}")
            return

    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()
