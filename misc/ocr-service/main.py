from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import io
import os
import tempfile
import logging
from typing import Optional
from contextlib import asynccontextmanager

# Import OCR functions
from ocr_processor import OCRProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global OCR processor instance
ocr_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global ocr_processor
    logger.info("🚀 Starting OCR Service...")
    
    # Initialize OCR processor
    ocr_processor = OCRProcessor()
    logger.info("✅ OCR models loaded successfully")
    
    yield
    
    logger.info("🛑 Shutting down OCR Service...")

# Create FastAPI app
app = FastAPI(
    title="CTI OCR Service",
    description="Optical Character Recognition service for CTI pipeline",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ocr-service"}

@app.post("/ocr/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
    polish: bool = True
):
    """
    Extract text from uploaded image file
    
    Args:
        file: Image file (PNG, JPG, JPEG, BMP, TIFF)
        polish: Whether to apply text polishing/cleaning
    
    Returns:
        JSON response with extracted text
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only image files are supported."
            )
        
        logger.info(f"📄 Processing image: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text using OCR processor
            extracted_text = ocr_processor.extract_text(tmp_file_path, polish=polish)
            
            logger.info(f"✅ Text extracted successfully from {file.filename}")
            
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "text": extracted_text,
                "text_length": len(extracted_text),
                "polished": polish
            })
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error(f"❌ OCR extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.post("/ocr/extract-text-batch")
async def extract_text_batch(
    files: list[UploadFile] = File(...),
    polish: bool = True
):
    """
    Extract text from multiple image files
    
    Args:
        files: List of image files
        polish: Whether to apply text polishing/cleaning
    
    Returns:
        JSON response with extracted text for each file
    """
    try:
        results = []
        
        for file in files:
            if not file.content_type.startswith('image/'):
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Invalid file type: {file.content_type}"
                })
                continue
            
            try:
                # Read file content
                file_content = await file.read()
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                    tmp_file.write(file_content)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Extract text
                    extracted_text = ocr_processor.extract_text(tmp_file_path, polish=polish)
                    
                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "text": extracted_text,
                        "text_length": len(extracted_text)
                    })
                    
                finally:
                    os.unlink(tmp_file_path)
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        successful_extractions = sum(1 for r in results if r["success"])
        logger.info(f"✅ Batch processing completed: {successful_extractions}/{len(files)} successful")
        
        return JSONResponse(content={
            "success": True,
            "total_files": len(files),
            "successful_extractions": successful_extractions,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"❌ Batch OCR processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch OCR processing failed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "CTI OCR Service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "single_ocr": "/ocr/extract-text",
            "batch_ocr": "/ocr/extract-text-batch"
        }
    }
