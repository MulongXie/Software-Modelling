from bs4 import BeautifulSoup, Comment
import re
from typing import List, Set, Optional
from .page import PageElement


class HTMLParser:
    """
    HTML parser for cleaning and extracting elements from web pages.
    Adapted from reference implementation for static page analysis.
    """
    
    def __init__(self):
        # Tags that should be kept even when empty
        self.preserve_tags = {'hr', 'br', 'img', 'video', 'input', 'meta', 'link', 'textarea'}
        # Attributes to preserve during cleaning
        self.allowed_attrs = ['href', 'src', 'type', 'id', 'class', 'role', 'name', 'title', 'aria-expanded', 'aria-label', 'data-icon']
        
    def clean_html(self, html_content: str, url: str, preserve_structure: bool = True) -> BeautifulSoup:
        """
        Clean HTML content by removing unnecessary elements and attributes.
        
        Args:
            html_content: Raw HTML content to clean
            url: URL of the page (for context)
            preserve_structure: Whether to preserve basic HTML structure
            
        Returns:
            BeautifulSoup object with cleaned HTML
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Clean head section
        self._clean_head(soup)
        
        # Clean elements
        self._clean_elements(soup)
        
        # Remove empty elements
        self._remove_empty_elements(soup)
        
        # Add title information
        self._add_title_info(soup, url)
        
        return soup
    
    def extract_elements(self, soup: BeautifulSoup) -> List[PageElement]:
        """
        Extract all relevant elements from the cleaned HTML.
        
        Args:
            soup: BeautifulSoup object with cleaned HTML
            
        Returns:
            List of PageElement objects
        """
        elements = []
        
        # Find all relevant elements
        for tag in soup.find_all(True):  # Find all tags
            if tag.name in ['script', 'style', 'head', 'meta']:
                continue
                
            element = self._create_page_element(tag)
            if element:
                elements.append(element)
        
        return elements
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = "") -> Set[str]:
        """
        Extract all links from the HTML.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            Set of absolute URLs
        """
        links = set()
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and not href.startswith('#'):
                # Convert relative to absolute URL if needed
                if href.startswith('/') and base_url:
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                links.add(href)
        
        return links
    
    def _clean_head(self, soup: BeautifulSoup):
        """Clean head section, keeping only title"""
        head = soup.find('head')
        if head:
            for tag in head.find_all():
                if tag.name != 'title':
                    tag.decompose()
    
    def _clean_elements(self, soup: BeautifulSoup):
        """Remove unnecessary elements and attributes"""
        # Remove script, style, and other unwanted tags
        for tag in soup.find_all(['script', 'style', 'source', 'path']):
            tag.decompose()
        
        # Remove tooltips
        for tag in soup.find_all(attrs={'role': 'tooltip'}):
            tag.decompose()
        
        # Clean attributes
        for tag in soup.find_all():
            if tag.name == 'img' or tag.name == 'svg':
                # Remove src from images to avoid loading issues
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in self.allowed_attrs or attr == 'src':
                        del tag[attr]
            else:
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in self.allowed_attrs:
                        del tag[attr]
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
    
    def _remove_empty_elements(self, soup: BeautifulSoup):
        """Remove empty elements recursively"""
        while True:
            removed = False
            for element in soup.find_all():
                # Skip preserved tags
                if element.name in self.preserve_tags:
                    continue
                # Skip elements with attributes
                if element.attrs:
                    continue
                # Get content (excluding whitespace)
                content = ''.join(str(child) for child in element.contents).strip()
                # Remove if empty
                if not content:
                    element.decompose()
                    removed = True
                    break
            if not removed:
                break
    
    def _add_title_info(self, soup: BeautifulSoup, url: str):
        """Add title information to the cleaned HTML"""
        body = soup.find('body')
        if body:
            title_text = soup.find('title').string if soup.find('title') else "No title"
            stamp_html = f'''
            <div class="page-info">
                <h1 class="page-url">{url}</h1>
                <h2 class="page-title">{title_text}</h2>
                <hr>
            </div>
            '''
            body.insert(0, BeautifulSoup(stamp_html, 'html.parser'))
    
    def _create_page_element(self, tag) -> Optional[PageElement]:
        """Create a PageElement from a BeautifulSoup tag"""
        if not tag.name:
            return None
        
        # Get text content
        text = tag.get_text(strip=True)
        
        # Get attributes
        attributes = dict(tag.attrs) if tag.attrs else {}
        
        # Determine element type
        element_type = self._classify_element(tag)
        
        return PageElement(
            tag=tag.name,
            text=text,
            attributes=attributes,
            element_type=element_type
        )
    
    def _classify_element(self, tag) -> str:
        """Classify element type based on tag and attributes"""
        tag_name = tag.name.lower()
        
        # Navigation elements
        if tag_name == 'nav' or 'nav' in tag.get('class', []):
            return 'navigation'
        
        # Button elements
        if tag_name in ['button', 'input'] and tag.get('type') == 'submit':
            return 'button'
        
        # Link elements
        if tag_name == 'a' and tag.get('href'):
            return 'link'
        
        # Form elements
        if tag_name in ['form', 'input', 'textarea', 'select']:
            return 'form'
        
        # Header elements
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return 'header'
        
        # Content elements
        if tag_name in ['p', 'div', 'span', 'article', 'section']:
            return 'content'
        
        # Media elements
        if tag_name in ['img', 'video', 'audio']:
            return 'media'
        
        return 'unknown' 