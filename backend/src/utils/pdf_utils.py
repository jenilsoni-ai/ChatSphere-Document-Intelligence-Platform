from typing import Optional
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.pdfparser import PDFSyntaxError
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from a PDF file using multiple methods
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text or None if extraction fails
    """
    try:
        # First try PyPDF2
        try:
            reader = PdfReader(file_path)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            
            if text.strip():
                return text
        except Exception as e:
            logger.warning(f"PyPDF2 extraction failed: {str(e)}")
        
        # If PyPDF2 fails or returns no text, try pdfminer
        try:
            text = pdfminer_extract_text(file_path)
            if text.strip():
                return text
        except PDFSyntaxError as e:
            logger.error(f"PDFMiner extraction failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during PDF extraction: {str(e)}")
            return None
            
        return None
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {str(e)}")
        return None