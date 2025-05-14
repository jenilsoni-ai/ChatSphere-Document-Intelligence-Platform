import aiohttp
import logging
from typing import Dict, Any, Optional
from ..utils.text_utils import clean_text, extract_text_from_html
from ..core.config import settings

logger = logging.getLogger(__name__)

class WebsiteScraper:
    def __init__(self):
        self.api_key = settings.FIRECRAWL_API_KEY
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY is not set in environment variables")
        self.base_url = "https://api.firecrawl.com/extract"
        
    async def scrape_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Scrape content from a URL using Firecrawl's extract API with fallback to direct scraping
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dictionary containing the scraped content and metadata
        """
        try:
            # First try using Firecrawl API
            result = await self._scrape_with_firecrawl(url)
            if result:
                return result
                
            # If Firecrawl fails, fallback to direct scraping
            logger.info("Falling back to direct website scraping")
            return await self._scrape_directly(url)
                    
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return None
            
    async def _scrape_with_firecrawl(self, url: str) -> Optional[Dict[str, Any]]:
        """Try scraping with Firecrawl API"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {
                    "url": url,
                    "extract_text": True,
                    "extract_metadata": True,
                    "extract_links": False,
                    "clean_text": True
                }
                
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=params,
                    timeout=30  # Add timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Firecrawl API error: {error_text}")
                        return None
                        
                    data = await response.json()
                    
                    # Clean and process the extracted content
                    cleaned_content = await clean_text(data.get('text', ''))
                    
                    return {
                        'content': cleaned_content,
                        'title': data.get('metadata', {}).get('title', ''),
                        'description': data.get('metadata', {}).get('description', ''),
                        'url': url,
                        'word_count': len(cleaned_content.split()),
                        'source_type': 'website'
                    }
                    
        except aiohttp.ClientError as e:
            logger.error(f"Firecrawl API connection error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Firecrawl API error: {str(e)}")
            return None
            
    async def _scrape_directly(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback method to scrape website directly"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch URL directly: {response.status}")
                        return None
                        
                    html_content = await response.text()
                    
                    # Extract text from HTML
                    text_content = await extract_text_from_html(html_content)
                    cleaned_content = await clean_text(text_content)
                    
                    # Try to extract title from HTML
                    title = ''
                    description = ''
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title = soup.title.string if soup.title else ''
                        meta_desc = soup.find('meta', attrs={'name': 'description'})
                        description = meta_desc.get('content', '') if meta_desc else ''
                    except Exception as e:
                        logger.warning(f"Error extracting metadata: {str(e)}")
                    
                    return {
                        'content': cleaned_content,
                        'title': title or url,
                        'description': description,
                        'url': url,
                        'word_count': len(cleaned_content.split()),
                        'source_type': 'website'
                    }
                    
        except Exception as e:
            logger.error(f"Direct scraping error: {str(e)}")
            return None

# Create a global instance
website_scraper = WebsiteScraper() 