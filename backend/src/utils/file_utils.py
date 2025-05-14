import os
import tempfile
from typing import List, Dict, Any, Optional, BinaryIO
from pathlib import Path
import mimetypes

from fastapi import UploadFile

# Supported file types and their MIME types
SUPPORTED_FILE_TYPES = {
    # Text files
    'txt': 'text/plain',
    'md': 'text/markdown',
    
    # Document files
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    
    # Spreadsheet files
    'csv': 'text/csv',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    
    # Presentation files
    'ppt': 'application/vnd.ms-powerpoint',
    'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    
    # Web files
    'html': 'text/html',
    'htm': 'text/html',
    'xml': 'application/xml',
    'json': 'application/json',
}

async def validate_file_type(file: UploadFile) -> bool:
    """Validate if the file type is supported
    
    Args:
        file: The uploaded file
        
    Returns:
        True if file type is supported, False otherwise
    """
    if not file.filename:
        return False
    
    # Get file extension
    file_ext = file.filename.split('.')[-1].lower()
    
    # Check if extension is supported
    return file_ext in SUPPORTED_FILE_TYPES

async def get_file_size(file: UploadFile) -> int:
    """Get the size of an uploaded file
    
    Args:
        file: The uploaded file
        
    Returns:
        File size in bytes
    """
    # Save file to temporary location to get size
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        # Read file in chunks to avoid memory issues with large files
        chunk_size = 1024 * 1024  # 1MB chunks
        file_size = 0
        
        # Reset file position
        await file.seek(0)
        
        # Read file in chunks
        while chunk := await file.read(chunk_size):
            temp_file.write(chunk)
            file_size += len(chunk)
        
        # Reset file position for future operations
        await file.seek(0)
    
    # Clean up temporary file
    os.unlink(temp_file.name)
    
    return file_size

async def save_file_locally(file: UploadFile, directory: str = None) -> str:
    """Save an uploaded file to a local temporary directory
    
    Args:
        file: The uploaded file
        directory: Optional directory to save the file in
        
    Returns:
        Path to the saved file
    """
    # Create temporary directory if not provided
    if not directory:
        directory = tempfile.mkdtemp()
    else:
        os.makedirs(directory, exist_ok=True)
    
    # Generate file path
    file_path = os.path.join(directory, file.filename)
    
    # Save file
    with open(file_path, "wb") as f:
        # Reset file position
        await file.seek(0)
        
        # Read file in chunks to avoid memory issues with large files
        chunk_size = 1024 * 1024  # 1MB chunks
        while chunk := await file.read(chunk_size):
            f.write(chunk)
        
        # Reset file position for future operations
        await file.seek(0)
    
    return file_path

async def get_mime_type(file_path: str) -> str:
    """Get the MIME type of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    # Get file extension
    file_ext = os.path.splitext(file_path)[1][1:].lower()
    
    # Check if extension is in our supported types
    if file_ext in SUPPORTED_FILE_TYPES:
        return SUPPORTED_FILE_TYPES[file_ext]
    
    # Use mimetypes library as fallback
    mime_type, _ = mimetypes.guess_type(file_path)
    
    return mime_type or 'application/octet-stream'

async def cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files
    
    Args:
        file_paths: List of file paths to clean up
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            # Log error but continue
            print(f"Error cleaning up file {file_path}: {str(e)}")

async def cleanup_temp_dir(directory: str) -> None:
    """Clean up temporary directory and all files in it
    
    Args:
        directory: Directory path to clean up
    """
    try:
        if os.path.exists(directory) and os.path.isdir(directory):
            # Remove all files in directory
            for file_name in os.listdir(directory):
                file_path = os.path.join(directory, file_name)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            
            # Remove directory
            os.rmdir(directory)
    except Exception as e:
        # Log error but continue
        print(f"Error cleaning up directory {directory}: {str(e)}")