import requests
from typing import Dict, List, Optional, Set
from page.page import Page, PageElement
from page.html_parser import HTMLParser
from page.element_prioritizer import ElementPrioritizer
import time


class WebExplorer:
    """
    Main orchestrator class for web exploration and analysis.
    Manages page loading, parsing, and element prioritization.
    """
    
    def __init__(self, max_pages: int = 100, delay: float = 1.0):
        """
        Initialize the WebExplorer.
        Args:
            max_pages: Maximum number of pages to analyze
            delay: Delay between requests (in seconds)
        """
        self.max_pages = max_pages
        self.delay = delay
        
        # Components
        self.html_parser = HTMLParser()
        self.element_prioritizer = ElementPrioritizer()
        
        # State management
        self.visited_pages: Dict[str, Page] = {}
        self.failed_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        
        # Session for maintaining cookies/headers
        self.session = requests.Session()
    
    def analyze_url(self, url: str) -> Optional[Page]:
        """
        Analyze a single URL and return a Page object.
        Args:
            url: URL to analyze
        Returns:
            Page object if successful, None if failed
        """
        if url in self.visited_pages:
            return self.visited_pages[url]
        
        if url in self.failed_urls:
            return None
        
        try:
            # Fetch the page
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Create page object
            page = Page(url=url, raw_html=response.text)
            
            # Extract title
            title = response.text.split('<title>')[1].split('</title>')[0] if '<title>' in response.text else "No title"
            page.title = title
            
            # Process the page
            self._process_page(page)
            
            # Cache the page
            self.visited_pages[url] = page
            
            # Add delay
            time.sleep(self.delay)
            
            return page
            
        except Exception as e:
            print(f"Failed to analyze {url}: {e}")
            self.failed_urls.add(url)
            return None
    
    def get_prioritized_elements(self, url: str, element_type: str = None) -> List[PageElement]:
        """
        Get prioritized elements from a page.
        Args:
            url: URL of the page
            element_type: Optional filter by element type
        Returns:
            List of PageElement objects sorted by priority
        """
        if url not in self.visited_pages:
            return []
        
        page = self.visited_pages[url]
        elements = page.elements
        
        if element_type:
            elements = page.get_elements_by_type(element_type)
        
        # Sort by priority score (highest first)
        return sorted(elements, key=lambda x: x.priority_score, reverse=True)
