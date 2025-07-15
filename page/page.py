from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import hashlib


@dataclass
class PageElement:
    """Represents a single element on a page with its properties"""
    tag: str
    text: str
    attributes: Dict[str, str]
    xpath: Optional[str] = None
    priority_score: float = 0.0
    element_type: str = "unknown"  # nav, button, link, content, etc.


class Page:
    """
    Represents a web page with its content and extracted elements.
    Serves as a cache and storage mechanism for page analysis.
    """
    
    def __init__(self, url: str, raw_html: str = "", title: str = ""):
        self.url = url
        self.raw_html = raw_html
        self.title = title
        self.domain = urlparse(url).netloc
        self.path = urlparse(url).path
        
        # Page content analysis
        self.cleaned_html: Optional[str] = None
        self.soup: Optional[BeautifulSoup] = None
        self.elements: List[PageElement] = []
        self.links: Set[str] = set()
        
        # Page metadata
        self.page_hash = self._generate_hash()
        self.is_processed = False
        self.load_time: Optional[float] = None
        self.error_message: Optional[str] = None
        
    def _generate_hash(self) -> str:
        """Generate a unique hash for this page based on URL and content"""
        content = f"{self.url}_{self.raw_html[:1000] if self.raw_html else ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def set_content(self, raw_html: str, title: str = ""):
        """Set the page content and update hash"""
        self.raw_html = raw_html
        self.title = title
        self.page_hash = self._generate_hash()
        self.is_processed = False
        
    def add_element(self, element: PageElement):
        """Add an element to the page"""
        self.elements.append(element)
        
    def get_elements_by_type(self, element_type: str) -> List[PageElement]:
        """Get all elements of a specific type"""
        return [elem for elem in self.elements if elem.element_type == element_type]
    
    def get_high_priority_elements(self, min_score: float = 0.5) -> List[PageElement]:
        """Get elements with priority score above threshold"""
        return [elem for elem in self.elements if elem.priority_score >= min_score]
    
    def has_changed(self, new_html: str) -> bool:
        """Check if page content has changed"""
        new_hash = hashlib.md5(f"{self.url}_{new_html[:1000]}".encode()).hexdigest()
        return new_hash != self.page_hash
    
    def __str__(self):
        return f"Page(url='{self.url}', elements={len(self.elements)}, processed={self.is_processed})"
    
    def __repr__(self):
        return self.__str__() 