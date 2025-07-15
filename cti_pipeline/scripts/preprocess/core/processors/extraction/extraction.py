"""
Text Extraction Module for CTI Preprocessing Pipeline

This module provides text extraction functionality from various file formats
as the first step in the preprocessing pipeline.

Supported formats:
- PDF files (with pypdf)
- HTML files (with BeautifulSoup)
- JSON files 
- CSV files
- Plain text files
"""

import os
import re
import json
import csv
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pypdf import PdfReader
from bs4 import BeautifulSoup


@dataclass
class ExtractionResult:
    """Result of text extraction operation"""
    success: bool
    text: str
    file_path: str
    file_format: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TextExtractor:
    """
    Text extraction from various file formats for CTI preprocessing.
    
    This class handles the extraction of text content from different file formats
    as the first step in the CTI preprocessing pipeline.
    """
    
    def __init__(self):
        """Initialize the text extractor"""
        self.supported_formats = {'.pdf', '.txt', '.json', '.html', '.htm', '.csv'}
    
    def extract_from_file(self, file_path: str) -> ExtractionResult:
        """
        Extract text from a file based on its format.
        """
        if not os.path.exists(file_path):
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format="unknown",
                error_message=f"[Extract] File not found: {file_path}"
            )
        
        _, extension = os.path.splitext(file_path.lower())
        
        if extension not in self.supported_formats:
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format=extension,
                error_message=f"[Extract] Unsupported file format: {extension}"
            )
        
        try:
            if extension == '.pdf':
                text = self._extract_pdf(file_path)
            elif extension == '.txt':
                text = self._extract_txt(file_path)
            elif extension == '.json':
                text = self._extract_json(file_path)
            elif extension in ['.html', '.htm']:
                text = self._extract_html(file_path)
            elif extension == '.csv':
                text = self._extract_csv(file_path)
            else:
                raise ValueError(f"Unsupported format: {extension}")
            
            return ExtractionResult(
                success=True,
                text=text,
                file_path=file_path,
                file_format=extension,
                metadata={
                    'original_length': len(text),
                    'file_size': os.path.getsize(file_path)
                }
            )
            
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return ExtractionResult(
                success=False,
                text="",
                file_path=file_path,
                file_format=extension,
                error_message=f"[Extract] Extraction failed: {str(e)}"
            )
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file using pypdf"""
        try:
            with open(file_path, "rb") as f:
                reader = PdfReader(f)
                text_content = ""
                
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    text_content += page_text + "\n"
                
                print("[Extract] Extracted text from PDF with {} pages".format(len(reader.pages)))

                return text_content
                
        except Exception as e:
            raise Exception(f"[Extract] PDF extraction error: {str(e)}")
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from plain text file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin1") as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"[Extract] Text file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] Text file extraction error: {str(e)}")
    
    def _extract_json(self, file_path: str) -> str:
        """Extract text from JSON file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                return json.dumps(content, ensure_ascii=False, indent=2)
        except Exception as e:
            raise Exception(f"[Extract] JSON extraction error: {str(e)}")
    
    def _extract_html(self, file_path: str) -> str:
        """Extract text from HTML file using BeautifulSoup"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
                return soup.get_text(separator="\n")
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin1") as f:
                    soup = BeautifulSoup(f, "html.parser")
                    return soup.get_text(separator="\n")
            except Exception as e:
                raise Exception(f"[Extract] HTML file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] HTML extraction error: {str(e)}")
    
    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                return "\n".join("; ".join(row) for row in reader)
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, newline="", encoding="latin1") as f:
                    reader = csv.reader(f)
                    return "\n".join("; ".join(row) for row in reader)
            except Exception as e:
                raise Exception(f"[Extract] CSV file encoding error: {str(e)}")
        except Exception as e:
            raise Exception(f"[Extract] CSV extraction error: {str(e)}")


# Convenience function for quick usage
def extract_text_from_file(file_path: str) -> str:
    """
    Quick function to extract text from a file.
    """
    extractor = TextExtractor()
    result = extractor.extract_from_file(file_path)
    return result.text if result.success else ""


def extract_with_result(file_path: str) -> ExtractionResult:
    """
    Extract text from a file with detailed result information.
    """
    extractor = TextExtractor()
    return extractor.extract_from_file(file_path)