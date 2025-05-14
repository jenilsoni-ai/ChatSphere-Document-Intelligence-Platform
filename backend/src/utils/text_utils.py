import re
from typing import List, Dict, Any, Optional
from html import unescape
from bs4 import BeautifulSoup

# Regular expressions for text cleaning
HTML_TAG_PATTERN = re.compile(r'<.*?>')
MULTIPLE_SPACES_PATTERN = re.compile(r'\s+')
SPECIAL_CHARS_PATTERN = re.compile(r'[^\w\s]')

async def clean_text(text: str, remove_html: bool = True, remove_special_chars: bool = False) -> str:
    """Clean text by removing HTML tags, extra spaces, and optionally special characters
    
    Args:
        text: Text to clean
        remove_html: Whether to remove HTML tags
        remove_special_chars: Whether to remove special characters
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Unescape HTML entities
    text = unescape(text)
    
    # Remove HTML tags if requested
    if remove_html:
        text = HTML_TAG_PATTERN.sub(' ', text)
    
    # Remove special characters if requested
    if remove_special_chars:
        text = SPECIAL_CHARS_PATTERN.sub(' ', text)
    
    # Replace multiple spaces with a single space
    text = MULTIPLE_SPACES_PATTERN.sub(' ', text)
    
    # Strip leading and trailing whitespace
    return text.strip()

async def extract_text_from_html(html_content: str) -> str:
    """Extract text from HTML content
    
    Args:
        html_content: HTML content
        
    Returns:
        Extracted text
    """
    if not html_content:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract text
    text = soup.get_text(separator=' ', strip=True)
    
    # Clean text
    return await clean_text(text)

async def split_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into chunks with overlap
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # If text is shorter than chunk size, return as is
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Get chunk of text
        end = start + chunk_size
        
        # If this is not the last chunk, try to find a good break point
        if end < len(text):
            # Try to find the last period, question mark, or exclamation point
            last_period = max(text.rfind('.', start, end), 
                             text.rfind('?', start, end),
                             text.rfind('!', start, end))
            
            # If found, use it as the end point
            if last_period != -1 and last_period > start + chunk_size // 2:
                end = last_period + 1
        
        # Add chunk to list
        chunks.append(text[start:end])
        
        # Move start position for next chunk, accounting for overlap
        start = end - overlap
    
    return chunks

async def normalize_text(text: str) -> str:
    """Normalize text by converting to lowercase and removing extra whitespace
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple spaces with a single space
    text = MULTIPLE_SPACES_PATTERN.sub(' ', text)
    
    # Strip leading and trailing whitespace
    return text.strip()

async def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text using a simple frequency-based approach
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Normalize text
    text = await normalize_text(text)
    
    # Remove special characters
    text = SPECIAL_CHARS_PATTERN.sub(' ', text)
    
    # Split into words
    words = text.split()
    
    # Count word frequency
    word_counts = {}
    for word in words:
        if len(word) > 2:  # Ignore very short words
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Return top keywords
    return [word for word, count in sorted_words[:max_keywords]]