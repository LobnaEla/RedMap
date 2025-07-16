import json
import logging
import sys
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .chunking.processor import CTIProcessor
from .utils.config import load_config, validate_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cti_processing.log')
    ]
)
logger = logging.getLogger(__name__)


def process_cti_text(text: str, config: Optional[Dict] = None, window: int = 2) -> List[Dict[str, Any]]:
    """
    Process CTI text and return IOC-based chunks.
    
    This is the main API function for external pipeline integration.
    
    Args:
        text: CTI report text to process
        config: Configuration dictionary (will load from config.yaml if None)
        window: Context window size around each IOC
        
    Returns:
        List of chunks with IOC information
    """
    if not text or not text.strip():
        raise ValueError("Input text cannot be empty")
    
    try:
        # Load configuration if not provided
        if config is None:
            config = load_config()
            validate_config(config)
        
        # Initialize processor
        processor = CTIProcessor(config=config)
        
        # Process the report with IOC-based chunking
        results = processor.process_report(text, window=window)
        
        logger.info(f"Successfully processed text ({len(text)} chars) -> {len(results)} chunks")
        return results
        
    except Exception as e:
        logger.error(f"Error processing CTI text: {e}")
        raise


def process_cti_file(file_path: Union[str, Path], config: Optional[Dict] = None, window: int = 2) -> List[Dict[str, Any]]:
    """
    Process CTI file and return IOC-based chunks.
    
    Convenience function for processing files directly.
    
    Args:
        file_path: Path to CTI report file
        config: Configuration dictionary (will load from config.yaml if None)
        window: Context window size around each IOC
        
    Returns:
        List of chunks with IOC information
                
    """
    input_path = Path(file_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading CTI report from: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    if not text.strip():
        raise ValueError(f"Input file is empty: {input_path}")
    
    return process_cti_text(text, config, window)


def extract_iocs_only(text: str, config: Optional[Dict] = None) -> List[Dict[str, str]]:
    """
    Extract only IOCs from text without chunking.
    
    Args:
        text: CTI report text to process
        config: Configuration dictionary (will load from config.yaml if None)
        
    Returns:
        List of IOC dictionaries with 'ioc' and 'type' keys
    """
    if not text or not text.strip():
        return []
    
    try:
        # Load configuration if not provided
        if config is None:
            config = load_config()
            validate_config(config)
        
        # Initialize processor
        processor = CTIProcessor(config=config)
        
        # Extract IOCs only
        iocs = processor.get_iocs_only(text)
        
        logger.info(f"Extracted {len(iocs)} IOCs from text ({len(text)} chars)")
        return iocs
        
    except Exception as e:
        logger.error(f"Error extracting IOCs: {e}")
        return []


def create_processor(config_path: Optional[str] = None, api_key: Optional[str] = None) -> CTIProcessor:
    """
    Create a reusable CTI processor instance.
    
    For pipelines that need to process multiple reports efficiently.
    
    Args:
        config_path: Path to configuration file
        api_key: Optional API key override
        
    Returns:
        CTIProcessor instance ready for use
        
    """
    config = load_config(config_path or "config.yaml")
    validate_config(config)
    
    processor = CTIProcessor(api_key=api_key, config=config)
    logger.info("CTI processor created successfully")
    return processor


def main(config_path: Optional[str] = None, input_file: Optional[str] = None, window: int = 2, output_file: Optional[str] = None):
    """
    Main function to process CTI reports with enhanced error handling and logging.
    
    Args:
        input_file: Path to input CTI report file (default: tests/example_cti_report.txt)
        window: Context window size around each IOC
        output_file: Optional custom output file path
    """
    try:
        # Use the API function for processing
        input_path = Path(input_file or "tests/example_cti_report.txt")
        
        logger.info(f"Processing CTI report: {input_path}")
        
        # Process the file using the API function
        results = process_cti_file(input_path, window=window)
        
        # Output results with metadata
        logger.info(f"Processing completed. Generated {len(results)} chunks")
        
        # Add timestamp import
        from datetime import datetime
        
        output = {
            "metadata": {
                "input_file": str(input_path),
                "total_chunks": len(results),
                "processing_timestamp": datetime.now().isoformat(),
                "strategy": "ioc_based",
                "window_size": window
            },
            "chunks": results
        }
        
        # Print to console
        print(json.dumps(output, indent=2))
        
        # Save results to file
        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path("output") / f"processed_{input_path.stem}.json"
        
        output_path.parent.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
        logger.info(f"Results saved to: {output_path}")
        
        return output  # Return for programmatic use
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process CTI reports for IOC extraction and chunking")
    parser.add_argument("--config", "-c", help="Path to configuration file")
    parser.add_argument("--input", "-i", help="Path to input CTI report file")
    parser.add_argument("--output", "-o", help="Path to output JSON file")
    parser.add_argument("--window", "-w", type=int, default=2, 
                       help="Context window size around each IOC")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        main(args.config, args.input, args.window, args.output)
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)