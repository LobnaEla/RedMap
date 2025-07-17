import glob
import json
import os
import logging
from pathlib import Path
import time
from dotenv import load_dotenv
from cti_pipeline.src.llm.core.chunk_processor import ChunkProcessor
from cti_pipeline.src.llm.core.anthropic_client import AnthropicClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO to DEBUG
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
    try:
        logger.debug("Starting test execution...")
        # Sample chunk data - Updated IOCs to string
        sample_chunk = {
            "chunk_id": "test_123",
            "text": "Attackers used PowerShell to download and execute malware",
            "iocs": "192.168.1.100, malware.ps1",  # Changed from list to string
        }

        # Load chunk files
        chunk_files = load_chunk_files(CHUNKS_DIR)
        logger.debug(f"✅ Successfully loaded {len(chunk_files)} chunk files")
        chunk_file = chunk_files[10]
        logger.debug(f"Selected chunk file: {chunk_file}")

        try:
            with open(chunk_file, "r", encoding="utf-8") as f:
                chunk_data = json.load(f)
                logger.debug("✅ Successfully loaded chunk data")

            filename = os.path.basename(chunk_file)
            chunks = chunk_data.get("chunks", [])
            logger.debug(f"✅ Found {len(chunks)} chunks in {filename}")

            for chunk_idx, chunk in enumerate(chunks, 1):
                chunk_id = chunk.get("chunk_id", "unknown")

                # Add detailed chunk content logging
                logger.debug("\n" + "=" * 50)
                logger.debug(f"Processing chunk {chunk_idx}/{len(chunks)}")
                logger.debug("=" * 50)
                logger.debug("Chunk Details:")
                logger.debug(f"  ID: {chunk_id}")
                logger.debug(f"  Text: {chunk.get('text', '')[:500]}...")
                # Updated IOCs logging to handle string
                logger.debug(f"  IOCs: {chunk.get('iocs', '')}")
                logger.debug(f"  Length: {len(chunk.get('text', ''))} characters")
                logger.debug("=" * 50 + "\n")

                # Validation du chunk
                if not isinstance(chunk, dict):
                    error_msg = "Invalid chunk format: not a dictionary"
                    logger.warning(f"❌ Chunk {chunk_id}: {error_msg}")
                    continue

                if "text" not in chunk or not chunk["text"].strip():
                    error_msg = "Empty text content in chunk"
                    logger.warning(f"❌ Chunk {chunk_id}: {error_msg}")
                    continue

                logger.debug(f"✅ Chunk {chunk_id} validation successful")

                # Traitement du chunk
                logger.debug(f"🔄 Sending chunk {chunk_id} to LLM processor")
                mapping = test_chunk_processor(chunk, filename)

                if mapping["success"]:
                    logger.debug(f"✅ Successfully processed chunk {chunk_id}")
                    logger.debug(
                        f"🎯 MITRE techniques found: {mapping.get('mitre_techniques', [])}"
                    )
                else:
                    logger.warning(
                        f"❌ Failed to process chunk {chunk_id}: {mapping.get('error', 'Unknown error')}"
                    )

                logger.debug("⏳ Waiting 500ms before next chunk...")
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ Error processing chunks: {str(e)}")
            return

    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
    finally:
        logger.info("✅ Test run completed")


if __name__ == "__main__":
    main()
