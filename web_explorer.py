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
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
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
    
    def get_page_summary(self, url: str) -> Optional[Dict]:
        """
        Get a summary of a page's analysis.
        
        Args:
            url: URL of the page
            
        Returns:
            Dictionary with page summary or None if page not found
        """
        if url not in self.visited_pages:
            return None
        
        page = self.visited_pages[url]
        
        # Group elements by type
        elements_by_type = {}
        for element in page.elements:
            if element.element_type not in elements_by_type:
                elements_by_type[element.element_type] = []
            elements_by_type[element.element_type].append(element)
        
        # Get high priority elements
        high_priority = page.get_high_priority_elements()
        
        return {
            'url': url,
            'title': page.title,
            'total_elements': len(page.elements),
            'elements_by_type': {k: len(v) for k, v in elements_by_type.items()},
            'high_priority_elements': len(high_priority),
            'links_found': len(page.links),
            'is_processed': page.is_processed,
            'load_time': page.load_time
        }
    
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
    
    def _process_page(self, page: Page):
        """
        Process a page: clean HTML, extract elements, and prioritize them.
        
        Args:
            page: Page object to process
        """
        start_time = time.time()
        
        try:
            # Clean HTML
            cleaned_soup = self.html_parser.clean_html(page.raw_html, page.url)
            page.soup = cleaned_soup
            page.cleaned_html = str(cleaned_soup)
            
            # Extract elements
            elements = self.html_parser.extract_elements(cleaned_soup)
            
            # Prioritize elements
            for element in elements:
                element.priority_score = self.element_prioritizer.calculate_priority(element)
            
            page.elements = elements
            
            # Extract links
            page.links = self.html_parser.extract_links(cleaned_soup, page.url)
            self.discovered_urls.update(page.links)
            
            # Mark as processed
            page.is_processed = True
            page.load_time = time.time() - start_time
            
        except Exception as e:
            page.error_message = str(e)
            page.load_time = time.time() - start_time
    
    def get_stats(self) -> Dict:
        """
        Get exploration statistics.
        
        Returns:
            Dictionary with exploration stats
        """
        return {
            'pages_analyzed': len(self.visited_pages),
            'failed_urls': len(self.failed_urls),
            'discovered_urls': len(self.discovered_urls),
            'total_elements': sum(len(page.elements) for page in self.visited_pages.values()),
            'processed_pages': sum(1 for page in self.visited_pages.values() if page.is_processed)
        } 