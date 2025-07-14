import requests
import logging
from typing import Optional, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class OCRClient:
    """Client for communicating with the OCR service API"""
    
    def __init__(self, ocr_service_url: str = "http://ocr-service:8000"):
        """
        Initialize OCR client
        
        Args:
            ocr_service_url: URL of the OCR service
        """
        self.base_url = ocr_service_url.rstrip('/')
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """
        Check if OCR service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ OCR service health check failed: {e}")
            return False
    
    def extract_text_from_file(self, file_path: str, polish: bool = True) -> Optional[str]:
        """
        Extract text from image file using OCR service
        
        Args:
            file_path: Path to the image file
            polish: Whether to apply text polishing
            
        Returns:
            Extracted text or None if failed
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return None
            
            # Prepare file for upload
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f, 'image/*')}
                data = {'polish': polish}
                
                logger.info(f"🔄 Sending {file_path} to OCR service...")
                
                response = self.session.post(
                    f"{self.base_url}/ocr/extract-text",
                    files=files,
                    data=data,
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        extracted_text = result.get('text', '')
                        logger.info(f"✅ OCR completed: {len(extracted_text)} characters extracted")
                        return extracted_text
                    else:
                        logger.error(f"❌ OCR service returned error: {result}")
                        return None
                else:
                    logger.error(f"❌ OCR service request failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Failed to extract text from {file_path}: {e}")
            return None
    
    def extract_text_from_files(self, file_paths: List[str], polish: bool = True) -> dict:
        """
        Extract text from multiple image files using batch endpoint
        
        Args:
            file_paths: List of paths to image files
            polish: Whether to apply text polishing
            
        Returns:
            Dictionary with results for each file
        """
        try:
            # Prepare files for upload
            files = []
            valid_paths = []
            
            for file_path in file_paths:
                if os.path.exists(file_path):
                    files.append(('files', (os.path.basename(file_path), open(file_path, 'rb'), 'image/*')))
                    valid_paths.append(file_path)
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
            
            if not files:
                logger.error("❌ No valid files to process")
                return {}
            
            try:
                data = {'polish': polish}
                
                logger.info(f"🔄 Sending {len(files)} files to OCR service...")
                
                response = self.session.post(
                    f"{self.base_url}/ocr/extract-text-batch",
                    files=files,
                    data=data,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        logger.info(f"✅ Batch OCR completed: {result.get('successful_extractions', 0)}/{len(files)} successful")
                        
                        # Create mapping from file path to result
                        results = {}
                        for i, file_result in enumerate(result.get('results', [])):
                            if i < len(valid_paths):
                                results[valid_paths[i]] = file_result
                        
                        return results
                    else:
                        logger.error(f"❌ OCR batch service returned error: {result}")
                        return {}
                else:
                    logger.error(f"❌ OCR batch service request failed: {response.status_code} - {response.text}")
                    return {}
                    
            finally:
                # Close all file handles
                for _, (_, file_handle, _) in files:
                    file_handle.close()
                    
        except Exception as e:
            logger.error(f"❌ Failed to extract text from batch: {e}")
            return {}

# Fallback function for backward compatibility
def extract_text(image_path: str, polish: bool = True) -> str:
    """
    Fallback function that tries OCR service first, then local processing
    
    Args:
        image_path: Path to the image file
        polish: Whether to apply text polishing
        
    Returns:
        Extracted text
    """
    # Try OCR service first
    ocr_client = OCRClient()
    
    if ocr_client.health_check():
        result = ocr_client.extract_text_from_file(image_path, polish)
        if result is not None:
            return result
        logger.warning("⚠️ OCR service failed, attempting fallback...")
    else:
        logger.warning("⚠️ OCR service unavailable, attempting fallback...")
    
    # Fallback to local processing (if available)
    try:
        from .ocr_library_local import extract_text as extract_text_local
        logger.info("🔄 Using local OCR fallback...")
        return extract_text_local(image_path)
    except ImportError:
        logger.error("❌ No local OCR fallback available")
        return ""
