from bs4 import BeautifulSoup, Comment
from typing import Optional


class HTMLParser:
    """
    Minimal HTML parser for cleaning web page content.
    Simplified version focusing on basic HTML cleaning.
    """
    
    def __init__(self):
        # Tags that should be kept even when empty
        self.preserve_tags = {'hr', 'br', 'img', 'video', 'input', 'meta', 'link', 'textarea'}
        # Attributes to preserve during cleaning
        self.allowed_attrs = ['href', 'src', 'type', 'id', 'class', 'role', 'name', 'title', 'aria-expanded', 'aria-label', 'data-icon']
        
    def clean_html(self, html_content: str, url: str, save_path: str = None) -> BeautifulSoup:
        """
        Clean HTML content by removing unnecessary elements and attributes.
        
        Args:
            html_content: Raw HTML content to clean
            url: URL of the page (for context)
            save_path: Path to save the cleaned HTML
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
        
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
        
        return soup
    
    def _clean_head(self, soup: BeautifulSoup):
        """Clean head section, keeping only title"""
        head = soup.find('head')
        if head:
            for tag in head.find_all():
                if tag.name != 'title':
                    tag.decompose()
    
    def _clean_elements(self, soup: BeautifulSoup):
        """
        Cleans and simplifies HTML content by removing unnecessary elements and attributes.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
        # Remove script, style, and source tags
        for tag in soup.find_all(['script', 'style', 'source', 'path']):
            tag.decompose()
        
        # Remove tooltips
        for tag in soup.find_all(attrs={'role': 'tooltip'}):
            tag.decompose()
        
        # Clean attributes
        for tag in soup.find_all():
            # Special handling for <img> tags - remove src attribute
            if tag.name == 'img' or tag.name == 'svg':
                # Remove src from images to avoid loading issues
                attrs = dict(tag.attrs)
                for attr in attrs:
                    if attr not in self.allowed_attrs or (attr == 'src' and len(tag['src']) > 200):
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
        """
        Removes empty elements from HTML.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
        Returns:
            None (modifies soup object in place)
        """
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
        """
        Adds title information to the cleaned HTML.
        Args:
            soup (BeautifulSoup): The HTML soup object to clean
            url (str): The URL of the page
        Returns:
            None (modifies soup object in place)
        """
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